import json
#import math
import copy
import re

#from gflownet.path_config import path_args

RES_LEVEL_SPEED = 0.5
RES_LEVEL_POS = 0.5

def my_round(value, level):
    return round(value / level) * level

def make_env_actions(scenario, actionSeq):
    # Minute is not considered
    actionSeq.append('time+' + str(scenario['time']['hour']))
    actionSeq.append('weather+rain+' + str(round(scenario['weather']['rain'], 1)))
    actionSeq.append('weather+wetness+' + str(round(scenario['weather']['wetness'], 1)))
    actionSeq.append('weather+fog+' + str(round(scenario['weather']['fog'], 1)))
    actionSeq.append('weather+sunny+' + str(round(scenario['weather']['sunny'], 1)))

def make_env_actions_space(scenario, actionSpace):
    # Minute is not considered
    if 'time+' not in actionSpace:
        actionSpace['time+'] = set()
    actionSpace['time+'].add(round(scenario['time']['hour'], 1))
    if 'weather+rain+' not in actionSpace:
        actionSpace['weather+rain+'] = set()
    actionSpace['weather+rain+'].add(round(scenario['weather']['rain'], 1))
    if 'weather+wetness+' not in actionSpace:
        actionSpace['weather+wetness+'] = set()
    actionSpace['weather+wetness+'].add(round(scenario['weather']['wetness'], 1))
    if 'weather+fog+' not in actionSpace:
        actionSpace['weather+fog+'] = set()
    actionSpace['weather+fog+'].add(round(scenario['weather']['fog'], 1))
    if 'weather+sunny+' not in actionSpace:
        actionSpace['weather+sunny+'] = set()
    actionSpace['weather+sunny+'].add(round(scenario['weather']['sunny'], 1))

def make_ego_actions(scenario, actionSeq):
    pos = scenario['ego']['start']['lane_position']
    actionSeq.append('ego+start+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], RES_LEVEL_POS)))
    actionSeq.append('ego+start+speed+' + str(my_round(scenario['ego']['start']['speed'], RES_LEVEL_SPEED)))
    pos = scenario['ego']['destination']['lane_position']
    actionSeq.append('ego+destination+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], RES_LEVEL_POS)))
    actionSeq.append('ego+destination+speed+' + str(my_round(scenario['ego']['destination']['speed'], RES_LEVEL_SPEED)))

def make_ego_actions_space(scenario, actionSpace):
    poition = scenario['ego']['start']['lane_position']
    type_name = 'ego+start+lane_position+' + poition['lane'] + "+"
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(poition['offset'], RES_LEVEL_POS))

    type_name = 'ego+start+speed+'
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(scenario['ego']['start']['speed'], RES_LEVEL_SPEED))

    poition = scenario['ego']['destination']['lane_position']
    type_name = 'ego+destination+lane_position+' + poition['lane'] + "+"
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(poition['offset'], RES_LEVEL_POS))

    type_name = 'ego+destination+speed+'
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(my_round(scenario['ego']['destination']['speed'], RES_LEVEL_SPEED))

def make_npc_actions(scenario, actionSeq):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        pos = npc['start']['lane_position']
        #actionSeq.append(npcid + '+name+' + npc['name'])
        actionSeq.append(npcid + '+start+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], RES_LEVEL_POS)))
        actionSeq.append(npcid + '+start+speed+' + str(my_round(npc['start']['speed'], RES_LEVEL_SPEED)))
        for i, waypoint in enumerate(npc['motion']):
            pos = waypoint['lane_position']
            actionSeq.append(npcid + '+motion+' + str(i) + '+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], RES_LEVEL_POS)))
            actionSeq.append(npcid + '+motion+' + str(i) + '+speed+' + str(my_round(waypoint['speed'], RES_LEVEL_SPEED)))
        if npc['destination'] is None:
            continue
        pos = npc['destination']['lane_position']
        actionSeq.append(npcid + '+destination+lane_position+' + pos['lane'] + '+' + str(my_round(pos['offset'], RES_LEVEL_POS)))
        actionSeq.append(npcid + '+destination+speed+' + str(my_round(npc['destination']['speed'], RES_LEVEL_SPEED)))

def make_npc_actions_space(scenario, actionSpace):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        type_name = npcid + '+name+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(npc['name'])

        lp = npc['start']['lane_position']
        type_name = npcid + '+start+lane_position+' + lp['lane'] + '+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(lp['offset'], RES_LEVEL_POS))
        type_name = npcid + '+start+speed+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(npc['start']['speed'], RES_LEVEL_SPEED))
        for i, waypoint in enumerate(npc['motion']):
            type_name = npcid + '+motion+' + str(i) + '+lane_position+' + waypoint['lane_position']['lane'] + '+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(my_round(waypoint['lane_position']['offset'], RES_LEVEL_POS))
            type_name = npcid + '+motion+' + str(i) + '+speed+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(my_round(waypoint['speed'], RES_LEVEL_SPEED))
        if npc['destination'] is None:
            continue
        lp = npc['destination']['lane_position']
        type_name = npcid + '+destination+lane_position+' + lp['lane'] + '+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(lp['offset'], RES_LEVEL_POS))
        type_name = npcid + '+destination+speed+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(my_round(npc['destination']['speed'], RES_LEVEL_SPEED))

def make_pedestrain_actions(scenario, actionSeq):
    pass

def make_obstacle_actions(scenario, actionSeq):
    pass

"""
Testable Scenario --> Action Sequence
"""
def encode(scenario):
    scenario['actions'] = []
    make_env_actions(scenario, scenario['actions'])
    make_ego_actions(scenario, scenario['actions'])
    make_npc_actions(scenario, scenario['actions'])
    make_pedestrain_actions(scenario, scenario['actions'])
    make_obstacle_actions(scenario, scenario['actions'])

"""
Action Sequence --> Testable Scenario
"""
def make_template(scenarioname, actionseq):
    npc_list = []
    npc_max_motion = {}
    for action in actionseq:
        list_str = action.split("+")
        if len(list_str) > 0 and "npc" in list_str[0]:
            if not list_str[0] in npc_list:
                npc_list.append(list_str[0])
            if not list_str[0] in npc_max_motion:
                npc_max_motion[list_str[0]] = 0
        if len(list_str) > 2 and list_str[1] == "motion":
            npc_max_motion[list_str[0]] = max(npc_max_motion[list_str[0]], int(list_str[2]))

    scenario = {}
    scenario["actions"] = actionseq
    scenario["ScenarioName"] = scenarioname
    scenario["map"] = "Town05"
    scenario["time"] = {
        "hour": 8,
        "minute": 0
    }
    scenario["weather"] = {
        "rain": 0.0,
        "sunny": 0.0,
        "wetness": 0.0,
        "fog": 0.0
    }
    scenario["ego"] = {
        "ID": "ego_vehicle",
        "name": "vehicle.tesla.model3",
        "color": "17,37,103",
        "start": {
            "lane_position": {
                "lane": "",
                "offset": 0.0,
                "roadID": None
            },
            "heading": {
                "ref_lane_point": {
                    "lane": "",
                    "offset": 0.0,
                    "roadID": None
                },
                "ref_angle": 0.0
            },
            "speed": 0.0
        },
        "destination": {
            "lane_position": {
                "lane": "",
                "offset": 0.0,
                "roadID": 1
            },
            "heading": {
                "ref_lane_point": {
                    "lane": "",
                    "offset": 0.0,
                    "roadID": None
                },
                "ref_angle": 0.0
            },
            "speed": 0.0
        },
    }
    
    scenario["npcList"] = []
    npc_dict = {
        "ID": "npc",
        "name": "",
        "color": None,
        "start":
        {
            "lane_position":
            {
                "lane": "",
                "offset": 0.0,
                "roadID": None
            },
            "heading":
            {
                "ref_lane_point":
                {
                    "lane": "",
                    "offset": 0.0,
                    "roadID": None
                },
                "ref_angle": 0.0
            },
            "speed": 0.0
        },
        "motion": [],
        "destination":
        {
            "lane_position":
            {
                "lane": "",
                "offset": 0.0,
                "roadID": None
            },
            "heading":
            {
                "ref_lane_point":
                {
                    "lane": "",
                    "offset": 0.0,
                    "roadID": None
                },
                "ref_angle": 0.0
            },
            "speed": 0.0
        }
    }

    motion = {
        "lane_position": {
            "lane": "",
            "offset": 0.0,
            "roadID": None
        },
        "heading": {
            "ref_lane_point": {
                "lane": "",
                "offset": 0.0,
                "roadID": None
            },
            "ref_angle": 0.0
        },
        "speed": 0.0
    }
    for npc in npc_list:
        new_npc_dict = copy.deepcopy(npc_dict)
        new_npc_dict["ID"] = npc
        if npc in npc_max_motion:
            for num in range(npc_max_motion[npc] + 1):
                new_npc_dict["motion"].append(copy.deepcopy(motion))
        scenario["npcList"].append(new_npc_dict)

    scenario["pedestrianList"] = []
    scenario["obstacleList"] = []
    scenario["AgentNames"] = npc_list

    return scenario

"""
def decode(scenario):
    for action in scenario["actions"]:
        list_str = action.split("+")
        if list_str[0] == "time":
            scenario[list_str[0]]["hour"] = int(list_str[-1])
        elif list_str[0] == "weather":
            scenario[list_str[0]][list_str[1]] = float(list_str[-1])
        elif list_str[0] == "ego":
            if list_str[2] == "lane_position":
                scenario[list_str[0]][list_str[1]][list_str[2]]["lane"] = list_str[3]
                scenario[list_str[0]][list_str[1]][list_str[2]]["offset"] = float(list_str[-1])
            elif list_str[2] == "speed":
                scenario[list_str[0]][list_str[1]][list_str[2]] = float(list_str[-1])
        elif list_str[0].startswith("npc"):
            idx = int(list_str[0].split("npc")[-1])
            if list_str[1] == "motion":
                if list_str[3] == "lane_position":
                    scenario["npcList"][idx][list_str[1]][int(list_str[2])][list_str[3]]["lane"] = list_str[-2]
                    scenario["npcList"][idx][list_str[1]][int(list_str[2])][list_str[3]]["offset"] = float(list_str[-1])
                elif list_str[3] == "speed":
                    scenario["npcList"][idx][list_str[1]][int(list_str[2])][list_str[3]] = float(list_str[-1])
            else:
                if list_str[2] == "lane_position":
                    scenario["npcList"][idx][list_str[1]][list_str[2]]["lane"] = list_str[3]
                    scenario["npcList"][idx][list_str[1]][list_str[2]]["offset"] = float(list_str[-1])
                elif list_str[2] == "speed":
                    scenario["npcList"][idx][list_str[1]][list_str[2]] = float(list_str[-1])
        elif action == "," or action == ".":
            pass
        else:
            assert False, "No matching for action: " + action
"""

def decode(scenario):
    offset_recorder = {}
    for action in scenario["actions"]:
        list_str = action.split("+")
        if list_str[0] == "time":
            scenario[list_str[0]]["hour"] = int(list_str[-1])
        elif list_str[0] == "weather":
            scenario[list_str[0]][list_str[1]] = float(list_str[-1])
        elif list_str[0] == "ego":
            if list_str[2] == "lane_position":
                scenario[list_str[0]][list_str[1]][list_str[2]]["lane"] = list_str[3]
                scenario[list_str[0]][list_str[1]][list_str[2]]["offset"] = float(list_str[-1])
            elif list_str[2] == "speed":
                scenario[list_str[0]][list_str[1]][list_str[2]] = float(list_str[-1])
        elif list_str[0].startswith("npc"):
            idx = int(list_str[0].split("npc")[-1])
            if list_str[1] == "motion":
                if list_str[3] == "lane_position":
                    npc_roadid = list_str[0] + '+' + list_str[-2]
                    if npc_roadid in offset_recorder and offset_recorder[npc_roadid] >= float(list_str[-1]):
                        scenario["npcList"][idx][list_str[1]][int(list_str[2])][list_str[3]]["lane"] = ""
                        continue
                    else:
                        offset_recorder[npc_roadid] = float(list_str[-1])
                    scenario["npcList"][idx][list_str[1]][int(list_str[2])][list_str[3]]["lane"] = list_str[-2]
                    scenario["npcList"][idx][list_str[1]][int(list_str[2])][list_str[3]]["offset"] = float(list_str[-1])
                elif list_str[3] == "speed":
                    scenario["npcList"][idx][list_str[1]][int(list_str[2])][list_str[3]] = float(list_str[-1])
            else:
                if list_str[2] == "lane_position":
                    scenario["npcList"][idx][list_str[1]][list_str[2]]["lane"] = list_str[-2]
                    scenario["npcList"][idx][list_str[1]][list_str[2]]["offset"] = float(list_str[-1])
                elif list_str[2] == "speed":
                    scenario["npcList"][idx][list_str[1]][list_str[2]] = float(list_str[-1])
        else:
            assert False, "No matching for action: " + action

    for npc in scenario["npcList"]:
        new_motion = []
        for motion in npc["motion"]:
            if len(motion["lane_position"]["lane"]) > 0:
                new_motion.append(motion)
        npc["motion"] = new_motion

    for npc in scenario["npcList"]:
        if (npc["ID"] + '+' + npc["destination"]["lane_position"]["lane"]) in offset_recorder and offset_recorder[npc["ID"] + '+' + npc["destination"]["lane_position"]["lane"]] > npc["destination"]["lane_position"]["offset"]:
            npc["destination"]["lane_position"]["offset"] = offset_recorder[npc["ID"] + '+' + npc["destination"]["lane_position"]["lane"]]

if __name__ == '__main__':
    import os
    actionseq_dir = os.environ["HOME"] + "/scenario_runner_able_edition/Law_Judgement/generated_actionseq/"
    scenarios_dir = os.environ["HOME"] + "/scenario_runner_able_edition/Law_Judgement/generated_scenarios/"
    for actionseq_file in os.listdir(actionseq_dir):
        print(actionseq_file)
        with open(actionseq_dir + actionseq_file) as file:
            action_sequence_list = json.load(file)
        generated_scenarios = []
        for actionseq in action_sequence_list:
            generated_scenario = make_template(actionseq["ScenarioName"], actionseq["actions"])
            decode(generated_scenario)
            generated_scenarios.append(generated_scenario)

        with open(scenarios_dir + actionseq_file, 'w') as wf:
            json.dump(generated_scenarios, wf, indent=4)
