#!/usr/bin/env python3

import carla
import time

host = "127.0.0.1"
port = 2000

def get_world(client):
    world = client.get_world()
    return world

def get_map(world):
    carlamap = world.get_map()
    return carlamap

if __name__ == '__main__':
    world = None
    while world is None:
        time.sleep(1.0)
        world = get_world(carla.Client(host, port))

    carlamap = get_map(world)
    spectator = world.get_spectator()
    while not world is None and not carlamap is None and not spectator is None:
        print("====================")
        wp = carlamap.get_waypoint(spectator.get_location(), project_to_road=True, lane_type=carla.LaneType.Driving)
        print("Road: {}, section: {}, lane: {}, lane s: {}, junction: {}.".format(wp.road_id, wp.section_id, wp.lane_id, wp.s, wp.junction_id))
        print(wp)

        traffic_light_dict = {}
        for traffic_light in world.get_actors().filter('*traffic_light*'):
            traffic_light_dict[traffic_light] = spectator.get_location().distance(traffic_light.get_location())
        #print(sorted(traffic_light_dict.items(), key=lambda x:x[1])[:4])
        for closest_traffic_light_tuple in sorted(traffic_light_dict.items(), key=lambda x:x[1])[:4]:
            print("-----")
            traffic_light = closest_traffic_light_tuple[0]
            distance = closest_traffic_light_tuple[1]
            print("Opendrive ID: {}, pole index: {}, state: {}, time: {}, {}, {}".format(\
                traffic_light.get_opendrive_id(), traffic_light.get_pole_index(), traffic_light.get_state(),\
                traffic_light.get_red_time(), traffic_light.get_yellow_time(), traffic_light.get_green_time()))
            print("Traffic light location: {}".format(traffic_light.get_location()))
        print("-----")

        left_wp = wp
        left_lane_amount = 0
        while not left_wp.get_left_lane() is None and left_wp.get_left_lane().lane_type == carla.LaneType.Driving and int(left_wp.get_left_lane().lane_id) * int(wp.lane_id) > 0:
            left_wp = left_wp.get_left_lane()
            left_lane_amount += 1
        right_wp = wp
        right_lane_amount = 0
        while not right_wp.get_right_lane() is None and right_wp.get_right_lane().lane_type == carla.LaneType.Driving and int(right_wp.get_right_lane().lane_id) * int(wp.lane_id) > 0:
            right_wp = right_wp.get_right_lane()
            right_lane_amount += 1
        left_wp = left_wp.next_until_lane_end(1)[-1]
        right_wp = right_wp.next_until_lane_end(1)[-1]
        if left_lane_amount + right_lane_amount > 0:
            delta_x = (left_wp.transform.location.x - right_wp.transform.location.x) / (left_lane_amount + right_lane_amount) / 2
            delta_y = (left_wp.transform.location.y - right_wp.transform.location.y) / (left_lane_amount + right_lane_amount) / 2
            print("Stop line point 1: x={}, y={}".format(left_wp.transform.location.x + delta_x, left_wp.transform.location.y + delta_y))
            print("Stop line point 2: x={}, y={}".format(right_wp.transform.location.x - delta_x, right_wp.transform.location.y - delta_y))
        time.sleep(1.0)