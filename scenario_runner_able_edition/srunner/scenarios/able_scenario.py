#!/usr/bin/env python

# Copyright (c) 2018-2020 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provide BasicScenario, the basic class of all the scenarios.
"""

from __future__ import print_function

import py_trees

import carla
from agents.navigation.local_planner import RoadOption, _compute_connection
from agents.navigation.global_route_planner import GlobalRoutePlanner

from srunner.scenariomanager.carla_data_provider import CarlaDataProvider
#from srunner.scenariomanager.timer import TimeOut
#from srunner.scenariomanager.weather_sim import WeatherBehavior
from srunner.scenariomanager.scenarioatomics.atomic_behaviors import ActorTransformSetter, WaypointFollower, StopVehicle, Idle, WaitUtilEgoMove
from srunner.scenariomanager.scenarioatomics.atomic_criteria import CollisionTest
from srunner.scenarios.basic_scenario import BasicScenario
            

class ABLEScenario(BasicScenario):

    """
    Base class for user-defined scenario
    """

    def __init__(self, world, ego_vehicles, config, debug_mode=False,
                 terminate_on_failure=False, criteria_enable=False, timeout=180):
        """
        Initialize all parameters required for NewScenario
        """
        self.config = config
        self.data = config.data
        self.world = world
        self.map = CarlaDataProvider.get_map()
        self.global_planner = GlobalRoutePlanner(self.map, 0.1)
        self.timeout = timeout
        # Call constructor of BasicScenario
        super(ABLEScenario, self).__init__(
          "AbleScenario",
          ego_vehicles,
          config,
          world,
          debug_mode,
          terminate_on_failure=terminate_on_failure,
          criteria_enable=criteria_enable)

    def _initialize_environment(self, world):
        """
        Default initialization of weather and road friction.
        Override this method in child class to provide custom initialization.
        """

        # Set the appropriate weather conditions
        world.set_weather(self.config.weather)

        # Set the appropriate road friction
        if self.config.friction is not None:
            friction_bp = world.get_blueprint_library().find('static.trigger.friction')
            extent = carla.Location(1000000.0, 1000000.0, 1000000.0)
            friction_bp.set_attribute('friction', str(self.config.friction))
            friction_bp.set_attribute('extent_x', str(extent.x))
            friction_bp.set_attribute('extent_y', str(extent.y))
            friction_bp.set_attribute('extent_z', str(extent.z))

            # Spawn Trigger Friction
            transform = carla.Transform()
            transform.location = carla.Location(-10000.0, -10000.0, 0.0)
            world.spawn_actor(friction_bp, transform)

    def _initialize_actors(self, config):
        """
        Default initialization of other actors.
        Override this method in child class to provide custom initialization.
        """
        if config.other_actors:
            new_actors = CarlaDataProvider.request_new_actors(config.other_actors)
            if not new_actors:
                raise Exception("Error: Unable to add actors")

            for new_actor in new_actors:
                self.other_actors.append(new_actor)

    def _create_behavior(self):
        """
        Pure virtual function to setup user-defined scenario behavior
        """
        root = py_trees.composites.Parallel("Root", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)

        for npc in self.data["npcList"]:
            npc_actor = CarlaDataProvider.get_actor_by_name(npc["ID"])
            if npc_actor is None:
                continue

            npc_behavior = py_trees.composites.Sequence("Npc", policy=py_trees.common.ParallelPolicy.SUCCESS_ON_ALL)

            #lane_position = npc["start"]['lane_position']
            lane_position = npc["motion"][0]['lane_position']
            waypoint = self.map.get_waypoint_xodr(
                int(lane_position['lane'].replace("lane_", "")),
                lane_position['roadID'],
                lane_position['offset']
            )
            npc_behavior.add_child(ActorTransformSetter(npc_actor, waypoint.transform))
            #npc_behavior.add_child(Idle(16.0))
            npc_behavior.add_child(WaitUtilEgoMove())

            for idx in range(len(npc["motion"])):
                if idx == 0:
                    continue
                lane_position = npc["motion"][idx]['lane_position']
                waypoint = self.map.get_waypoint_xodr(
                    int(lane_position['lane'].replace("lane_", "")),
                    lane_position['roadID'],
                    lane_position['offset']
                )
                if idx == 0:
                    previous_lane_position = npc["start"]['lane_position']
                else:
                    previous_lane_position = npc["motion"][idx-1]['lane_position']
                previous_waypoint = self.map.get_waypoint_xodr(
                    int(previous_lane_position['lane'].replace("lane_", "")),
                    previous_lane_position['roadID'],
                    previous_lane_position['offset']
                )
                
                # Set Speed
                if idx < len(npc["motion"])-1:
                    #target_speed = (npc["motion"][idx]['speed'] + npc["motion"][idx+1]['speed'])/2
                    target_speed = max(npc["motion"][idx]['speed'], npc["motion"][idx+1]['speed'])
                else:
                    #target_speed = (npc["motion"][idx]['speed'] + npc["destination"]['speed'])/2
                    target_speed = max(npc["motion"][idx]['speed'], npc["destination"]['speed'])
                #target_speed = npc["motion"][idx]['speed']
                if target_speed < 0.4:
                    target_speed = 0.4
                
                # Set route
                if previous_waypoint and waypoint:
                    route = self.global_planner.trace_route(previous_waypoint.transform.location,
                                                            waypoint.transform.location)
                    # Check if the route is planned incorrectly
                    route_covered_road_id_dict = {}
                    for wp_tuple in route:
                        route_covered_road_id_dict[wp_tuple[0].road_id] = True
                    if len(route_covered_road_id_dict) > 4:
                        continue
                    npc_behavior.add_child(WaypointFollower(npc_actor, target_speed=target_speed, plan=route, avoid_collision=False, name="FollowWaypointsABLE"))
            
            previous_lane_position = npc["motion"][-1]['lane_position']
            previous_waypoint = self.map.get_waypoint_xodr(
                int(previous_lane_position['lane'].replace("lane_", "")),
                previous_lane_position['roadID'],
                previous_lane_position['offset']
            )
            lane_position = npc["destination"]['lane_position']
            waypoint = self.map.get_waypoint_xodr(
                int(lane_position['lane'].replace("lane_", "")),
                lane_position['roadID'],
                lane_position['offset']
            )
            if previous_waypoint and waypoint:
                route = self.global_planner.trace_route(previous_waypoint.transform.location,
                                                        waypoint.transform.location)
                npc_behavior.add_child(WaypointFollower(npc_actor, target_speed=npc["destination"]['speed'], plan=route, avoid_collision=False, name="FollowWaypointsABLE"))
            
            npc_behavior.add_child(StopVehicle(npc_actor, 1.0))
            root.add_child(npc_behavior)

        root.add_child(py_trees.behaviours.Running())

        return root

    def _create_test_criteria(self):
        """
        A list of all test criteria will be created that is later used
        in parallel behavior tree.
        """
        criteria = []

        collision_criterion = CollisionTest(self.ego_vehicles[0])

        criteria.append(collision_criterion)

        return criteria

    def __del__(self):
        """
        Remove all actors upon deletion
        """
        self.remove_all_actors()
