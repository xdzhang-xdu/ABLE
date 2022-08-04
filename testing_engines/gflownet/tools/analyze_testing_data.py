import json
import math
import os

from testing_engines.gflownet.GFN_Fuzzing import load_specifications
from testing_engines.gflownet.lib.monitor import Monitor

"""compute the total covered specs in all sessions, and compute their difficulty value.
"""

def compute_difficulty():

    with open("/home/xdzhang/work/shortgun/testing_engines/gflownet/rawdata/specs/spec_data.json") as file:
        specs = json.load(file)
    del specs["all_rules"]
    #
    # belong_to = "my_"
    belong_to = "lawbreaker_"

    all_specs = list(specs.values())
    # sessions = ['Intersection_with_Double-Direction_Roads', 'lane_change_in_the_same_road']
    sessions = ['Single-Direction-1']
    # data_path = '/data/xdzhang/apollo7/22-07-31-active-2*64/{}/data'
    # data_path = "/data/DATA-For-Traffic-Laws/T-Junction-Apollo6.0/{}/data"
    data_path = "/data/xdzhang/apollo7/lawbreaker-8-2/{}/data"
    oracle_list = []
    total_data_difficulty = dict()
    for session in sessions:
        print("Start analyzing session {}".format(session))
        covered_specs = []
        covered_num = 0
        data_dir = data_path.format(session)
        for root, _, data_files in os.walk(data_dir):
            for data_file in data_files:
                if not data_file.endswith('.json'):
                    continue
                with open(os.path.join(root, data_file)) as f:
                    data = json.load(f)
                    monitor = Monitor(data, 0)
                    for spec in all_specs:
                        rub_spec = monitor.continuous_monitor2(spec)
                        if rub_spec >= 0:
                            if spec in total_data_difficulty.keys():
                                total_data_difficulty[spec]["tests_num"] += 1
                                if session not in total_data_difficulty[spec]["sessions"]:
                                    total_data_difficulty[spec]["sessions"].append(session)
                            else:
                                total_data_difficulty[spec] = dict()
                                total_data_difficulty[spec]["tests_num"] = 1
                                total_data_difficulty[spec]["sessions"] = [session]
                            covered_num += 1
                            if spec not in covered_specs:
                                covered_specs.append(spec)
    for key, value in total_data_difficulty.items():
        total_data_difficulty[key]["difficulty"] = math.exp(128/(100*total_data_difficulty[key]["tests_num"] * len(total_data_difficulty[key]["sessions"])))
    total_data = sorted(total_data_difficulty.items(), key = lambda item : item[1]["difficulty"])
    with open(belong_to + 'total_data_difficulty.json', 'w', encoding='utf-8') as f:
        json.dump(total_data, f, ensure_ascii=False, indent=4)

def compute_coverage(belong_to, data_path, sessions):
    with open("/home/xdzhang/work/shortgun/testing_engines/gflownet/rawdata/specs/spec_data.json") as file:
        specs = json.load(file)
    del specs["all_rules"]
    #
    all_specs = list(specs.values())
    total_data_cover_by_session = dict()
    for session in sessions:
        print("Start analyzing session {}".format(session))
        covered_specs = []
        covered_num = 0
        data_dir = data_path.format(session)
        print("Current path {}".format(data_dir))
        for root, _, data_files in os.walk(data_dir):
            for data_file in data_files:
                if not data_file.endswith('.json'):
                    continue
                with open(os.path.join(root, data_file)) as f:
                    data = json.load(f)
                    monitor = Monitor(data, 0)
                    for spec in all_specs:
                        if spec in covered_specs:
                            continue
                        rub_spec = monitor.continuous_monitor2(spec)
                        if rub_spec >= 0:
                            covered_num += 1
                            covered_specs.append(spec)
        total_data_cover_by_session[session] = covered_specs
        print("Session {}, covered_num: {}, covered_specs: {}".format(session, covered_num, covered_specs))
    with open(belong_to + 'total_data_cover_by_session_tj.json', 'w', encoding='utf-8') as f:
        json.dump(total_data_cover_by_session, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # my_sessions = ['double_direction', 'lane_change', 'single_direction']
    my_sessions = ['t_junction']
    apollo7_data_path_my = '/data/xdzhang/apollo7/shortgun/{}/data'
    # data_path = "/data/DATA-For-Traffic-Laws/T-Junction-Apollo6.0/{}/data"
    # apollo6_data_path_my = "/data/xdzhang/apollo6/64*3-active-lack_t_junction/{}/data"
    compute_coverage("my_", apollo7_data_path_my, my_sessions)

    # lb_sessions = ['Intersection_with_Double-Direction_Roads', 'lane_change_in_the_same_road', 'Single-Direction-1']
    lb_sessions = ['T-Junction01']
    apollo7_data_path_lb = "/data/xdzhang/apollo7/lawbreaker-8-2/{}/data"
    # apollo6_data_path_lb = "/data/xdzhang/apollo6/lawbreaker/{}/data"
    compute_coverage("lawbreaker_", apollo7_data_path_lb, lb_sessions)