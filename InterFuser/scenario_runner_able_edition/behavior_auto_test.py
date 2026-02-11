#!/usr/bin/env python

import os
import json
import psutil
import time
import subprocess

def main(able_file_name):
    HOME = os.environ["HOME"]

    CarlaExists = False
    for proc in psutil.process_iter():
        if "CarlaUE4.sh" in proc.name():
            CarlaExists = True
            break
    if not CarlaExists:
        bashCommand = HOME + "/CARLA_0.9.14/CarlaUE4.sh -quality-level=low -windowed -Resx=600 -Resy=480"
        subprocess.Popen(bashCommand, shell=True)
        time.sleep(15)

    srunner_path = HOME + "/scenario_runner_able_edition/"
    env_srunner = os.environ.copy()
    env_srunner["PATH"] = os.pathsep.join([srunner_path, env_srunner["PATH"]])
    subprocess.run(["conda", "run", "-n", "srunner", "python3", "scenario_runner.py", "--sync", "--reloadWorld",
                    "--able", able_file_name,
                    "--agent", "srunner/autoagents/behavior_agent.py",
                    "--agentConfig", able_file_name], cwd=srunner_path, env=env_srunner)

if __name__ == '__main__':
    HOME = os.environ["HOME"]
    generated_scenarios_path = HOME + "/scenario_runner_able_edition/Law_Judgement/generated_scenarios/"
    for scenarios in os.listdir(generated_scenarios_path):
        if os.path.isfile(generated_scenarios_path + scenarios):
            with open(generated_scenarios_path + scenarios, "r") as scenarios_file:
                data = json.load(scenarios_file)
            for scenario in data:
                session, ext = os.path.splitext(scenarios)
                idx = scenario["ScenarioName"].replace("NO_", "")
                if "actions" in scenario:
                    del scenario["actions"]
                able_file_name = "trace/trace_temp_" + session + ".json"
                with open(able_file_name, "w") as able_file:
                    json.dump(scenario, able_file, indent=4)
                while not os.path.exists("trace/temp_" + session + "/replay_temp_" + session + "_" + idx + ".json"):
                    main(able_file_name)
