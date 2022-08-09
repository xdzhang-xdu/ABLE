import json
import math
import os

if __name__ == "__main__":
    path_lb = "apollo6/lawbreaker_total_data_cover_by_session.json"
    path_my = "apollo6/my_total_data_cover_by_session.json"
    print("compare between {} and {}".format(path_my, path_lb))
    with open(path_lb) as f:
        data_lb = json.load(f)
    with open(path_my) as f:
        data_my = json.load(f)
    print("For session double_direction -->")
    print("exist in mine but not in lawbreaker:")
    print("shortgun: {}".format(len(data_my["double_direction"])))
    print("lawbreaker: {}".format(len(data_lb["Intersection_with_Double-Direction_Roads"])))
    delta = set(data_my["double_direction"]).difference(set(data_lb["Intersection_with_Double-Direction_Roads"]))
    print(len(delta), delta)
    print("exist in lawbreaker but not in mine:")
    delta = set(set(data_lb["Intersection_with_Double-Direction_Roads"]).difference(data_my["double_direction"]))
    print(len(delta), delta)
    print("--------------")

    print("For session single_direction -->")
    print("exist in mine but not in lawbreaker:")
    print("shortgun: {}".format(len(data_my["single_direction"])))
    print("lawbreaker: {}".format(len(data_lb["Single-Direction-1"])))
    delta = set(data_my["single_direction"]).difference(set(data_lb["Single-Direction-1"]))
    print(len(delta), delta)
    print("exist in lawbreaker but not in mine:")
    delta = set(set(data_lb["Single-Direction-1"]).difference(data_my["single_direction"]))
    print(len(delta), delta)
    print("--------------")

    print("For session lane_change -->")
    print("exist in mine but not in lawbreaker:")
    print("shortgun: {}".format(len(data_my["lane_change"])))
    print("lawbreaker: {}".format(len(data_lb["lane_change_in_the_same_road"])))
    delta = set(data_my["lane_change"]).difference(set(data_lb["lane_change_in_the_same_road"]))
    print(len(delta), delta)
    print("exist in lawbreaker but not in mine:")
    delta = set(set(data_lb["lane_change_in_the_same_road"]).difference(data_my["lane_change"]))
    print(len(delta), delta)

    #
    # print("--------------")
    # print("For session t_junction -->")
    # print("exist in mine but not in lawbreaker:")
    # print("shortgun: {}".format(len(data_my["t_junction"])))
    # print("lawbreaker: {}".format(len(data_lb["T-Junction01"])))
    # delta = set(data_my["t_junction"]).difference(set(data_lb["T-Junction01"]))
    # print(len(delta), delta)
    # print("exist in lawbreaker but not in mine:")
    # delta = set(set(data_lb["T-Junction01"]).difference(data_my["t_junction"]))
    # print(len(delta), delta)

    ours = set(data_my["double_direction"]) | set(data_my["single_direction"]) | set(data_my["lane_change"])
           # | set(data_my["t_junction"])
    print(len(ours), ours)

    lb = set(data_lb["Intersection_with_Double-Direction_Roads"]) | set(data_lb["Single-Direction-1"]) | set(data_lb["lane_change_in_the_same_road"])
         # | set(data_lb["T-Junction01"])
    print(len(lb), lb)
    print("================")
    print(ours - lb)
    print(lb - ours)