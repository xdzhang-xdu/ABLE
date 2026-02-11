#!/usr/bin/env python3

import os
import subprocess
from multiprocessing import Process
import psutil
import signal
import time
import json

HOME = os.environ["HOME"]
INTERFUSER_ROOT = HOME + "/InterFuser"
CARLA_ROOT = INTERFUSER_ROOT + "/carla"
LEADERBOARD_ROOT = INTERFUSER_ROOT + "/leaderboard"

def carla_is_running():
    for proc in psutil.process_iter():
        if "CarlaUE4.sh" in proc.name():
            return True
    return False

def run_carla():
    subprocess.Popen(["bash", CARLA_ROOT + "/CarlaUE4.sh"], cwd=CARLA_ROOT, stdout=subprocess.DEVNULL)

def terminate_carla():
    for proc in psutil.process_iter():
        if "CarlaUE4-Linux-Shipping" in proc.name():
            proc.send_signal(signal.SIGINT)
            time.sleep(5)
            if psutil.pid_exists(proc.pid) and "CarlaUE4-Linux-Shipping" in proc.name():
                proc.send_signal(signal.SIGINT)
                time.sleep(3)
            break

def run_evaluation(able_file):
    evaluation_process = subprocess.Popen(["conda", "run", "-n", "srunner0913", "bash", LEADERBOARD_ROOT + "/scripts/run_evaluation_ABLE.sh", able_file], cwd=INTERFUSER_ROOT)
    evaluation_process.wait()

def main(able_file):
    # Start Carla
    if not carla_is_running():
        print("Starting Carla...")
        carla_process = Process(target=run_carla)
        carla_process.start()
        time.sleep(15)

    # Start evaluation
    run_evaluation(able_file)

    # Shut down carla
    print("Stopping carla process:", carla_process)
    terminate_carla()
    carla_process.join()

if __name__ == '__main__':
    generated_scenarios_path = INTERFUSER_ROOT + "/scenario_runner_able_edition/Law_Judgement/generated_scenarios/"
    for scenarios in os.listdir(generated_scenarios_path):
        if os.path.isfile(generated_scenarios_path + scenarios):
            with open(generated_scenarios_path + scenarios, "r") as scenarios_file:
                data = json.load(scenarios_file)
            idx = 0
            for scenario in data:
                if "actions" in scenario:
                    del scenario["actions"]
                able_dir_name = ("temp_" + scenarios).replace(".json", "")
                able_file_name = "trace_temp_" + scenarios
                if os.path.isfile(INTERFUSER_ROOT + "/scenario_runner_able_edition/trace/" + able_dir_name + "/replay_" + able_dir_name + "_" + str(idx) + ".json"):
                    print("Skip " + able_dir_name + "_" + str(idx) + ".json")
                else:
                    while not os.path.isfile(INTERFUSER_ROOT + "/scenario_runner_able_edition/trace/" + able_dir_name + "/replay_" + able_dir_name + "_" + str(idx) + ".json"):
                        with open(INTERFUSER_ROOT + "/scenario_runner_able_edition/trace/" + able_file_name, "w") as able_file:
                            json.dump(scenario, able_file, indent=4)
                        print("Running " + able_dir_name + "_" + str(idx) + ".json")
                        main(INTERFUSER_ROOT + "/scenario_runner_able_edition/trace/" + able_file_name)
                        time.sleep(10)
                idx += 1
