#!/usr/bin/env python3

import os
import psutil
import subprocess
import time
import ujson as json

import numpy as np
from sklearn.metrics.pairwise import pairwise_distances
from tslearn.metrics import cdist_dtw
from sklearn.cluster import DBSCAN, HDBSCAN, OPTICS, AgglomerativeClustering, AffinityPropagation, SpectralClustering
from sklearn.metrics import silhouette_score, silhouette_samples

from concurrent.futures import ProcessPoolExecutor
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
    subprocess.Popen(["bash", CARLA_ROOT + "/CarlaUE4.sh", "-Resx=600", "-Resy=480", "-prefernvidia"], stdout=subprocess.DEVNULL)

def terminate_carla():
    for proc in psutil.process_iter():
        if "CarlaUE4-Linux-Shipping" in proc.name():
            proc.terminate()
            time.sleep(5)
            if psutil.pid_exists(proc.pid) and "CarlaUE4-Linux-Shipping" in proc.name():
                proc.kill()
            break

def get_euclidean_dist(trajectories):
    return pairwise_distances(trajectories, metric="sqeuclidean", n_jobs=24)

def get_manhattan_dist(trajectories):
    return pairwise_distances(trajectories, metric="manhattan", n_jobs=24)

def get_dtw_dist(time_sequences):
    return cdist_dtw(time_sequences, n_jobs=24)

def get_trajectory_dict(session, data_source_name, trace):
    # Use saved trajectory
    analysis_dir = "analysis_trajectory/"
    save_file = analysis_dir + session + "_" + data_source_name + ".json"
    print(save_file)
    if os.path.isfile(save_file):
        with open(save_file, 'r') as trajectory_file:
            npc_trajectory_Dict = json.load(trajectory_file)
        print("Using save file:", save_file)
        return npc_trajectory_Dict

    with open("temp_trace.json", 'w') as temp_trace_file:
        json.dump(trace, temp_trace_file)

    # This python script needs python 3.10, but carla needs python 3.7
    subprocess.run(["conda", "run", "-n", "srunner", "python3", "test_suite_opt_get_trajectory.py", save_file])

    with open(save_file, 'r') as trajectory_file:
        npc_trajectory_Dict = json.load(trajectory_file)
    return npc_trajectory_Dict

    exit()

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

    # Save trajectory
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    with open(save_file, 'w') as analysis_file:
        json.dump(npc_trajectory_Dict, analysis_file)
    return npc_trajectory_Dict

def get_speed_dict(session, data_source_name, trace):
    # Use saved speed
    analysis_dir = "analysis_speed/"
    save_file = analysis_dir + session + "_" + data_source_name + ".json"
    if os.path.isfile(save_file):
        with open(save_file, 'r') as speed_file:
            npc_speed_Dict = json.load(speed_file)
        print("Using save file:", save_file)
        return npc_speed_Dict

    # Init dict
    npc_speed_Dict = {}
    for npc in trace[0]["npcList"]:
        npc_speed_Dict[npc["ID"]] = []

    # Get speed of each npc
    #for scenario in trace:
    for debug_idx, scenario in enumerate(trace):
        for npc in scenario["npcList"]:
            speed = []

            speed.append(npc["start"]["speed"])
            if "motion" in npc:
                for idx in range(len(npc["motion"])):
                    speed.append(npc["motion"][idx]['speed'])
            speed.append(npc["destination"]['speed'])

            npc_speed_Dict[npc["ID"]].append(speed)

    # Save speed
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    with open(save_file, 'w') as analysis_file:
        json.dump(npc_speed_Dict, analysis_file)
    return npc_speed_Dict

def get_trajectory_dist_dict(session, data_source_name, trace, npc_trajectory_Dict):
    # Use saved trajectory
    analysis_dir = "analysis_trajectory_dist/"
    save_file = analysis_dir + session + "_" + data_source_name + ".json"
    if os.path.isfile(save_file):
        with open(save_file, 'r') as dist_file:
            npc_trajectory_dist_Dict = json.load(dist_file)
        for npc_id in npc_trajectory_dist_Dict:
            npc_trajectory_dist_Dict[npc_id] = np.array(npc_trajectory_dist_Dict[npc_id])
        print("Using save file:", save_file)
        return npc_trajectory_dist_Dict

    # Calculate pairwise trajectory distance
    npc_trajectory_dist_Dict = {}
    for npc in trace[0]["npcList"]:
        npc_trajectory_dist_Dict[npc["ID"]] = get_dtw_dist(npc_trajectory_Dict[npc["ID"]])

    # Save trajectory
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    npc_trajectory_dist_Dict_serialized = {}
    for npc_id in npc_trajectory_dist_Dict:
        npc_trajectory_dist_Dict_serialized[npc_id] = npc_trajectory_dist_Dict[npc_id].tolist()
    with open(save_file, 'w') as analysis_file:
        json.dump(npc_trajectory_dist_Dict_serialized, analysis_file)
    return npc_trajectory_dist_Dict

def get_speed_dist_dict(session, data_source_name, trace, npc_speed_Dict):
    # Use saved speed
    analysis_dir = "analysis_speed_dist/"
    save_file = analysis_dir + session + "_" + data_source_name + ".json"
    if os.path.isfile(save_file):
        with open(save_file, 'r') as dist_file:
            npc_speed_dist_Dict = json.load(dist_file)
        for npc_id in npc_speed_dist_Dict:
            npc_speed_dist_Dict[npc_id] = np.array(npc_speed_dist_Dict[npc_id])
        print("Using save file:", save_file)
        return npc_speed_dist_Dict

    # Calculate pairwise speed distance
    npc_speed_dist_Dict = {}
    for npc in trace[0]["npcList"]:
        npc_speed_dist_Dict[npc["ID"]] = get_dtw_dist(npc_speed_Dict[npc["ID"]])

    # Save speed
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    npc_speed_dist_Dict_serialized = {}
    for npc_id in npc_speed_dist_Dict:
        npc_speed_dist_Dict_serialized[npc_id] = npc_speed_dist_Dict[npc_id].tolist()
    with open(save_file, 'w') as analysis_file:
        json.dump(npc_speed_dist_Dict_serialized, analysis_file)
    return npc_speed_dist_Dict

def get_overall_dist_matrix(npc_trajectory_dist_Dict, npc_speed_dist_Dict):
    for npc_id in npc_trajectory_dist_Dict:
        overall_dist_matrix = np.ones_like(npc_trajectory_dist_Dict[npc_id])
        break
    for npc_id in npc_trajectory_dist_Dict:
        #overall_dist_matrix *= np.sqrt(np.power(npc_trajectory_dist_Dict[npc_id], 2) + np.power(npc_speed_dist_Dict[npc_id], 2))
        overall_dist_matrix *= npc_trajectory_dist_Dict[npc_id]

    return overall_dist_matrix

def get_n_clusters(model, param_dict, x):
    max_n_clusters = x.shape[0]

    max_score = 0
    suggested_n_clusters = 2
    for k in range(2, max_n_clusters):
        param_dict["n_clusters"] = k
        model = model.set_params(**param_dict)
        labels = model.fit(x).labels_

        np.fill_diagonal(x, 0.)
        score_avg = silhouette_score(x, labels, metric="precomputed")
        sample_silhouette_values = silhouette_samples(x, labels, metric="precomputed")
        should_skip_n_clusters = False
        for ith_values in sample_silhouette_values:
            if np.max(ith_values) < score_avg:
                should_skip_n_clusters = True
                break
        if should_skip_n_clusters:
            continue
        if score_avg > max_score:
            max_score = score_avg
            suggested_n_clusters = k

    print("Number of clusters for {}: {}".format(model, suggested_n_clusters))
    print("Silhouette score:", max_score)

    return suggested_n_clusters

def get_n_clusters_posteriori(model, param_dict, x, violations_dict_list):
    max_n_clusters = x.shape[0]

    max_reduction = 0
    suggested_n_clusters = 2
    for k in range(max_n_clusters, 2, -1):
        param_dict["n_clusters"] = k
        model = model.set_params(**param_dict)
        labels = model.fit(x).labels_

        reserved_idx_list = []
        clustered_label_set = set()
        for scenario_idx, label in enumerate(labels):
            if label == -1 or not label in clustered_label_set:
                reserved_idx_list.append(scenario_idx)
                clustered_label_set.add(label)

        total_violations = {}
        for violations_dict in violations_dict_list:
            total_violations.update(violations_dict)
        violations = {}
        for scenario_idx in reserved_idx_list:
            violations.update(violations_dict_list[scenario_idx])

        num_labels = len(labels)
        num_reserved = len(reserved_idx_list)
        current_reduction = num_labels - num_reserved
        num_total_violations = len(total_violations)
        num_reserved_violations = len(violations)
        violation_depreciation = num_total_violations - num_reserved_violations
        if current_reduction >= max_reduction and violation_depreciation == 0:
            max_reduction = current_reduction
            suggested_n_clusters = k
        else:
            break

    print("Number of clusters for {}: {}".format(model, suggested_n_clusters))

    return suggested_n_clusters

def get_all_cluster_labels(x, violations_dict_list=None):
    clustering_labels_dict = {}

    db_model = DBSCAN(eps=np.max(x), min_samples=2, metric="precomputed", n_jobs=24).fit(x.copy())
    clustering_labels_dict["DBSCAN"] = db_model.labels_

    optics_model = OPTICS(min_samples=2, metric="precomputed", n_jobs=24).fit(x.copy())
    clustering_labels_dict["OPTICS"] = optics_model.labels_

    hdb_model = HDBSCAN(min_cluster_size=2,
                        min_samples=2,
                        metric="precomputed",
                        cluster_selection_method="leaf",
                        allow_single_cluster=True,
                        n_jobs=24).fit(x.copy())
    clustering_labels_dict["HDBSCAN"] = hdb_model.labels_

    param_dict = {}
    param_dict["metric"] = "precomputed"
    param_dict["linkage"] = "single"
    #n_clusters = get_n_clusters_posteriori(AgglomerativeClustering(), param_dict, x.copy(), violations_dict_list)
    #agglomerative_model = AgglomerativeClustering(n_clusters=n_clusters, metric="precomputed", linkage="single").fit(x.copy())
    agglomerative_model = AgglomerativeClustering(n_clusters=None,
                                                  metric="precomputed",
                                                  linkage="single",
                                                  distance_threshold=np.median(x)).fit(x.copy())
    clustering_labels_dict["AgglomerativeClustering"] = agglomerative_model.labels_

    beta = 1.0
    x_similarity = np.exp(-beta * x / x.std())

    affinitypropagation_model = AffinityPropagation(affinity="precomputed").fit(-x.copy())
    clustering_labels_dict["AffinityPropagation"] = affinitypropagation_model.labels_

    param_dict = {}
    param_dict["affinity"] = "precomputed"
    param_dict["assign_labels"] = "cluster_qr"
    param_dict["n_jobs"] = 24
    n_clusters = get_n_clusters_posteriori(SpectralClustering(), param_dict, x_similarity, violations_dict_list)
    spectral_model = SpectralClustering(n_clusters=n_clusters,
                                        affinity="precomputed",
                                        assign_labels="cluster_qr",
                                        n_jobs=24).fit(x_similarity)
    clustering_labels_dict["SpectralClustering"] = spectral_model.labels_

    return clustering_labels_dict

def get_HDBSCAN_labels(x):
    HDBSCAN_labels_list = [[None for _ in range(1, 10)] for _ in range(1, 10)]
    for param_1 in range(1, 10):
        for param_2 in range(1, 10):
            hdb_model = HDBSCAN(min_cluster_size=int(2**param_1),
                                min_samples=int(2**param_2),
                                metric="precomputed",
                                cluster_selection_method="leaf",
                                allow_single_cluster=True,
                                n_jobs=24).fit(x.copy())
            HDBSCAN_labels_list[param_1-1][param_2-1] = hdb_model.labels_

    return HDBSCAN_labels_list

def get_violation_robustness(scenario_dataset):
    violations_dict_list = [{} for _ in scenario_dataset]
    with ProcessPoolExecutor(max_workers=24) as executor:
        for violations_dict, idx in executor.map(get_robustness_with_idx, scenario_dataset):
            violations_dict_list[idx] = violations_dict

    return violations_dict_list

def get_trajectories_directed_distance(trajectory1, trajectory2, probs1, probs2):
    directed_distance = 0.0
    samesincestart = True
    for idx in range(len(trajectory1)):
        if samesincestart and trajectory1[idx] == trajectory2[idx]:
            continue

        samesincestart = False
        directed_distance = directed_distance - np.log(probs1[idx]) - np.log(probs2[idx])

    return directed_distance

def get_discrepancy_coefficient(trajectory1, trajectory2):
    num_shared_actions = len(set(trajectory1) & set(trajectory2))
    return 1 - num_shared_actions / len(trajectory1)

samples_g = None
probs_generated_g = None

def get_directed_distance_parrellel(sample_idx_tuple):
    sample1_idx, sample2_idx = sample_idx_tuple
    directed_distance = get_trajectories_directed_distance(samples_g[sample1_idx], samples_g[sample2_idx],
                                                           probs_generated_g[sample1_idx], probs_generated_g[sample2_idx])
    discrepancy_coefficient = get_discrepancy_coefficient(samples_g[sample1_idx], samples_g[sample2_idx])
    return sample_idx_tuple, directed_distance, discrepancy_coefficient

def directed_dist_based_tso(samples, probs_generated, quantile=0.1):
    num_samples = len(samples)
    directed_distance_cache = np.full((num_samples, num_samples), float("inf"))
    discrepancy_coefficient_cache = np.ones((num_samples, num_samples))
    global samples_g
    global probs_generated_g
    samples_g = samples
    probs_generated_g = probs_generated

    sample_idx_tuples = []
    for sample1_idx in range(num_samples):
        for sample2_idx in range(sample1_idx+1, num_samples):
            sample_idx_tuples.append((sample1_idx, sample2_idx))
    with ProcessPoolExecutor(max_workers=24) as executor:
        for sample_idx_tuple, directed_distance, discrepancy_coefficient in executor.map(get_directed_distance_parrellel, sample_idx_tuples):
            sample1_idx, sample2_idx = sample_idx_tuple
            directed_distance_cache[sample1_idx][sample2_idx] = directed_distance
            discrepancy_coefficient_cache[sample1_idx][sample2_idx] = discrepancy_coefficient
    directed_dist_mod = directed_distance_cache * discrepancy_coefficient_cache
    tso_min_directed_distance = np.quantile(np.min(directed_dist_mod, axis=1), quantile)

    reduced_idx_set = set()
    for sample1_idx in range(num_samples):
        for sample2_idx in range(sample1_idx+1, num_samples):
            if sample2_idx in reduced_idx_set:
                continue
            if directed_dist_mod[sample1_idx][sample2_idx] < tso_min_directed_distance:
                reduced_idx_set.add(sample2_idx)
    print("Reserved: {}, reduced: {}, ratio: {}".format(len(samples) - len(reduced_idx_set), len(reduced_idx_set),\
                                                        len(reduced_idx_set) / len(samples)))
    
    return list(reduced_idx_set)

def distance_based_tso(trace_dir):
    reduced_idx_dict = {}
    for session in sorted(os.listdir(trace_dir)):
        if not os.path.isdir(trace_dir + session):
            continue
        if "rs" in session or "bysopt" in session or "rl" in session:
            continue

        actionseq_path = "generated_actionseq/" + session + ".json"
        with open(actionseq_path.replace(".json", "_tsodata.json"), 'r') as tso_file:
            tso_data = json.load(tso_file)

        reduced_idx_dict[session] = {}
        reduced_idx_dict[session]["reduced_idx_list"] = []
        reduced_idx_dict[session]["samples"] = []
        for batch in range(len(tso_data)):
            reduced_idx_list = directed_dist_based_tso(tso_data[batch]["samples"], np.array(tso_data[batch]["probs_generated"]), 0.2)
            idx_offset = len(reduced_idx_dict[session]["samples"])
            for meta_idx, _ in enumerate(reduced_idx_list):
                reduced_idx_list[meta_idx] = reduced_idx_list[meta_idx] + idx_offset
            reduced_idx_dict[session]["reduced_idx_list"].extend(reduced_idx_list)
            reduced_idx_dict[session]["samples"].extend(tso_data[batch]["samples"])

    return reduced_idx_dict

def trajectory_based_tso(trace_dir):
    ignore_weather = True

    scenario_data_dict = {}
    violations_dict_list_dict = {}
    for session in sorted(os.listdir(trace_dir)):
        if not os.path.isdir(trace_dir + session):
            continue
        if "rs" in session or "bysopt" in session or "rl" in session:
            continue

        session_dir = trace_dir + session + "/"
        scenario_file_list = [session_dir + scenario_file for scenario_file in os.listdir(session_dir)]
        scenario_count = 0
        for scenario_file in scenario_file_list:
            if os.path.isfile(scenario_file) and scenario_file.endswith(".json"):
                scenario_count += 1
        scenario_List = [{}] * scenario_count
        with ProcessPoolExecutor(max_workers=24) as executor:
            for scenario_data, scenario_idx in executor.map(load_json_data_with_idx, scenario_file_list):
                if ignore_weather:
                    scenario_data["weather"]["rain"] = .0
                    scenario_data["weather"]["sunny"] = .0
                    scenario_data["weather"]["wetness"] = .0
                    scenario_data["weather"]["fog"] = .0
                else:
                    if scenario_data["weather"]["rain"] >= 1.0:
                        scenario_data["weather"]["rain"] /= 100.0
                    if scenario_data["weather"]["sunny"] >= 1.0:
                        scenario_data["weather"]["sunny"] /= 100.0
                    if scenario_data["weather"]["wetness"] >= 1.0:
                        scenario_data["weather"]["wetness"] /= 100.0
                    if scenario_data["weather"]["fog"] >= 1.0:
                        scenario_data["weather"]["fog"] /= 100.0
                scenario_List[scenario_idx] = scenario_data
        violations_dict_list = get_violation_robustness(scenario_List)
        if not session in violations_dict_list_dict:
            violations_dict_list_dict[session] = []
        for violations_dict in violations_dict_list:
            violations_dict_list_dict[session].append(violations_dict)

        if not session in scenario_data_dict:
            scenario_data_dict[session] = []
        for scenario_data in scenario_List:
            del scenario_data["trace"]
            scenario_data_dict[session].append(scenario_data)
        del scenario_List

    reserved_idx_dict = {}
    for session in scenario_data_dict:
        trace = scenario_data_dict[session]
        trajectory_dict = get_trajectory_dict(session, "gfn", trace)
        trajectory_dist_dict = get_trajectory_dist_dict(session, "gfn", trace, trajectory_dict)
        speed_dict = get_speed_dict(session, "gfn", trace)
        speed_dist_dict = get_speed_dist_dict(session, "gfn", trace, speed_dict)
        overall_dist_matrix = get_overall_dist_matrix(trajectory_dist_dict, speed_dist_dict)

        reserved_idx_dict[session] = {}

        labels_dict = get_all_cluster_labels(overall_dist_matrix, violations_dict_list_dict[session])
        for clustering in labels_dict:
            print("=" * 40)
            print("Method:", clustering)
            labels = labels_dict[clustering]

            n_labels = len(set(labels)) - (1 if -1 in set(labels) else 0) + (labels == -1).sum()
            print("Labels number:", n_labels)
            if n_labels > 1 and n_labels < len(labels):
                np.fill_diagonal(overall_dist_matrix, 0.)
                score_avg = silhouette_score(overall_dist_matrix, labels, metric="precomputed")
                print("Silhouette score:", score_avg)

            reserved_idx_list = []
            clustered_label_set = set()
            for scenario_idx, label in enumerate(labels):
                if label == -1 or not label in clustered_label_set:
                    reserved_idx_list.append(scenario_idx)
                    clustered_label_set.add(label)
            reserved_idx_dict[session][clustering] = reserved_idx_list

            print("Scenario dataset size: {}-{}={}".format(len(labels), len(labels) - len(reserved_idx_list), len(reserved_idx_list)))

            violations_dict_list = violations_dict_list_dict[session]

            total_violations = {}
            for violations_dict in violations_dict_list:
                total_violations.update(violations_dict)

            violations = {}
            for scenario_idx in reserved_idx_list:
                violations.update(violations_dict_list[scenario_idx])

            print("Discovered violations counts: {} -> {}, depreciation: {}".format(len(total_violations), len(violations), len(total_violations) - len(violations)))

        print("=" * 40)

        HDBSCAN_param_tuning_list = [[None for _ in range(1, 10)] for _ in range(1, 10)]
        HDBSCAN_labels_list = get_HDBSCAN_labels(overall_dist_matrix)
        for param_1 in range(1, 10):
            for param_2 in range(1, 10):
                labels = HDBSCAN_labels_list[param_1-1][param_2-1]

                reserved_idx_list = []
                clustered_label_set = set()
                for scenario_idx, label in enumerate(labels):
                    if label == -1 or not label in clustered_label_set:
                        reserved_idx_list.append(scenario_idx)
                        clustered_label_set.add(label)

                violations_dict_list = violations_dict_list_dict[session]

                total_violations = {}
                for violations_dict in violations_dict_list:
                    total_violations.update(violations_dict)

                violations = {}
                for scenario_idx in reserved_idx_list:
                    violations.update(violations_dict_list[scenario_idx])

                HDBSCAN_param_tuning_list[param_1-1][param_2-1] = (len(labels) - len(reserved_idx_list),
                                                                   len(total_violations) - len(violations))

        for param_1 in range(1, 10):
            print(HDBSCAN_param_tuning_list[param_1-1])

    return reserved_idx_dict, violations_dict_list_dict

def ablation_study():
    HOME = os.environ["HOME"]
    SRUNNER_ROOT = HOME + "/scenario_runner_able_edition/"
    trace_dir = SRUNNER_ROOT + "trace/"

    reduced_idx_dict_directed_dist = distance_based_tso(trace_dir)
    reserved_idx_dict_trajectory, violations_dict_list_dict = trajectory_based_tso(trace_dir)

    print("=" * 40)
    print("=" * 40)
    print("Ablation study:")
    print()

    for session in sorted(os.listdir(trace_dir)):
        if not os.path.isdir(trace_dir + session):
            continue
        if "rs" in session or "bysopt" in session or "rl" in session:
            continue

        reduced_idx_list = reduced_idx_dict_directed_dist[session]["reduced_idx_list"]
        reserved_idx_list = reserved_idx_dict_trajectory[session]["HDBSCAN"]

        n_samples = reduced_idx_dict_directed_dist[session]["samples"]

        violations_dict_list = violations_dict_list_dict[session]
        violations_union = set()
        violations_intersection = set(violations_dict_list[0].keys())
        violations_intersection_dict = {}
        quantile = 0.95
        for violations_dict in violations_dict_list:
            violations_union = violations_union | set(violations_dict.keys())
            violations_intersection = violations_intersection & set(violations_dict.keys())
            for violation in violations_dict:
                if not violation in violations_intersection_dict:
                    violations_intersection_dict[violation] = 0
                violations_intersection_dict[violation] += 1
        for violation in violations_intersection_dict:
            violations_intersection_dict[violation] /= len(violations_dict_list)
            if violations_intersection_dict[violation] >= quantile:
                violations_intersection.add(violation)

        print("Full test suite:", len(n_samples))
        violation_scenario_amount = 0
        for scenario_idx in range(len(n_samples)):
            if len(violations_dict_list[scenario_idx]) > 0:
                violation_scenario_amount += 1
        print("Test cases with violation: {}".format(violation_scenario_amount))
        print()

        print("Directed distance method only:")
        print("Scenario dataset size: {}-{}={}".format(len(n_samples), len(reduced_idx_list), len(n_samples) - len(reduced_idx_list)))
        directed_dist_violations = {}
        violation_scenario_amount = 0
        for scenario_idx in range(len(n_samples)):
            if scenario_idx not in reduced_idx_list:
                directed_dist_violations.update(violations_dict_list[scenario_idx])
                if len(violations_dict_list[scenario_idx]) > 0:
                    violation_scenario_amount += 1
        print("Discovered violations counts: {} -> {}, depreciation: {}".format(len(violations_union),
                                                                                len(directed_dist_violations),
                                                                                len(violations_union) - len(directed_dist_violations)))
        print("Test cases with violation: {}".format(violation_scenario_amount))
        print()

        print("Trajectory method only:")
        print("Scenario dataset size: {}-{}={}".format(len(n_samples), len(n_samples) - len(reserved_idx_list), len(reserved_idx_list)))
        trajectory_violations = {}
        violation_scenario_amount = 0
        for scenario_idx in reserved_idx_list:
            trajectory_violations.update(violations_dict_list[scenario_idx])
            if len(violations_dict_list[scenario_idx]) > 0:
                violation_scenario_amount += 1
        print("Discovered violations counts: {} -> {}, depreciation: {}".format(len(violations_union),
                                                                                len(trajectory_violations),
                                                                                len(violations_union) - len(trajectory_violations)))
        print("Test cases with violation: {}".format(violation_scenario_amount))
        print()

        print("Union method:")
        tso_idx_list = []
        for scenario_idx in range(len(n_samples)):
            if not scenario_idx in reduced_idx_list or scenario_idx in reserved_idx_list:
                tso_idx_list.append(scenario_idx)
        print("Scenario dataset size: {}-{}={}".format(len(n_samples), len(n_samples) - len(tso_idx_list), len(tso_idx_list)))
        tso_violations = {}
        violation_scenario_amount = 0
        for scenario_idx in tso_idx_list:
            tso_violations.update(violations_dict_list[scenario_idx])
            if len(violations_dict_list[scenario_idx]) > 0:
                violation_scenario_amount += 1
        print("Discovered violations counts: {} -> {}, depreciation: {}".format(len(violations_union),
                                                                                len(tso_violations),
                                                                                len(violations_union) - len(tso_violations)))
        print("Test cases with violation: {}".format(violation_scenario_amount))
        print()

        print("Intersection method:")
        tso_idx_list = []
        for scenario_idx in reserved_idx_list:
            if not scenario_idx in reduced_idx_list:
                tso_idx_list.append(scenario_idx)
        print("Scenario dataset size: {}-{}={}".format(len(n_samples), len(n_samples) - len(tso_idx_list), len(tso_idx_list)))
        tso_violations = {}
        violation_scenario_amount = 0
        for scenario_idx in tso_idx_list:
            tso_violations.update(violations_dict_list[scenario_idx])
            if len(violations_dict_list[scenario_idx]) > 0:
                violation_scenario_amount += 1
        print("Discovered violations counts: {} -> {}, depreciation: {}".format(len(violations_union),
                                                                                len(tso_violations),
                                                                                len(violations_union) - len(tso_violations)))
        print("Test cases with violation: {}".format(violation_scenario_amount))
        print()

if __name__ == "__main__":
    ablation_study()
    terminate_carla()
