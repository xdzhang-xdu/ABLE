#!/usr/bin/env python3

import os
import sys
import psutil
import time
import subprocess
from multiprocessing import Process
import ujson as json

import carla

host = '127.0.0.1'
port = 2000

def carla_is_running():
    for proc in psutil.process_iter():
        if "CarlaUE4" in proc.name():
            return True
    return False

def run_carla():
    CARLA_ROOT = os.environ["CARLA_ROOT"]
    subprocess.Popen(["bash", CARLA_ROOT + "/CarlaUE4.sh", "-Resx=600", "-Resy=480", "-prefernvidia"], stdout=subprocess.DEVNULL)

def terminate_carla():
    for proc in psutil.process_iter():
        if "CarlaUE4-Linux-Shipping" in proc.name():
            proc.terminate()
            time.sleep(5)
            if psutil.pid_exists(proc.pid) and "CarlaUE4-Linux-Shipping" in proc.name():
                proc.kill()
            break

def get_trajectory_dict(save_file):
    with open("temp_trace.json", 'r') as temp_trace_file:
        trace = json.load(temp_trace_file)

    if not carla_is_running():
        carla_process = Process(target=run_carla)
        carla_process.start()
        time.sleep(15)

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
    scenario_idx = 0
    for scenario in trace:
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

        scenario_idx += 1

    terminate_carla()

    # Save trajectory
    analysis_dir = "analysis_trajectory/"
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    with open(save_file, 'w') as analysis_file:
        json.dump(npc_trajectory_Dict, analysis_file)
    return npc_trajectory_Dict

if __name__ == '__main__':
    if len(sys.argv) > 1:
        get_trajectory_dict(sys.argv[1])