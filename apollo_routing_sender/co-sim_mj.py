#!/usr/bin/env python3

import carla

import os
import psutil
import shutil
import time
import random
import math
import json
import subprocess
from multiprocessing import Process
import docker
from websocket import create_connection

HOME = os.environ["HOME"]

host = '127.0.0.1'
port = 2000

env_dict_apollo = {}
env_dict_apollo["PATH"] = "/apollo/bazel-bin/modules/tools/visualizer:/apollo/bazel-bin/cyber/tools/cyber_launch:/apollo/bazel-bin/cyber/tools/cyber_service:/apollo/bazel-bin/cyber/tools/cyber_node:/apollo/bazel-bin/cyber/tools/cyber_channel:/apollo/bazel-bin/cyber/tools/cyber_monitor:/apollo/bazel-bin/cyber/tools/cyber_recorder:/apollo/bazel-bin/cyber/mainboard:/usr/local/cuda/bin:/opt/apollo/sysroot/bin:/usr/local/nvidia/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/apollo/scripts:/usr/local/qt5/bin"

env_dict_bridge = {}
env_dict_bridge["PATH"] = "/apollo/bazel-bin/cyber:/apollo/bazel-bin/cyber/tools/cyber_recorder:/apollo/bazel-bin/cyber/tools/cyber_monitor:/apollo/cyber/tools/cyber_launch:/apollo/cyber/tools/cyber_channel:/apollo/cyber/tools/cyber_node:/apollo/cyber/tools/cyber_service:/usr/local/Qt5.5.1/5.5/gcc_64/bin:/apollo/bazel-bin/modules/tools/visualizer:/apollo/bazel-bin/modules/data/tools/rosbag_to_record:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
env_dict_bridge["PYTHONPATH"] = "/root/carla_apollo_bridge_13/carla-python-0.9.13/carla:/root/carla_apollo_bridge_13/carla-python-0.9.13/carla/dist/carla-0.9.13-py2.7-linux-x86_64.egg:/apollo/py_proto:/apollo/bazel-bin/cyber/py_wrapper:/apollo/cyber/python:"
env_dict_bridge["CYBER_PATH"] = "/apollo/cyber"
env_dict_bridge["CARLA_PYTHON_ROOT"] = "/root/carla_apollo_bridge_13/carla-python-0.9.13"

def carla_is_running():
    for proc in psutil.process_iter():
        if "CarlaUE4.sh" in proc.name():
            return True
    return False

def run_carla():
    CARLA_ROOT = os.environ["CARLA_ROOT"]
    subprocess.run(["bash", CARLA_ROOT + "/CarlaUE4.sh", "-prefernvidia", "-quality-level=low", "-fps=30", "-Resx=600", "-Resy=480"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def change_carla_map(data_map):
    carla_client = carla.Client(host, port)
    carla_world = carla_client.get_world()
    carla_map = carla_world.get_map()

    if data_map is None or data_map == "":
        data_map = "Town01"
    if carla_map.name != "Carla/Maps/" + data_map:
        carla_client.load_world(data_map)
        print("Loading Carla {}...".format(data_map))
        time.sleep(5)

def run_manual_control(container):
    cmd = ["bash", "-c", "source /apollo/cyber/setup.bash && python examples/manual_control.py"]
    _, output = container.exec_run(cmd, user='root',
                                   stdin=True,
                                   stream=True,
                                   environment=env_dict_bridge,
                                   workdir="/root/carla_apollo_bridge_13")
    #for sub_output in output:
    #    print(sub_output.decode(), end='')

def run_bridge(container):
    cmd = ["bash", "-c", "source /apollo/cyber/setup.bash && python carla_cyber_bridge/run_bridge.py"]
    _, output = container.exec_run(cmd, user='root',
                                   stdin=True,
                                   stream=True,
                                   environment=env_dict_bridge,
                                   workdir="/root/carla_apollo_bridge_13")
    for sub_output in output:
        print(sub_output.decode(), end='')

def setup_srunner(able_file_name):
    HOME = os.environ["HOME"]
    srunner_path = HOME + "/scenario_runner_able_edition/"
    env_srunner = os.environ.copy()
    env_srunner["PATH"] = os.pathsep.join([srunner_path, env_srunner["PATH"]])
    subprocess.run(["conda", "run", "-n", "srunner", "python3", "scenario_runner.py", "--sync", "--waitForEgo", "--able", "trace/" + able_file_name], cwd=srunner_path, env=env_srunner)

def start_all_modules():
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "SETUP_MODE" }))
    print("All modules are started.")
    apollo_socket.close()

def reset_all_modules():
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "RESET_MODE" }))
    print("All modules are reset.")
    apollo_socket.close()

def start_one_module(module):
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "START_MODULE", 'value': module }))
    print("Module", module, "is started.")
    apollo_socket.close()

def reset_one_module(module):
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "STOP_MODULE", 'value': module }))
    print("Module", module, "is reset.")
    apollo_socket.close()

def enter_auto_mode():
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "ENTER_AUTO_MODE" }))
    print("Enter auto mode.")
    #print(apollo_socket.recv())
    apollo_socket.close()

def change_mode():
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "CHANGE_MODE", 'value': "Mkz Lgsvl" }))
    print("Mode changed to: Mkz Lgsvl")
    #print(apollo_socket.recv())
    apollo_socket.close()

def change_map(map_name):
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "CHANGE_MAP", 'value': map_name }))
    print("Map changed to:", map_name)
    #print(apollo_socket.recv())
    apollo_socket.close()

def change_vehicle():
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIAction', 'action': "CHANGE_VEHICLE", 'value': "Lincoln2017MKZ LGSVL" }))
    print("Vehicle change to: Lincoln2017MKZ LGSVL")
    #print(apollo_socket.recv())
    apollo_socket.close()

def get_HMIStatus():
    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({ 'type': 'HMIStatus' }))
    print("Get HMIStatus:")
    print(apollo_socket.recv())
    apollo_socket.close()

def get_current_transform(world):
    for vehicle in world.get_actors().filter('*vehicle*'):
        if vehicle.attributes['role_name'] == "hero" or vehicle.attributes['role_name'] == "ego_vehicle":
            return vehicle.get_transform()

def get_random_transform(world):
    spawn_points = world.get_map().get_spawn_points()
    return random.choice(spawn_points)

def send_routing_request(end_location = None, waypoints = []):
    world = carla.Client(host, port).get_world()
    start_transform = get_current_transform(world)
    correcting_vector = start_transform.get_forward_vector()
    shift = 1.355
    start_location = start_transform.location - shift * correcting_vector
    if end_location is None:
        end_location = get_random_transform(world).location
    start_location.z = 0.0
    end_location.z = 0.0

    apollo_socket = create_connection("ws://localhost:8888/websocket")
    apollo_socket.send(json.dumps({\
        'type': 'SendRoutingRequest',\
        'start': {\
            'x': start_location.x,\
            'y': -start_location.y,\
            'z': start_location.z,\
            'heading': math.radians(-start_transform.rotation.yaw)\
        },\
        'end': {\
            'x': end_location.x,\
            'y': -end_location.y,\
            'z': end_location.z,\
        },\
        'waypoint':waypoints\
    }))
    #print(apollo_socket.recv())
    apollo_socket.close()

def main(able_file_name):
    # Start Carla
    if not carla_is_running():
        print("Starting Carla...")
        carla_process = Process(target=run_carla)
        carla_process.start()
        time.sleep(15)

    with open(HOME + "/scenario_runner_able_edition/trace/" + able_file_name) as trace_file:
        data = json.load(trace_file)
        data_map = data["map"]

    change_carla_map_process = Process(target=change_carla_map, args=(data_map,))
    change_carla_map_process.start()
    change_carla_map_process.join()

    client = docker.from_env()
    container = client.containers.get("apollo_dev_yc")
    container_bridge = client.containers.get("carla-apollo-13")

    try:
        # Start bridge container
        if container_bridge.status == "exited":
            container_bridge.start()
            time.sleep(5)
            print("Container", container_bridge.name, "has been started.")
        elif container_bridge.status == "running":
            print("Container", container_bridge.name, "is already running.")
        else:
            print("Unknown container status:", container_bridge.status)
            exit()

        # Spawn the ego vehicle
        print("Spawning ego...")
        manual_control_process = Process(target=run_manual_control, args=(container_bridge,))
        manual_control_process.start()
        time.sleep(15)

        # Start Apollo container
        if container.status == "exited":
            container.start()
            time.sleep(5)
            print("Container", container.name, "has been started.")
        elif container.status == "running":
            print("Container", container.name, "is already running.")
        else:
            print("Unknown container status:", container.status)
            exit()

        # Start Dreamview
        cmd = "bash /apollo/scripts/bootstrap.sh restart"
        _, output = container.exec_run(cmd, user='yc',
                                    stdin=True,
                                    stream=True,
                                    environment=env_dict_apollo)
        for sub_output in output:
            print(sub_output.decode(), end='')

        # Set start transform
        """
        lane_position_start = data["ego"]["start"]['lane_position']
        start_transform = world.get_map().get_waypoint_xodr(
            int(lane_position_start['lane'].replace("lane_", "")),
            lane_position_start['roadID'],
            lane_position_start['offset']
        ).transform
        start_transform.location.z += 0.5
        for vehicle in world.get_actors().filter('*vehicle*'):
            if vehicle.attributes['role_name'] == "hero" or vehicle.attributes['role_name'] == "ego_vehicle":
                vehicle.set_transform(start_transform)
                break
        time.sleep(15)
        """

        # Start the bridge
        print("Starting bridge...")
        bridge_process = Process(target=run_bridge, args=(container_bridge,))
        bridge_process.start()
        time.sleep(15)

        # Initiate Apollo
        change_mode()
        change_vehicle()
        change_map("Carla " + data_map)
        time.sleep(5)
        for module in ["Routing", "Localization", "Prediction", "Planning", "Control"]:
            start_one_module(module)
        time.sleep(15)

        # Get end transform
        """
        end_location = None
        lane_position_destination = data["ego"]["destination"]['lane_position']
        end_location = world.get_map().get_waypoint_xodr(
            int(lane_position_destination['lane'].replace("lane_", "")),
            lane_position_destination['roadID'],
            lane_position_destination['offset']
        ).transform.location
        """

        # Setup scenario runner
        print("Starting srunner...")
        srunner_process = Process(target=setup_srunner, args=(able_file_name,))
        srunner_process.start()
        srunner_process.join()
        #send_routing_request(end_location=end_location)
        #time.sleep(120)
    finally:
        # Stop bridge and clean up
        print("Stopping bridge process:", manual_control_process, bridge_process)

        for proc in psutil.process_iter():
            cmdline = proc.cmdline()
            if len(cmdline) == 2 and cmdline[0] == "python" and cmdline[1] == "carla_cyber_bridge/run_bridge.py":
                cmd = "bash -c \"ps -ef | grep 'python carla_cyber_bridge/run_bridge.py' | grep -v 'grep' | awk '{print $2}' | xargs kill -s 2\""
                _, output = container_bridge.exec_run(cmd, user='root',
                                            stdin=True,
                                            stream=True,
                                            environment=env_dict_bridge,
                                            workdir="/root/carla_apollo_bridge_13")
                for sub_output in output:
                    print(sub_output.decode(), end='')
                time.sleep(1)
                if psutil.pid_exists(proc.pid) and len(proc.cmdline()) == 2 and proc.cmdline()[0] == "python" and proc.cmdline()[1] == "carla_cyber_bridge/run_bridge.py":
                    _, output = container_bridge.exec_run(cmd, user='root',
                                                stdin=True,
                                                stream=True,
                                                environment=env_dict_bridge,
                                                workdir="/root/carla_apollo_bridge_13")
                    for sub_output in output:
                        print(sub_output.decode(), end='')
        bridge_process.join()

        for proc in psutil.process_iter():
            cmdline = proc.cmdline()
            if len(cmdline) == 2 and cmdline[0] == "python" and cmdline[1] == "examples/manual_control.py":
                cmd = "bash -c \"ps -ef | grep 'python examples/manual_control.py' | grep -v 'grep' | awk '{print $2}' | xargs kill -s 2\""
                _, output = container_bridge.exec_run(cmd, user='root',
                                            stdin=True,
                                            stream=True,
                                            environment=env_dict_bridge,
                                            workdir="/root/carla_apollo_bridge_13")
                for sub_output in output:
                    print(sub_output.decode(), end='')
        manual_control_process.join()

        time.sleep(10)
        container_bridge.stop()

        # Shut down Carla
        print("Stopping carla process:", carla_process)
        for proc in psutil.process_iter():
            if "CarlaUE4-Linux-Shipping" in proc.name():
                proc.kill()
        carla_process.join()

        # Shut down Dreamview
        cmd = "bash /apollo/scripts/bootstrap.sh stop"
        _, output = container.exec_run(cmd, user='yc',
                                    stdin=True,
                                    stream=True,
                                    environment=env_dict_apollo)
        for sub_output in output:
            print(sub_output.decode(), end='')

        time.sleep(15)
        container.stop()

if __name__ == '__main__':
    subprocess.run(["xhost", "+"])

    HOME = os.environ["HOME"]
    APOLLO = os.environ["APOLLO_ROOT_DIR"]
    generated_scenarios_dir = HOME + "/scenario_runner_able_edition/Law_Judgement/generated_scenarios/"
    for scenarios in os.listdir(generated_scenarios_dir):
        if os.path.isfile(generated_scenarios_dir + scenarios) and scenarios.endswith(".json"):
            able_file_name = "trace_" + scenarios
            session = scenarios.replace(".json", "")
            trace_dir = os.path.join(HOME + "/scenario_runner_able_edition/trace/", session)
            if not os.path.isdir(trace_dir):
                os.mkdir(trace_dir)

            with open(generated_scenarios_dir + scenarios, "r") as scenarios_file:
                data = json.load(scenarios_file)
            for idx, scenario in enumerate(data):
                replay_path = os.path.join(trace_dir, "replay_{}_{}.json".format(session, str(idx)))
                if os.path.isfile(replay_path):
                    print("Skipping:", "{}_{}".format(session, str(idx)))
                else:
                    while not os.path.isfile(replay_path):
                        with open(HOME + "/scenario_runner_able_edition/trace/" + able_file_name, "w") as able_file:
                            json.dump(scenario, able_file, indent=4)
                        print("Running:", "{}_{}".format(session, str(idx)))
                        main(able_file_name)
                        time.sleep(10)
                        if os.path.isdir(APOLLO + "/data"):
                            shutil.rmtree(APOLLO + "/data")
