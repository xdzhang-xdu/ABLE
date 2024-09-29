#!/usr/bin/env python

# Copyright (c) 2019 Intel Corporation
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides the key configuration parameters for a route-based scenario
"""

import time
import carla
import json
from agents.navigation.local_planner import RoadOption

import srunner.osc2_stdlib.vehicle as vehicles
from srunner.scenarioconfigs.scenario_configuration import ActorConfigurationData, ScenarioConfiguration
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider


class ABLEScenarioConfiguration(ScenarioConfiguration):

    """
    This class provides the basic configuration for a route
    """

    def __init__(self, filename, client):
        self.client = client
        self.ego_vehicles = []
        self.other_actors = []
        if type(filename) == str:
            with open(filename) as trace_file:
                data = json.load(trace_file)
        else:
            data = filename
        self.data = data
        self.name = filename
        self.scenarioname = data["ScenarioName"]
        self.town = data["map"]
        self.weather = carla.WeatherParameters()
        self.parse_json_configuration()

    def parse_json_configuration(self):
        """
        Parse json generated from GFN
        """
        self.weather.precipitation = self.data["weather"]["rain"] * 100
        self.weather.cloudiness = self.data["weather"]["sunny"] * 100
        self.weather.wetness = self.data["weather"]["wetness"] * 100
        self.weather.fog_density = self.data["weather"]["fog"] * 100
        self.weather.sun_azimuth_angle = 45
        self.weather.sun_altitude_angle = 70
        self._set_carla_town()
        self.set_ego_vehicle()
        self.set_npc_vehicle()
    
    def set_ego_vehicle(self):
        ego_lane_position = self.data["ego"]["start"]["lane_position"]
        spawn_point = CarlaDataProvider.get_map().get_waypoint_xodr(
            int(ego_lane_position['lane'].replace("lane_", "")),
            ego_lane_position['roadID'],
            ego_lane_position['offset']
        ).transform

        new_actor = ActorConfigurationData(
            model = self.data["ego"]["name"],
            transform = spawn_point,
            speed = self.data["ego"]["start"]["speed"],
            rolename = self.data["ego"]["ID"],
            random = False,
            color = self.data["ego"]["color"]
        )
        self.ego_vehicles.append(new_actor)
    
    def set_npc_vehicle(self):
        for npc in self.data["npcList"]:
            npc_lane_position = npc["start"]["lane_position"]
            spawn_point = CarlaDataProvider.get_map().get_waypoint_xodr(
                int(npc_lane_position['lane'].replace("lane_", "")),
                npc_lane_position['roadID'],
                npc_lane_position['offset']
            ).transform
            new_actor = ActorConfigurationData(
                model = npc["name"],
                transform = spawn_point,
                speed = npc["start"]["speed"],
                rolename = npc["ID"],
                random = True,
                color = npc["color"]
            )
            self.other_actors.append(new_actor)

    def _set_carla_town(self):
        world = self.client.get_world()
        carlamap = None
        if world:
            world.get_settings()
            carlamap = world.get_map()
        if world is None or (carlamap is not None and carlamap.name.split('/')[-1] != self.town):
            self.client.load_world(self.town)
            time.sleep(5)
            world = self.client.get_world()

            CarlaDataProvider.set_world(world)
            if CarlaDataProvider.is_sync_mode():
                world.tick()
            else:
                world.wait_for_tick()
        else:
            CarlaDataProvider.set_world(world)
