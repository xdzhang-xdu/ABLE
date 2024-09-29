#!/usr/bin/env python

# Copyright (c) 2018-2020 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides the ScenarioManager implementation.
It must not be modified and is for reference only!
"""

from __future__ import print_function
import sys
import os
import time
import subprocess
from multiprocessing import Process
from carla import Transform, Location, Rotation, TrafficLightState
import math
import numpy as np
import json
from websocket import create_connection

import py_trees

from srunner.autoagents.agent_wrapper import AgentWrapper
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
from srunner.scenariomanager.result_writer import ResultOutputProvider
from srunner.scenariomanager.timer import GameTime
from srunner.scenariomanager.watchdog import Watchdog

class ScenarioManager(object):

    """
    Basic scenario manager class. This class holds all functionality
    required to start, and analyze a scenario.

    The user must not modify this class.

    To use the ScenarioManager:
    1. Create an object via manager = ScenarioManager()
    2. Load a scenario via manager.load_scenario()
    3. Trigger the execution of the scenario manager.run_scenario()
       This function is designed to explicitly control start and end of
       the scenario execution
    4. Trigger a result evaluation with manager.analyze_scenario()
    5. If needed, cleanup with manager.stop_scenario()
    """

    def __init__(self, debug_mode=False, sync_mode=False, timeout=2.0):
        """
        Setups up the parameters, which will be filled at load_scenario()

        """
        self.scenario = None
        self.scenario_tree = None
        self.scenario_class = None
        self.ego_vehicles = None
        self.other_actors = None

        self._debug_mode = debug_mode
        self._agent = None
        self._sync_mode = sync_mode
        self._watchdog = None
        self._timeout = timeout

        self._running = False
        self._timestamp_last_run = 0.0
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None
        
        self.data_bridge = None
        self.able_data = None

    def _reset(self):
        """
        Reset all parameters
        """
        self._running = False
        self._timestamp_last_run = 0.0
        self.scenario_duration_system = 0.0
        self.scenario_duration_game = 0.0
        self.start_system_time = None
        self.end_system_time = None
        GameTime.restart()

    def cleanup(self):
        """
        This function triggers a proper termination of a scenario
        """

        if self._watchdog is not None:
            self._watchdog.stop()
            self._watchdog = None

        if self.scenario is not None:
            self.scenario.terminate()

        if self._agent is not None:
            self._agent.cleanup()
            self._agent = None

        CarlaDataProvider.cleanup()

    def load_scenario(self, scenario, agent=None):
        """
        Load a new scenario
        """
        self._reset()
        self._agent = AgentWrapper(agent) if agent else None
        if self._agent is not None:
            self._sync_mode = True
        self.scenario_class = scenario
        self.scenario = scenario.scenario
        self.scenario_tree = self.scenario.scenario_tree
        self.ego_vehicles = scenario.ego_vehicles
        self.other_actors = scenario.other_actors
        self.data_bridge.set_actors(self.ego_vehicles[0], self.other_actors)

        # To print the scenario tree uncomment the next line
        # py_trees.display.render_dot_tree(self.scenario_tree)

        if self._agent is not None:
            self._agent.setup_sensors(self.ego_vehicles[0], self._debug_mode)

    def set_camera(self):
        world = CarlaDataProvider.get_world()
        if world:
            spectator = world.get_spectator()
        if len(self.other_actors) > 0:
            ACTOR_ID = 0
            CAMERA_DIST = 40
            if ACTOR_ID == 0:
                npc_location = self.ego_vehicles[0].get_transform().location
                npc_rotation = self.ego_vehicles[0].get_transform().rotation
            else:
                npc_location = self.other_actors[ACTOR_ID-1].get_transform().location
                npc_rotation = self.other_actors[ACTOR_ID-1].get_transform().rotation
            if spectator and npc_location and npc_rotation:
                npc_forward_vector = npc_rotation.get_forward_vector() * CAMERA_DIST
                npc_up_vector = npc_rotation.get_up_vector() * CAMERA_DIST
                spectator.set_transform(Transform(npc_location - npc_forward_vector + npc_up_vector, Rotation(pitch=-45, yaw=npc_rotation.yaw)))

    def send_routing_request_apollo(self, waypoints = []):
        world = CarlaDataProvider.get_world()
        ego_vehicle = self.ego_vehicles[0]
        start_transform = ego_vehicle.get_transform()
        correcting_vector = start_transform.get_forward_vector()
        shift = 1.355
        start_location = start_transform.location - shift * correcting_vector

        lane_position_destination = self.able_data["ego"]["destination"]['lane_position']
        end_location = world.get_map().get_waypoint_xodr(
            int(lane_position_destination['lane'].replace("lane_", "")),
            lane_position_destination['roadID'],
            lane_position_destination['offset']
        ).transform.location

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

    def carla_to_ros2(self, transform):
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

    def send_routing_request_autoware(self):
        world = CarlaDataProvider.get_world()

        lane_position_destination = self.able_data["ego"]["destination"]['lane_position']
        goal_transform_carla = world.get_map().get_waypoint_xodr(
            int(lane_position_destination['lane'].replace("lane_", "")),
            lane_position_destination['roadID'],
            lane_position_destination['offset']
        ).transform
        goal_transform_ros2 = self.carla_to_ros2(goal_transform_carla)

        setgoalpose_cmd = "{{header: {{frame_id: 'map'}}, pose: {{position: {{x: {}, y: {}, z: {}}}, orientation: {{x: {}, y: {}, z: {}, w: {}}}}}}}".format(\
            goal_transform_ros2["x"],\
            goal_transform_ros2["y"],\
            goal_transform_ros2["z"],\
            goal_transform_ros2["qx"],\
            goal_transform_ros2["qy"],\
            goal_transform_ros2["qz"],\
            goal_transform_ros2["qw"])
        subprocess.run(["ros2", "topic", "pub", "--once", "/planning/mission_planning/goal", "geometry_msgs/msg/PoseStamped", setgoalpose_cmd])

        AUTOWARE_ROOT = os.environ["AUTOWARE_ROOT"]
        changeoperationmode_cmd = "source " + AUTOWARE_ROOT + "/install/setup.bash && ros2 service call /api/operation_mode/change_to_autonomous autoware_adapi_v1_msgs/srv/ChangeOperationMode {}"
        subprocess.run(changeoperationmode_cmd, shell=True, executable="/bin/bash")

    def ego_arrived(self, arrive_distance = 8.0):
        world = CarlaDataProvider.get_world()
        ego_location = self.ego_vehicles[0].get_location()
        if self.able_data:
            lane_position_destination = self.able_data["ego"]["destination"]['lane_position']
            dest_location = world.get_map().get_waypoint_xodr(
                int(lane_position_destination['lane'].replace("lane_", "")),
                lane_position_destination['roadID'],
                lane_position_destination['offset']
            ).transform.location
        elif self._agent:
            dest_location = self._agent._agent.destination
        else:
            return False
        distance = dest_location.distance(ego_location)
        return distance <= arrive_distance

    def run_scenario(self):
        """
        Trigger the start of the scenario and wait for it to finish/fail
        """
        print("ScenarioManager: Running scenario {}".format(self.scenario_tree.name))
        self.start_system_time = time.time()
        start_game_time = GameTime.get_time()

        self._watchdog = Watchdog(float(self._timeout))
        self._watchdog.start()
        self._running = True

        tick_counter = 0
        start_tick_threshold = 10

        while self._running:
            timestamp = None
            world = CarlaDataProvider.get_world()
            if world:
                snapshot = world.get_snapshot()
                if snapshot:
                    timestamp = snapshot.timestamp
            if timestamp:
                self._tick_scenario(timestamp)
                if tick_counter == start_tick_threshold:
                    self.data_bridge.update_ego_vehicle_start()
                    self.data_bridge.update_npc_vehicle_start()
                    self.send_routing_request_apollo()
                    self.set_camera()
                elif tick_counter > start_tick_threshold:
                    self.data_bridge.update_trace()
                    self.data_bridge.update_npc_vehicle_motion()
                    self.set_camera()
                # End the scenario once the ego vehicle has arrived
                if self.ego_arrived():
                    self.stop_scenario()
                
                tick_counter += 1

        self.cleanup()

        self.end_system_time = time.time()
        end_game_time = GameTime.get_time()

        self.scenario_duration_system = self.end_system_time - \
            self.start_system_time
        self.scenario_duration_game = end_game_time - start_game_time

        if self.scenario_tree.status == py_trees.common.Status.FAILURE:
            print("ScenarioManager: Terminated due to failure")

    def _tick_scenario(self, timestamp):
        """
        Run next tick of scenario and the agent.
        If running synchornously, it also handles the ticking of the world.
        """

        if self._timestamp_last_run < timestamp.elapsed_seconds and self._running:
            self._timestamp_last_run = timestamp.elapsed_seconds

            self._watchdog.update()

            if self._debug_mode:
                print("\n--------- Tick ---------\n")

            # Update game time and actor information
            GameTime.on_carla_tick(timestamp)
            CarlaDataProvider.on_carla_tick()

            if self._agent is not None:
                ego_action = self._agent()  # pylint: disable=not-callable

            if self._agent is not None:
                self.ego_vehicles[0].apply_control(ego_action)

            # Tick scenario
            self.scenario_tree.tick_once()

            if self._debug_mode:
                print("\n")
                py_trees.display.print_ascii_tree(self.scenario_tree, show_status=True)
                sys.stdout.flush()

            if self.scenario_tree.status != py_trees.common.Status.RUNNING:
                self._running = False

        if self._sync_mode and self._running and self._watchdog.get_status():
            CarlaDataProvider.get_world().tick()

    def get_running_status(self):
        """
        returns:
           bool:  False if watchdog exception occured, True otherwise
        """
        return self._watchdog.get_status()

    def stop_scenario(self):
        """
        This function is used by the overall signal handler to terminate the scenario execution
        """
        self._running = False

    def analyze_scenario(self, stdout, filename, junit, json):
        """
        This function is intended to be called from outside and provide
        the final statistics about the scenario (human-readable, in form of a junit
        report, etc.)
        """

        failure = False
        timeout = False
        result = "SUCCESS"

        if self.scenario.test_criteria is None:
            print("Nothing to analyze, this scenario has no criteria")
            return True

        for criterion in self.scenario.get_criteria():
            if (not criterion.optional and
                    criterion.test_status != "SUCCESS" and
                    criterion.test_status != "ACCEPTABLE"):
                failure = True
                result = "FAILURE"
            elif criterion.test_status == "ACCEPTABLE":
                result = "ACCEPTABLE"

        if self.scenario.timeout_node.timeout and not failure:
            timeout = True
            result = "TIMEOUT"

        output = ResultOutputProvider(self, result, stdout, filename, junit, json)
        output.write()

        return failure or timeout
