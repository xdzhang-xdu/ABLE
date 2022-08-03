import json
import math
import os

if __name__ == "__main__":
    covered = [1] * 81
    sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
    for session in sessions:
        path = "../generator/data/testset/a_testset_for_{}.json".format(session)
        with open(path) as f:
            data = json.load(f)
            for item in data:
                reward = 0.0
                robust = item["robustness"][1:]
                for i in range(81):
                    if robust[i] >= 0:
                        r = 0
                    else:
                        r = -robust[i]
                    reward += (covered[i]/(r + 1.0))
                item["robustness"][0] = reward
                # item["robustness"][0] = -max(item["robustness"][1:])
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)