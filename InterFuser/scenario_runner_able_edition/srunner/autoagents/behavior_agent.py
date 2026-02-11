#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides an NPC agent to control the ego vehicle
"""

from __future__ import print_function

import json
import carla
from agents.navigation.behavior_agent import BehaviorAgent as CarlaBehaviorAgent

from srunner.autoagents.autonomous_agent import AutonomousAgent
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider


class BehaviorAgent(AutonomousAgent):
    _agent = None
    spawnpoint = carla.Location()
    destination = carla.Location()

    def setup(self, path_to_conf_file):
        self._agent = None
        carlamap = CarlaDataProvider.get_map()

        with open(path_to_conf_file) as trace_file:
            data = json.load(trace_file)
        lane_position_start = data["ego"]["start"]['lane_position']
        self.spawnpoint = carlamap.get_waypoint_xodr(
            int(lane_position_start['lane'].replace("lane_", "")),
            lane_position_start['roadID'],
            lane_position_start['offset']
        ).transform.location
        lane_position_destination = data["ego"]["destination"]['lane_position']
        self.destination = carlamap.get_waypoint_xodr(
            int(lane_position_destination['lane'].replace("lane_", "")),
            lane_position_destination['roadID'],
            lane_position_destination['offset']
        ).transform.location

    def sensors(self):
        return []

    def run_step(self):
        """
        Execute one step of navigation.
        """
        ego_vehicle = CarlaDataProvider.get_actor_by_name("ego_vehicle")
        if self._agent is None:
            if not ego_vehicle is None:
                #self._agent = CarlaBehaviorAgent(ego_vehicle, behavior='normal', opt_dict={ 'ignore_traffic_lights':True })
                self._agent = CarlaBehaviorAgent(ego_vehicle, behavior='normal')
                self._agent.set_destination(end_location=self.destination, start_location=self.spawnpoint)
            else:
                return carla.VehicleControl()
        self._agent.get_local_planner().set_speed(ego_vehicle.get_speed_limit())
        return self._agent.run_step()

    def __call__(self):
        return self.run_step()
