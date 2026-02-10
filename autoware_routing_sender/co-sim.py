#!/usr/bin/env python3

import os
import subprocess
from multiprocessing import Process
import psutil
import signal
import time
import random
import numpy as np
import json
import carla

HOME = os.environ["HOME"]
AUTOWARE_ROOT = os.environ["AUTOWARE_ROOT"]
CARLA_ROOT = os.environ["CARLA_ROOT"]
OP_BRIDGE_ROOT = os.environ["OP_BRIDGE_ROOT"]

host = '127.0.0.1'
port = 2000

def carla_is_running():
    for proc in psutil.process_iter():
        if "CarlaUE4.sh" in proc.name():
            return True
    return False

def run_carla():
    subprocess.Popen(["bash", CARLA_ROOT + "/CarlaUE4.sh", "-Resx=600", "-Resy=480", "-fps=20"], cwd=CARLA_ROOT, stdout=subprocess.DEVNULL)

def terminate_carla():
    for proc in psutil.process_iter():
        if "CarlaUE4-Linux-Shipping" in proc.name():
            proc.send_signal(signal.SIGINT)
            time.sleep(5)
            if psutil.pid_exists(proc.pid) and "CarlaUE4-Linux-Shipping" in proc.name():
                proc.send_signal(signal.SIGINT)
                time.sleep(3)
            break

def run_bridge(start_transform_carla):
    os.environ["INITIAL_POSE_CARLA"] = "{},{},{},{},{},{}".format(
        start_transform_carla.location.x,\
        start_transform_carla.location.y,\
        start_transform_carla.location.z,\
        start_transform_carla.rotation.roll,\
        start_transform_carla.rotation.pitch,\
        start_transform_carla.rotation.yaw
    )
    start_transform_ros2 = carla_to_ros2(start_transform_carla)
    os.environ["INITIAL_POSE_ROS2"] = "{},{},{},{},{},{},{}".format(
        start_transform_ros2["x"],\
        start_transform_ros2["y"],\
        start_transform_ros2["z"],\
        start_transform_ros2["qx"],\
        start_transform_ros2["qy"],\
        start_transform_ros2["qz"],\
        start_transform_ros2["qw"]
    )
    subprocess.Popen(["bash", OP_BRIDGE_ROOT + "/op_scripts/run_exploration_mode_ros2.sh"], stdout=subprocess.DEVNULL, cwd=OP_BRIDGE_ROOT)

def terminate_bridge():
    for proc in psutil.process_iter():
        if proc.name() == "rviz2":
            proc.send_signal(signal.SIGKILL)
            break
    for proc in psutil.process_iter():
        cmdline = proc.cmdline()
        if len(cmdline) > 3 and cmdline[0].endswith("python3") and cmdline[1].endswith("ros2") and cmdline[2] == "launch" and cmdline[3].endswith("carla_simulator.launch.xml"):
            proc.send_signal(signal.SIGINT)
            time.sleep(15)
            break
    for proc in psutil.process_iter():
        cmdline = proc.cmdline()
        if len(cmdline) == 2 and cmdline[0] == "python3" and cmdline[1] == OP_BRIDGE_ROOT + "/op_bridge/op_bridge_ros2.py":
            proc.send_signal(signal.SIGKILL)
            break

def setup_srunner(able_file_name):
    srunner_path = HOME + "/scenario_runner_able_edition/"
    env_srunner = os.environ.copy()
    env_srunner["PATH"] = os.pathsep.join([srunner_path, env_srunner["PATH"]])

    PYTHONPATH_list = []
    for python_path in os.environ["PYTHONPATH"].split(':'):
        if "carla-0.9.15-py3.10-linux-x86_64.egg" in python_path:
            python_path = python_path.replace("carla-0.9.15-py3.10-linux-x86_64.egg", "carla-0.9.15-py3.7-linux-x86_64.egg")
            PYTHONPATH_list.insert(0, python_path)
        else:
            PYTHONPATH_list.append(python_path)
    env_srunner["PYTHONPATH"] = ':'.join(PYTHONPATH_list)

    subprocess.run(["conda", "run", "-n", "srunner", "python3", "scenario_runner.py", "--sync", "--waitForEgo", "--able", "trace/" + able_file_name], cwd=srunner_path, env=env_srunner)#, stderr = subprocess.STDOUT

def get_world(client):
    world = client.get_world()
    return world

def get_map(world):
    carla_map = world.get_map()
    return carla_map

def carla_to_ros2(transform):
    ros2_transform = {}

    ros2_transform["x"] = transform.location.x
    ros2_transform["y"] = -transform.location.y
    ros2_transform["z"] = transform.location.z

    roll = np.radians(transform.rotation.roll)
    pitch = -np.radians(transform.rotation.pitch)
    yaw = -np.radians(transform.rotation.yaw)
    qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
    qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
    qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    ros2_transform["qx"] = qx
    ros2_transform["qy"] = qy
    ros2_transform["qz"] = qz
    ros2_transform["qw"] = qw

    return ros2_transform

def get_current_transform(world):
    for vehicle in world.get_actors().filter('*vehicle*'):
        if vehicle.attributes['role_name'] == "hero" or vehicle.attributes['role_name'] == "ego_vehicle":
            return vehicle.get_transform()

def get_random_goal_transform(world):
    spawn_points = world.get_map().get_spawn_points()
    return random.choice(spawn_points)

def set_initial_pose(start_transform_carla):
    start_transform_ros2 = carla_to_ros2(start_transform_carla)
    covariance = [0.25, 0.0, 0.0, 0.0, 0.0, 0.0,\
                    0.0, 0.25, 0.0, 0.0, 0.0, 0.0,\
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,\
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,\
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,\
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.06853891909122467]
    poseestimate_cmd = "{{header: {{frame_id: 'map'}}, pose: {{pose: {{position: {{x: {}, y: {}, z: {}}}, orientation: {{x: {}, y: {}, z: {}, w: {}}}}}, covariance: {}}}}}".format(\
        start_transform_ros2["x"],\
        start_transform_ros2["y"],\
        start_transform_ros2["z"],\
        start_transform_ros2["qx"],\
        start_transform_ros2["qy"],\
        start_transform_ros2["qz"],\
        start_transform_ros2["qw"],\
        covariance)
    subprocess.run(["ros2", "topic", "pub", "--once", "/initialpose", "geometry_msgs/msg/PoseWithCovarianceStamped", poseestimate_cmd])
    time.sleep(5)

def send_routing_request(goal_transform_carla):
    goal_transform_ros2 = carla_to_ros2(goal_transform_carla)
    setgoalpose_cmd = "{{header: {{frame_id: 'map'}}, pose: {{position: {{x: {}, y: {}, z: {}}}, orientation: {{x: {}, y: {}, z: {}, w: {}}}}}}}".format(\
        goal_transform_ros2["x"],\
        goal_transform_ros2["y"],\
        goal_transform_ros2["z"],\
        goal_transform_ros2["qx"],\
        goal_transform_ros2["qy"],\
        goal_transform_ros2["qz"],\
        goal_transform_ros2["qw"])
    subprocess.run(["ros2", "topic", "pub", "--once", "/planning/mission_planning/goal", "geometry_msgs/msg/PoseStamped", setgoalpose_cmd])
    time.sleep(5)

    changeoperationmode_cmd = "source " + AUTOWARE_ROOT + "/install/setup.bash && ros2 service call /api/operation_mode/change_to_autonomous autoware_adapi_v1_msgs/srv/ChangeOperationMode {}"
    subprocess.run(changeoperationmode_cmd, shell=True, executable="/bin/bash")

def main(able_file_name):
    # Start Carla
    if not carla_is_running():
        print("Starting Carla...")
        carla_process = Process(target=run_carla)
        carla_process.start()
        time.sleep(15)

    try:
        client = carla.Client(host, port)
        world = get_world(client)
        carla_map = get_map(world)

        with open(HOME + "/scenario_runner_able_edition/trace/" + able_file_name) as trace_file:
            data = json.load(trace_file)
        data_map = data["map"]
        if data_map is None or data_map == "":
            data_map = "Town05"

        # Set map
        if carla_map.name != "Carla/Maps/" + data_map:
            client.load_world(data_map)
            print("Loading Carla {}...".format(data_map))
            time.sleep(5)
        os.environ["TOWN_NAME"] = data_map

        # Get initial pose
        lane_position_start = data["ego"]["start"]['lane_position']
        start_transform_carla = world.get_map().get_waypoint_xodr(
            int(lane_position_start['lane'].replace("lane_", "")),
            lane_position_start['roadID'],
            lane_position_start['offset']
        ).transform

        # Start the bridge
        print("Starting bridge...")
        bridge_process = Process(target=run_bridge, args=(start_transform_carla,))
        bridge_process.start()
        time.sleep(120)

        # Wait until localization initialized
        echo_initialization_state_cmd = "source " + AUTOWARE_ROOT + "/install/setup.bash && ros2 topic echo --once /api/localization/initialization_state"
        while True:
            result = subprocess.run(echo_initialization_state_cmd, shell=True, executable="/bin/bash", capture_output=True, text=True)
            if "state: 3" in result.stdout:
                break
            time.sleep(10)

        # Setup scenario runner
        print("Starting srunner...")
        srunner_process = Process(target=setup_srunner, args=(able_file_name,))
        srunner_process.start()
        srunner_process.join()

    finally:
        # Stop bridge and clean up
        print("Stopping bridge process:", bridge_process)
        terminate_bridge()
        bridge_process.join()

        # Shut down carla
        print("Stopping carla process:", carla_process)
        terminate_carla()
        carla_process.join()

if __name__ == '__main__':
    generated_scenarios_path = HOME + "/scenario_runner_able_edition/Law_Judgement/generated_scenarios/"
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
                if os.path.isfile(HOME + "/scenario_runner_able_edition/trace/" + able_dir_name + "/replay_" + able_dir_name + "_" + str(idx) + ".json"):
                    print("Skip " + able_dir_name + "_" + str(idx) + ".json")
                else:
                    while not os.path.isfile(HOME + "/scenario_runner_able_edition/trace/" + able_dir_name + "/replay_" + able_dir_name + "_" + str(idx) + ".json"):
                        with open(HOME + "/scenario_runner_able_edition/trace/" + able_file_name, "w") as able_file:
                            json.dump(scenario, able_file, indent=4)
                        print("Running " + able_dir_name + "_" + str(idx) + ".json")
                        main(able_file_name)
                        time.sleep(20)
                idx += 1
