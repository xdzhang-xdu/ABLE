#!/usr/bin/env python3

import os
import psutil
import subprocess
from concurrent.futures import ProcessPoolExecutor
import time
import ujson as json

import numpy as np
from dtw import *
import carla
import matplotlib.pyplot as plt
from violation_auditor import load_json_data_with_idx, get_robustness_with_idx

host = '127.0.0.1'
port = 2000

def carla_is_running():
    for proc in psutil.process_iter():
        if "CarlaUE4" in proc.name():
            return True
    return False

def run_carla():
    CARLA_ROOT = os.environ["CARLA_ROOT"]
    subprocess.Popen(["bash", CARLA_ROOT + "/CarlaUE4.sh", "-Resx=600", "-Resy=480", "-fps=20"], stdout=subprocess.DEVNULL)

def terminate_carla():
    for proc in psutil.process_iter():
        if "CarlaUE4-Linux-Shipping" in proc.name():
            proc.terminate()
            time.sleep(5)
            if psutil.pid_exists(proc.pid) and "CarlaUE4-Linux-Shipping" in proc.name():
                proc.kill()
            break

def get_dtw(trajectory_pair):
    #return dtw(trajectory_pair[0], trajectory_pair[1], keep_internals=True).distance
    return dtw(trajectory_pair[0], trajectory_pair[1], distance_only=True).distance

def get_test_suite(scenario_data_dict):
    for gfn_dir in [ "trace_apollo/", "trace_apollo_batch_2/"]:
        for _session in sorted(os.listdir(gfn_dir)):
            session = _session.replace("temp_", "")
            if "half" in session or "quater" in session:
                continue

            scenario_file_list = [gfn_dir + _session + "/" + scenario_file for scenario_file in os.listdir(gfn_dir + _session + "/")]
            scenario_count = 0
            for scenario_file in scenario_file_list:
                if os.path.isfile(scenario_file) and scenario_file.endswith(".json"):
                    scenario_count += 1
            scenario_List = [{}] * scenario_count
            with ProcessPoolExecutor(max_workers=24) as executor:
                for scenario_data, scenario_idx in executor.map(load_json_data_with_idx, scenario_file_list):
                    del scenario_data["trace"]
                    scenario_List[scenario_idx] = scenario_data

            if not session in scenario_data_dict:
                scenario_data_dict[session] = []
            scenario_data_dict[session].extend(scenario_List)

def get_trajectory_dict(session, data_source_name, trace):
    # Use saved trajectory
    analysis_dir = "analysis_trajectory/"
    save_file = analysis_dir + session + "_" + data_source_name + ".json"
    if os.path.isfile(save_file):
        with open(save_file, 'r') as trajectory_file:
            npc_trajectory_Dict = json.load(trajectory_file)
        print("Using save file:", save_file)
        return npc_trajectory_Dict

    client = carla.Client(host, port)
    carla_world = client.get_world()
    carla_map = carla_world.get_map()
    if carla_map is not None and carla_map.name.split('/')[-1] != trace[0]["map"]:
        client.load_world(trace[0]["map"])
        time.sleep(5)
        carla_world = client.get_world()
        carla_map = carla_world.get_map()

    # Init dict
    npc_trajectory_Dict = {}
    for npc in trace[0]["npcList"]:
        npc_trajectory_Dict[npc["ID"]] = []

    # Get trajectory of each npc
    for i, scenario in enumerate(trace):
        for npc in scenario["npcList"]:
            trajectory = []
            lane_position = npc["start"]['lane_position']
            while carla_map.get_waypoint_xodr(
                int(lane_position['lane'].replace("lane_", "")),
                lane_position['roadID'],
                lane_position['offset']
            ) is None:
                lane_position['offset'] -= 0.5
            start_location = carla_map.get_waypoint_xodr(
                int(lane_position['lane'].replace("lane_", "")),
                lane_position['roadID'],
                lane_position['offset']
            ).transform.location
            trajectory.append([start_location.x, start_location.y])
            if "motion" in npc:
                for idx in range(len(npc["motion"])):
                    lane_position = npc["motion"][idx]['lane_position']
                    while carla_map.get_waypoint_xodr(
                        int(lane_position['lane'].replace("lane_", "")),
                        lane_position['roadID'],
                        lane_position['offset']
                    ) is None:
                        lane_position['offset'] -= 0.5
                    motion_location = carla_map.get_waypoint_xodr(
                        int(lane_position['lane'].replace("lane_", "")),
                        lane_position['roadID'],
                        lane_position['offset']
                    ).transform.location
                    trajectory.append([motion_location.x, motion_location.y])
            lane_position = npc["destination"]['lane_position']
            while carla_map.get_waypoint_xodr(
                int(lane_position['lane'].replace("lane_", "")),
                lane_position['roadID'],
                lane_position['offset']
            ) is None:
                lane_position['offset'] -= 0.5
            end_location = carla_map.get_waypoint_xodr(
                int(lane_position['lane'].replace("lane_", "")),
                lane_position['roadID'],
                lane_position['offset']
            ).transform.location
            trajectory.append([end_location.x, end_location.y])

            npc_trajectory_Dict[npc["ID"]].append(trajectory)

    # Save trajectory
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    with open(save_file, 'w') as analysis_file:
        json.dump(npc_trajectory_Dict, analysis_file)
    return npc_trajectory_Dict

def get_trajectory_dist_dict(session, data_source_name, trace, npc_trajectory_Dict):
    # Use saved trajectory
    analysis_dir = "analysis_dtw/"
    save_file = analysis_dir + session + "_" + data_source_name + ".json"
    if os.path.isfile(save_file):
        with open(save_file, 'r') as dist_file:
            npc_trajectory_dist_Dict = json.load(dist_file)
        for npc_id in npc_trajectory_dist_Dict:
            npc_trajectory_dist_Dict[npc_id] = np.array(npc_trajectory_dist_Dict[npc_id])
        print("Using save file:", save_file)
        return npc_trajectory_dist_Dict

    # Init dict
    npc_trajectory_dist_Dict = {}
    for npc in trace[0]["npcList"]:
        npc_trajectory_dist_Dict[npc["ID"]] = []

    # Calculate pairwise trajectory DTW distance
    for npc in trace[0]["npcList"]:
        npc_trajectory_List = npc_trajectory_Dict[npc["ID"]]
        npc_trajectory_pairwise_List = []
        for i in range(len(npc_trajectory_List)):
            for j in range(i+1, len(npc_trajectory_List)):
                npc_trajectory_pairwise_List.append([npc_trajectory_List[i], npc_trajectory_List[j]])

        with ProcessPoolExecutor(max_workers=24) as executor:
            for distance in executor.map(get_dtw, npc_trajectory_pairwise_List):
                npc_trajectory_dist_Dict[npc["ID"]].append(distance)

    # Save trajectory
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    #npc_trajectory_dist_Dict_serialized = {}
    #for npc_id in npc_trajectory_dist_Dict:
    #    npc_trajectory_dist_Dict_serialized[npc_id] = npc_trajectory_dist_Dict[npc_id].tolist()
    with open(save_file, 'w') as analysis_file:
        json.dump(npc_trajectory_dist_Dict, analysis_file)
    return npc_trajectory_dist_Dict

def box_plot(trajectory_dist_dict1, trajectory_dist_dict2, trajectory_dist_dict3, session):
    npc_categories = list(trajectory_dist_dict1.keys())
    positions = [1.7, 2.0, 2.3]
    colors = ['gray', 'firebrick', 'teal']
    fig, ax = plt.subplots(1, len(npc_categories), figsize=(3, 3), sharey=True)
    fig.suptitle(session.replace("s", "S"))
    npc_idx = 0
    for npc in npc_categories:
        npc_data = []
        npc_data.append(trajectory_dist_dict1[npc])
        npc_data.append(trajectory_dist_dict2[npc])
        npc_data.append(trajectory_dist_dict3[npc])
        bp = ax[npc_idx].boxplot(npc_data, sym='', positions=positions, widths=0.2, showmeans=True,
                                 meanprops=dict(marker='D'))
        for elements in ['boxes', 'whiskers', 'fliers', 'means', 'medians', 'caps']:
            for i, element in enumerate(bp[elements]):
                color_idx = i // 2 if elements == "whiskers" or elements == "caps" else i
                element.set(color=colors[color_idx], linewidth=1.5)
                if elements == "fliers":
                    element.set_markeredgewidth(0.5)
                if elements == "means" or elements == "fliers":
                    element.set_markeredgecolor(colors[i])
                    element.set_markerfacecolor(colors[i])
        ax[npc_idx].set_xlabel(npc)
        ax[npc_idx].set_xticks([])
        npc_idx += 1

    ax[0].set_ylim(ymin=0)
    ax[0].set_ylabel("Dynamc Time Warping Distance")
    fig.legend(handles=[plt.Rectangle((0,0),1,1, fc=c, ec="k") for c in colors],
                 labels=['Genetic Algorithm', 'GFlowNet', 'Test Suite Optimized'], loc='upper left')

    plt.subplots_adjust(wspace=0)
    #plt.show()

    save_path = "results_dtw/"
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    plt.savefig(save_path + session + ".png", dpi=300)

if __name__ == "__main__":
    if not carla_is_running():
        run_carla()
        time.sleep(15)
        pass

    HOME = os.environ["HOME"]
    SRUNNER_ROOT = HOME + "/scenario_runner_able_edition"
    genetic_scenarios_path = SRUNNER_ROOT + "/Law_Judgement/traceset_mutated/"

    scenario_data_dict = {}
    get_test_suite(scenario_data_dict)

    with open("temp_opt.json", 'r') as temp_opt_file:
        optimized_idx_dict = json.load(temp_opt_file)

    for _session in sorted(os.listdir(genetic_scenarios_path)):
        session = _session.replace(".json", "")
        # GFlowNet
        scenario_data_gfn = scenario_data_dict[session]
        trajectory_dict_gfn = get_trajectory_dict(session, "gfn", scenario_data_gfn)
        trajectory_dist_dict_gfn = get_trajectory_dist_dict(session, "gfn", scenario_data_gfn, trajectory_dict_gfn)

        # Test Suite Optimized GFlowNet
        optimized_idx_list = optimized_idx_dict[session]
        scenario_data_idx = 0
        scenario_data_tso = []
        for optimized_idx in optimized_idx_list:
            scenario_data_tso.append(scenario_data_gfn[optimized_idx])
        trajectory_dict_tso = get_trajectory_dict(session, "tso", scenario_data_tso)
        trajectory_dist_dict_tso = get_trajectory_dist_dict(session, "tso", scenario_data_tso, trajectory_dict_tso)

        # Genetic Algorithm
        if os.path.isdir(genetic_scenarios_path + session):
            trajectory_dist_dict_genetic_total = {}
            #for subsession in os.listdir(genetic_scenarios_path + session):
            for subsession in ["mutated_traceset_{}_{}.json".format(i, session) for i in range(8)]:
                if os.path.isfile(genetic_scenarios_path + session + "/" + subsession):
                    with open(genetic_scenarios_path + session + "/" + subsession, "r") as scenarios_file:
                        scenario_data_genetic = json.load(scenarios_file)
                else:
                    scenario_data_genetic = None
                subsession_id = subsession.split("_")[2]
                trajectory_dict_genetic = get_trajectory_dict(session, "genetic_" + subsession_id, scenario_data_genetic)
                trajectory_dist_dict_genetic = get_trajectory_dist_dict(session, "genetic_" + subsession_id, scenario_data_genetic, trajectory_dict_genetic)
                for npc_id in trajectory_dist_dict_genetic:
                    trajectory_dist_dict_genetic[npc_id] = list(trajectory_dist_dict_genetic[npc_id])
                for npc_id in trajectory_dist_dict_genetic:
                    if npc_id in trajectory_dist_dict_genetic_total:
                        trajectory_dist_dict_genetic_total[npc_id].extend(trajectory_dist_dict_genetic[npc_id])
                    else:
                        trajectory_dist_dict_genetic_total[npc_id] = trajectory_dist_dict_genetic[npc_id]

        box_plot(trajectory_dist_dict_genetic_total, trajectory_dist_dict_gfn, trajectory_dist_dict_tso, session.replace("avunit_", ""))

    terminate_carla()
