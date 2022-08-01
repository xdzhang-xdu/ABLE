import json
import math
import os

from testing_engines.gflownet.GFN_Fuzzing import load_specifications
from testing_engines.gflownet.lib.monitor import Monitor

if __name__ == "__main__":
    all_specs, specs_table = load_specifications()
    sessions = ['double_direction', 'single_direction', 'lane_change']
    data_path = '/data/xdzhang/22-07-31-active-2*64/{}/data'
    oracle_list = []
    total_data = dict()
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
                        # if spec in covered_specs:
                        #     continue
                        rub_spec = monitor.continuous_monitor2(spec)
                        if rub_spec >= 0:
                            if spec in total_data.keys():
                                total_data[spec]["tests_num"] += 1
                                if session not in total_data[spec]["sessions"]:
                                    total_data[spec]["sessions"].append(session)
                            else:
                                total_data[spec] = dict()
                                total_data[spec]["tests_num"] = 1
                                total_data[spec]["sessions"] = [session]
                            covered_num += 1
                            covered_specs.append(spec)
        print("Session {}, covered_num: {}, covered_specs: {}".format(session, covered_num, covered_specs))
    # with open("/home/xdzhang/work/shortgun/testing_engines/gflownet/total_data.json") as f:
    #     total_data = json.load(f)
    for key, value in total_data.items():
        total_data[key]["difficulty"] = math.exp(128/(100*total_data[key]["tests_num"] * len(total_data[key]["sessions"])))
    total_data = sorted(total_data.items(), key = lambda item : item[1]["difficulty"])
    with open('../total_data_dif_active.json', 'w', encoding='utf-8') as f:
        json.dump(total_data, f, ensure_ascii=False, indent=4)
