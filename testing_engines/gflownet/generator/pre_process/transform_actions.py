import json
import os

from testing_engines.gflownet.path_config import path_args


def return_weather_level(value):
    level = 0
    interval_num = 5
    scale = 1.0 / interval_num
    for i in range(5):
        if value - scale > 0:
            value -= scale
            level += 1
        else:
            break
    return str(round((level + 0.5) * scale, 2))

def return_offset_level(position):
    higher_bound = 210.0
    interval_num = 10
    offset = position['offset']
    assert (offset <= higher_bound)
    scale = higher_bound / interval_num
    level = 0
    for i in range(5):
        if offset - scale > 0:
            offset -= scale
            level += 1
        else:
            break
    return position['lane'] + '+' + str((level + 0.5) * scale)

def return_speed_level(value):
    if value == 0:
        return "0"
    level = 0
    interval_num = 5
    scale = 10 / interval_num
    for i in range(10):
        if value - scale > 0:
            value -= scale
            level += 1
        else:
            break
    return str(round((level + 0.5) * scale, 2))

def make_env_actions(scenario, actionSeq):
    # Minute is not considered
    actionSeq.append('time+' + str(scenario['time']['hour']))
    actionSeq.append('weather+rain+' + return_weather_level(scenario['weather']['rain']))
    actionSeq.append('weather+wetness+' + return_weather_level(scenario['weather']['wetness']))
    actionSeq.append('weather+fog+' + return_weather_level(scenario['weather']['fog']))

def make_env_actions_space(scenario, actionSpace):
    # Minute is not considered
    if 'time+' not in actionSpace:
        actionSpace['time+'] = set()
    actionSpace['time+'].add(round(scenario['time']['hour'],1))
    if 'weather+rain+' not in actionSpace:
        actionSpace['weather+rain+'] = set()
    actionSpace['weather+rain+'].add(round(scenario['weather']['rain'],1))
    if 'weather+wetness+' not in actionSpace:
        actionSpace['weather+wetness+'] = set()
    actionSpace['weather+wetness+'].add(round(scenario['weather']['wetness'],1))
    if 'weather+fog+' not in actionSpace:
        actionSpace['weather+fog+'] = set()
    actionSpace['weather+fog+'].add(round(scenario['weather']['fog'],1))

def make_ego_actions(scenario, actionSeq):
    pos = scenario['ego']['start']['lane_position']
    actionSeq.append('ego+start+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
    actionSeq.append('ego+start+speed+' + str(round(scenario['ego']['start']['speed'], 0)))
    pos = scenario['ego']['destination']['lane_position']
    actionSeq.append('ego+destination+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
    actionSeq.append('ego+destination+speed+' + str(round(scenario['ego']['destination']['speed'], 0)))


def make_ego_actions_space(scenario, actionSpace):
    poition = scenario['ego']['start']['lane_position']
    type_name = 'ego+start+lane_position+' + poition['lane'] + "+"
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(round(poition['offset'], 0))

    type_name = 'ego+start+speed+'
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(round(scenario['ego']['start']['speed'], 0))

    poition = scenario['ego']['destination']['lane_position']
    type_name = 'ego+destination+lane_position+' + poition['lane'] + "+"
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(round(poition['offset'], 0))

    type_name = 'ego+destination+speed+'
    if type_name not in actionSpace:
        actionSpace[type_name] = set()
    actionSpace[type_name].add(round(scenario['ego']['destination']['speed'], 0))


def make_npc_actions(scenario, actionSeq):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        pos = npc['start']['lane_position']
        actionSeq.append(npcid + '+start+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
        actionSeq.append(npcid + '+start+speed+' + str(round(npc['start']['speed'], 0)))
        for i, waypoint in enumerate(npc['motion']):
            pos = waypoint['lane_position']
            actionSeq.append(npcid + '+motion+' + str(i) + '+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
            actionSeq.append(npcid + '+motion+' + str(i) + '+speed+' + str(round(waypoint['speed'], 0)))
        if npc['destination'] is None:
            continue
        pos = npc['destination']['lane_position']
        actionSeq.append(npcid + '+destination+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
        actionSeq.append(npcid + '+destination+speed+' + str(round(npc['destination']['speed'], 0)))

def make_npc_actions_space(scenario, actionSpace):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        lp = npc['start']['lane_position']
        type_name = npcid + '+start+lane_position+' + lp['lane'] + '+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(round(lp['offset'], 0))
        type_name = npcid + '+start+speed+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(round(npc['start']['speed'], 0))
        for i, waypoint in enumerate(npc['motion']):
            type_name = npcid + '+motion+' + str(i) + '+lane_position+' + waypoint['lane_position']['lane'] + '+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(round(waypoint['lane_position']['offset'], 0))
            type_name = npcid + '+motion+' + str(i) + '+speed+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(round(waypoint['speed'], 0))
        if npc['destination'] is None:
            continue
        lp = npc['destination']['lane_position']
        type_name = npcid + '+destination+lane_position+' + lp['lane'] + '+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(round(lp['offset'],0))
        type_name = npcid + '+destination+speed+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(round(npc['destination']['speed'], 0))

def make_pedestrain_actions(scenario, actionSeq):
    pass

def make_obstacle_actions(scenario, actionSeq):
    pass

def generate_actions(path):
    action_sequences = []
    with open(path) as f:
        data = json.load(f)
        for scenario in data:
            print('Handling ' + scenario['ScenarioName'])
            action_sequences.append(encode(scenario))
    return action_sequences

"""
Testable Scenario --> Action Sequence
"""
def encode(scenario):
    for_one_scenario = {'ScenarioName': scenario['ScenarioName']}
    actions = []
    make_env_actions(scenario, actions)
    make_ego_actions(scenario, actions)
    make_npc_actions(scenario, actions)
    make_pedestrain_actions(scenario, actions)
    make_obstacle_actions(scenario, actions)
    for_one_scenario['actions'] = actions
    for_one_scenario['robustness'] = scenario['robustness']
    return for_one_scenario

"""
Action Sequence --> Testable Scenario
"""
def decode(action_sequence, session):
    template_path = path_args.template_path.format(session)
    # template_path = "../data/template_for_{}.json".format(session)
    with open(template_path) as file:
        template = json.load(file)
        template["ScenarioName"] = action_sequence["ScenarioName"]
        for action in action_sequence["actions"]:
            if action.startswith("time+"):
                hour = action.replace("time+", "")
                template["time"]["hour"] = int(hour)
            elif action.startswith("weather+rain+"):
                rain = action.replace("weather+rain+", "")
                template["weather"]["rain"] = float(rain)
            elif action.startswith("weather+wetness+"):
                wetness = action.replace("weather+wetness+", "")
                template["weather"]["wetness"] = float(wetness)
            elif action.startswith("weather+fog+"):
                fog = action.replace("weather+fog+", "")
                template["weather"]["fog"] = float(fog)
            # For double direction.
            elif action.startswith("ego+start+lane_position+lane_540+"):
                start_offset = action.replace("ego+start+lane_position+lane_540+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+start+speed+"):
                start_speed = action.replace("ego+start+speed+", "")
                template["ego"]["start"]["speed"] = float(start_speed)
            elif action.startswith("ego+destination+lane_position+lane_572+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_572+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            elif action.startswith("ego+destination+speed+"):
                dest_speed = action.replace("ego+destination+speed+", "")
                template["ego"]["destination"]["speed"] = float(dest_speed)
            # NPC1
            elif action.startswith("npc1+start+lane_position+lane_574+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_574+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc1+start+speed+"):
                npc1_start_speed = action.replace("npc1+start+speed+", "")
                template["npcList"][0]["start"]["speed"] = float(npc1_start_speed)
            elif action.startswith("npc1+motion+0+lane_position+lane_569+"):
                npc1_motion_offset = action.replace("npc1+motion+0+lane_position+lane_569+", "")
                template["npcList"][0]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+0+speed+"):
                npc1_motion_speed = action.replace("npc1+motion+0+speed+", "")
                template["npcList"][0]["motion"][0]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc1+destination+lane_position+lane_569+"):
                npc1_dest_offset = action.replace("npc1+destination+lane_position+lane_569+", "")
                template["npcList"][0]["destination"]["lane_position"]["offset"] = float(npc1_dest_offset)
            elif action.startswith("npc1+destination+speed+"):
                npc1_dest_speed = action.replace("npc1+destination+speed+", "")
                template["npcList"][0]["destination"]["speed"] = float(npc1_dest_speed)
            # NPC2
            elif action.startswith("npc2+start+lane_position+lane_564+"):
                npc2_start_offset = action.replace("npc2+start+lane_position+lane_564+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc2_start_offset)
            elif action.startswith("npc2+start+speed+"):
                npc2_start_speed = action.replace("npc2+start+speed+", "")
                template["npcList"][1]["start"]["speed"] = float(npc2_start_speed)
            elif action.startswith("npc2+motion+0+lane_position+lane_568+"):
                npc2_motion_offset = action.replace("npc2+motion+0+lane_position+lane_568+", "")
                template["npcList"][1]["motion"][0]["lane_position"]["offset"] = float(npc2_motion_offset)
            elif action.startswith("npc2+motion+0+speed+"):
                npc2_motion_speed = action.replace("npc2+motion+0+speed+", "")
                template["npcList"][1]["motion"][0]["speed"] = float(npc2_motion_speed)
            elif action.startswith("npc2+destination+lane_position+lane_568+"):
                npc2_dest_offset = action.replace("npc2+destination+lane_position+lane_568+", "")
                template["npcList"][1]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            elif action.startswith("npc2+destination+speed+"):
                npc2_dest_speed = action.replace("npc2+destination+speed+", "")
                template["npcList"][1]["destination"]["speed"] = float(npc2_dest_speed)
            # NPC3
            elif action.startswith("npc3+start+lane_position+lane_565+"):
                npc3_start_offset = action.replace("npc3+start+lane_position+lane_565+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc3+start+speed+"):
                npc3_start_speed = action.replace("npc3+start+speed+", "")
                template["npcList"][2]["start"]["speed"] = float(npc3_start_speed)
            elif action.startswith("npc3+motion+0+lane_position+lane_569+"):
                npc3_motion_offset = action.replace("npc3+motion+0+lane_position+lane_569+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc3+motion+0+speed+"):
                npc3_motion_speed = action.replace("npc3+motion+0+speed+", "")
                template["npcList"][2]["motion"][0]["speed"] = float(npc3_motion_speed)
            elif action.startswith("npc3+destination+lane_position+lane_569+"):
                npc3_dest_offset = action.replace("npc3+destination+lane_position+lane_569+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc3+destination+speed+"):
                npc3_dest_speed = action.replace("npc3+destination+speed+", "")
                template["npcList"][2]["destination"]["speed"] = float(npc3_dest_speed)
            # NPC4
            elif action.startswith("npc4+start+lane_position+lane_570+"):
                npc4_start_offset = action.replace("npc4+start+lane_position+lane_570+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc4_start_offset)
            elif action.startswith("npc4+start+speed+"):
                npc4_start_speed = action.replace("npc4+start+speed+", "")
                template["npcList"][3]["start"]["speed"] = float(npc4_start_speed)
            elif action.startswith("npc4+motion+0+lane_position+lane_566+"):
                npc4_motion_offset = action.replace("npc4+motion+0+lane_position+lane_566+", "")
                template["npcList"][3]["motion"][0]["lane_position"]["offset"] = float(npc4_motion_offset)
            elif action.startswith("npc4+motion+0+speed+"):
                npc4_motion_speed = action.replace("npc4+motion+0+speed+", "")
                template["npcList"][3]["motion"][0]["speed"] = float(npc4_motion_speed)
            elif action.startswith("npc4+destination+lane_position+lane_566+"):
                npc4_dest_offset = action.replace("npc4+destination+lane_position+lane_566+", "")
                template["npcList"][3]["destination"]["lane_position"]["offset"] = float(npc4_dest_offset)
            elif action.startswith("npc4+destination+speed+"):
                npc4_dest_speed = action.replace("npc4+destination+speed+", "")
                template["npcList"][3]["destination"]["speed"] = float(npc4_dest_speed)
            # NPC5
            elif action.startswith("npc5+start+lane_position+lane_571+"):
                npc5_start_offset = action.replace("npc5+start+lane_position+lane_571+", "")
                template["npcList"][4]["start"]["lane_position"]["offset"] = float(npc5_start_offset)
            elif action.startswith("npc5+start+speed+"):
                npc5_start_speed = action.replace("npc5+start+speed+", "")
                template["npcList"][4]["start"]["speed"] = float(npc5_start_speed)
            elif action.startswith("npc5+motion+0+lane_position+lane_567+"):
                npc5_motion_offset = action.replace("npc5+motion+0+lane_position+lane_567+", "")
                template["npcList"][4]["motion"][0]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+0+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+0+speed+", "")
                template["npcList"][4]["motion"][0]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+destination+lane_position+lane_567+"):
                npc5_dest_offset = action.replace("npc5+destination+lane_position+lane_567+", "")
                template["npcList"][4]["destination"]["lane_position"]["offset"] = float(npc5_dest_offset)
            elif action.startswith("npc5+destination+speed+"):
                npc5_dest_speed = action.replace("npc5+destination+speed+", "")
                template["npcList"][4]["destination"]["speed"] = float(npc5_dest_speed)
            # For the entities in single direction
            elif action.startswith("ego+start+lane_position+lane_623+"):
                start_offset = action.replace("ego+start+lane_position+lane_623+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+destination+lane_position+lane_145+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_145+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            elif action.startswith("npc1+start+lane_position+lane_627+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_627+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc1+motion+0+lane_position+lane_627+"):
                npc1_motion_offset = action.replace("npc1+motion+0+lane_position+lane_627+", "")
                template["npcList"][0]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+1+lane_position+lane_627+"):
                npc5_motion_offset = action.replace("npc1+motion+1+lane_position+lane_627+", "")
                template["npcList"][0]["motion"][1]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+1+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+1+speed+", "")
                template["npcList"][0]["motion"][1]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+2+lane_position+lane_627+"):
                npc5_motion_offset = action.replace("npc1+motion+2+lane_position+lane_627+", "")
                template["npcList"][0]["motion"][2]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+2+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+2+speed+", "")
                template["npcList"][0]["motion"][2]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+3+lane_position+lane_899+"):
                npc5_motion_offset = action.replace("npc1+motion+3+lane_position+lane_899+", "")
                template["npcList"][0]["motion"][3]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+3+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+3+speed+", "")
                template["npcList"][0]["motion"][3]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+4+lane_position+lane_145+"):
                npc5_motion_offset = action.replace("npc1+motion+4+lane_position+lane_145+", "")
                template["npcList"][0]["motion"][4]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+4+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+4+speed+", "")
                template["npcList"][0]["motion"][4]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+motion+5+lane_position+lane_145+"):
                npc5_motion_offset = action.replace("npc1+motion+5+lane_position+lane_145+", "")
                template["npcList"][0]["motion"][5]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc1+motion+5+speed+"):
                npc5_motion_speed = action.replace("npc1+motion+5+speed+", "")
                template["npcList"][0]["motion"][5]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc1+destination+lane_position+lane_145+"):
                npc1_start_offset = action.replace("npc1+destination+lane_position+lane_145+", "")
                template["npcList"][0]["destination"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc2+start+lane_position+lane_627+"):
                npc3_start_offset = action.replace("npc2+start+lane_position+lane_627+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc2+motion+0+lane_position+lane_151+"):
                npc3_motion_offset = action.replace("npc2+motion+0+lane_position+lane_151+", "")
                template["npcList"][1]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc2+destination+lane_position+lane_151+"):
                npc3_dest_offset = action.replace("npc2+destination+lane_position+lane_151+", "")
                template["npcList"][1]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc3+start+lane_position+lane_626+"):
                npc3_start_offset = action.replace("npc3+start+lane_position+lane_626+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc3+motion+0+lane_position+lane_150+"):
                npc3_motion_offset = action.replace("npc3+motion+0+lane_position+lane_150+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc3+destination+lane_position+lane_150+"):
                npc3_dest_offset = action.replace("npc3+destination+lane_position+lane_150+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc4+start+lane_position+lane_625+"):
                npc3_start_offset = action.replace("npc4+start+lane_position+lane_625+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc4+motion+0+lane_position+lane_149+"):
                npc3_motion_offset = action.replace("npc4+motion+0+lane_position+lane_149+", "")
                template["npcList"][3]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc4+destination+lane_position+lane_149+"):
                npc3_dest_offset = action.replace("npc4+destination+lane_position+lane_149+", "")
                template["npcList"][3]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            # For the entities in lane change
            elif action.startswith("ego+start+lane_position+lane_221+"):
                start_offset = action.replace("ego+start+lane_position+lane_221+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+destination+lane_position+lane_220+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_220+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            elif action.startswith("npc1+start+lane_position+lane_221+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_221+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc2+start+lane_position+lane_221+"):
                npc2_start_offset = action.replace("npc2+start+lane_position+lane_221+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc2_start_offset)
            elif action.startswith("npc3+start+lane_position+lane_220+"):
                npc3_start_offset = action.replace("npc3+start+lane_position+lane_220+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            elif action.startswith("npc3+motion+0+lane_position+lane_231+"):
                npc3_motion_offset = action.replace("npc3+motion+0+lane_position+lane_231+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            elif action.startswith("npc3+destination+lane_position+lane_231+"):
                npc3_dest_offset = action.replace("npc3+destination+lane_position+lane_231+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            elif action.startswith("npc4+start+lane_position+lane_220+"):
                npc4_start_offset = action.replace("npc4+start+lane_position+lane_220+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc4_start_offset)
            elif action.startswith("npc5+start+lane_position+lane_220+"):
                npc5_start_offset = action.replace("npc5+start+lane_position+lane_220+", "")
                template["npcList"][4]["start"]["lane_position"]["offset"] = float(npc5_start_offset)
            elif action.startswith("npc5+motion+0+lane_position+lane_220+"):
                npc5_motion_offset = action.replace("npc5+motion+0+lane_position+lane_220+", "")
                template["npcList"][4]["motion"][0]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+1+lane_position+lane_220+"):
                npc5_motion_offset = action.replace("npc5+motion+1+lane_position+lane_220+", "")
                template["npcList"][4]["motion"][1]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+1+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+1+speed+", "")
                template["npcList"][4]["motion"][1]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+2+lane_position+lane_1037+"):
                npc5_motion_offset = action.replace("npc5+motion+2+lane_position+lane_1037+", "")
                template["npcList"][4]["motion"][2]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+2+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+2+speed+", "")
                template["npcList"][4]["motion"][2]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+3+lane_position+lane_1037+"):
                npc5_motion_offset = action.replace("npc5+motion+3+lane_position+lane_1037+", "")
                template["npcList"][4]["motion"][3]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+3+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+3+speed+", "")
                template["npcList"][4]["motion"][3]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+4+lane_position+lane_253+"):
                npc5_motion_offset = action.replace("npc5+motion+4+lane_position+lane_253+", "")
                template["npcList"][4]["motion"][4]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+4+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+4+speed+", "")
                template["npcList"][4]["motion"][4]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+motion+5+lane_position+lane_253+"):
                npc5_motion_offset = action.replace("npc5+motion+5+lane_position+lane_253+", "")
                template["npcList"][4]["motion"][5]["lane_position"]["offset"] = float(npc5_motion_offset)
            elif action.startswith("npc5+motion+5+speed+"):
                npc5_motion_speed = action.replace("npc5+motion+5+speed+", "")
                template["npcList"][4]["motion"][5]["speed"] = float(npc5_motion_speed)
            elif action.startswith("npc5+destination+lane_position+lane_253+"):
                npc1_start_offset = action.replace("npc5+destination+lane_position+lane_253+", "")
                template["npcList"][4]["destination"]["lane_position"]["offset"] = float(npc1_start_offset)
            # For the entities in t-junction
            elif action.startswith("ego+start+lane_position+lane_317+"):
                start_offset = action.replace("ego+start+lane_position+lane_317+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            elif action.startswith("ego+destination+lane_position+lane_321+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_321+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            # NPC1
            elif action.startswith("npc1+start+lane_position+lane_328+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_328+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc1+motion+0+lane_position+lane_328+"):
                npc1_motion_offset = action.replace("npc1+motion+0+lane_position+lane_328+", "")
                template["npcList"][0]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+1+lane_position+lane_328+"):
                npc1_motion_offset = action.replace("npc1+motion+1+lane_position+lane_328+", "")
                template["npcList"][0]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+2+lane_position+lane_328+"):
                npc1_motion_offset = action.replace("npc1+motion+2+lane_position+lane_328+", "")
                template["npcList"][0]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+3+lane_position+lane_1158+"):
                npc1_motion_offset = action.replace("npc1+motion+3+lane_position+lane_1158+", "")
                template["npcList"][0]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+4+lane_position+lane_1158+"):
                npc1_motion_offset = action.replace("npc1+motion+4+lane_position+lane_1158+", "")
                template["npcList"][0]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+5+lane_position+lane_320+"):
                npc1_motion_offset = action.replace("npc1+motion+5+lane_position+lane_320+", "")
                template["npcList"][0]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+5+lane_position+lane_320+"):
                npc1_motion_offset = action.replace("npc1+motion+5+lane_position+lane_320+", "")
                template["npcList"][0]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+6+lane_position+lane_1206+"):
                npc1_motion_offset = action.replace("npc1+motion+6+lane_position+lane_1206+", "")
                template["npcList"][0]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc1+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc1+motion+6+speed+", "")
                template["npcList"][0]["motion"][6]["speed"] = float(npc1_motion_speed)
            # NPC2
            elif action.startswith("npc2+start+lane_position+lane_331+"):
                npc1_start_offset = action.replace("npc2+start+lane_position+lane_331+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc2+motion+0+lane_position+lane_331+"):
                npc1_motion_offset = action.replace("npc2+motion+0+lane_position+lane_331+", "")
                template["npcList"][1]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+1+lane_position+lane_331+"):
                npc1_motion_offset = action.replace("npc2+motion+1+lane_position+lane_331+", "")
                template["npcList"][1]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+1+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+1+speed+", "")
                template["npcList"][1]["motion"][1]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+2+lane_position+lane_1160+"):
                npc1_motion_offset = action.replace("npc2+motion+2+lane_position+lane_1160+", "")
                template["npcList"][1]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+2+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+2+speed+", "")
                template["npcList"][1]["motion"][2]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+3+lane_position+lane_1158+"):
                npc1_motion_offset = action.replace("npc2+motion+3+lane_position+lane_1158+", "")
                template["npcList"][1]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+3+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+3+speed+", "")
                template["npcList"][1]["motion"][3]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+4+lane_position+lane_321+"):
                npc1_motion_offset = action.replace("npc2+motion+4+lane_position+lane_321+", "")
                template["npcList"][1]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+4+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+4+speed+", "")
                template["npcList"][1]["motion"][4]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+5+lane_position+lane_321+"):
                npc1_motion_offset = action.replace("npc2+motion+5+lane_position+lane_321+", "")
                template["npcList"][1]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+5+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+5+speed+", "")
                template["npcList"][1]["motion"][5]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+motion+6+lane_position+lane_321+"):
                npc1_motion_offset = action.replace("npc2+motion+6+lane_position+lane_321+", "")
                template["npcList"][1]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc2+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc2+motion+6+speed+", "")
                template["npcList"][1]["motion"][6]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc2+destination+lane_position+lane_321+"):
                npc2_dest_offset = action.replace("npc2+destination+lane_position+lane_321+", "")
                template["npcList"][1]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            # NPC3
            elif action.startswith("npc3+start+lane_position+lane_330+"):
                npc1_start_offset = action.replace("npc3+start+lane_position+lane_330+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc3+motion+0+lane_position+lane_330+"):
                npc1_motion_offset = action.replace("npc3+motion+0+lane_position+lane_330+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+1+lane_position+lane_330+"):
                npc1_motion_offset = action.replace("npc3+motion+1+lane_position+lane_330+", "")
                template["npcList"][2]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+1+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+1+speed+", "")
                template["npcList"][2]["motion"][1]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+2+lane_position+lane_1161+"):
                npc1_motion_offset = action.replace("npc3+motion+2+lane_position+lane_1161+", "")
                template["npcList"][2]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+2+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+2+speed+", "")
                template["npcList"][2]["motion"][2]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+3+lane_position+lane_1157+"):
                npc1_motion_offset = action.replace("npc3+motion+3+lane_position+lane_1157+", "")
                template["npcList"][2]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+3+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+3+speed+", "")
                template["npcList"][2]["motion"][3]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+4+lane_position+lane_322+"):
                npc1_motion_offset = action.replace("npc3+motion+4+lane_position+lane_322+", "")
                template["npcList"][2]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+4+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+4+speed+", "")
                template["npcList"][2]["motion"][4]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+5+lane_position+lane_322+"):
                npc1_motion_offset = action.replace("npc3+motion+5+lane_position+lane_322+", "")
                template["npcList"][2]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+5+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+5+speed+", "")
                template["npcList"][2]["motion"][5]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+motion+6+lane_position+lane_322+"):
                npc1_motion_offset = action.replace("npc3+motion+6+lane_position+lane_322+", "")
                template["npcList"][2]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc3+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc3+motion+6+speed+", "")
                template["npcList"][2]["motion"][6]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc3+destination+lane_position+lane_322+"):
                npc2_dest_offset = action.replace("npc3+destination+lane_position+lane_322+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            # NPC4
            elif action.startswith("npc4+start+lane_position+lane_329+"):
                npc1_start_offset = action.replace("npc4+start+lane_position+lane_329+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            elif action.startswith("npc4+motion+0+lane_position+lane_329+"):
                npc1_motion_offset = action.replace("npc4+motion+0+lane_position+lane_329+", "")
                template["npcList"][3]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+1+lane_position+lane_329+"):
                npc1_motion_offset = action.replace("npc4+motion+1+lane_position+lane_329+", "")
                template["npcList"][3]["motion"][1]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+1+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+1+speed+", "")
                template["npcList"][3]["motion"][1]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+2+lane_position+lane_1162+"):
                npc1_motion_offset = action.replace("npc4+motion+2+lane_position+lane_1162+", "")
                template["npcList"][3]["motion"][2]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+2+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+2+speed+", "")
                template["npcList"][3]["motion"][2]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+3+lane_position+lane_1157+"):
                npc1_motion_offset = action.replace("npc4+motion+3+lane_position+lane_1157+", "")
                template["npcList"][3]["motion"][3]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+3+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+3+speed+", "")
                template["npcList"][3]["motion"][3]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+4+lane_position+lane_323+"):
                npc1_motion_offset = action.replace("npc4+motion+4+lane_position+lane_323+", "")
                template["npcList"][3]["motion"][4]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+4+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+4+speed+", "")
                template["npcList"][3]["motion"][4]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+5+lane_position+lane_323+"):
                npc1_motion_offset = action.replace("npc4+motion+5+lane_position+lane_323+", "")
                template["npcList"][3]["motion"][5]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+5+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+5+speed+", "")
                template["npcList"][3]["motion"][5]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+motion+6+lane_position+lane_323+"):
                npc1_motion_offset = action.replace("npc4+motion+6+lane_position+lane_323+", "")
                template["npcList"][3]["motion"][6]["lane_position"]["offset"] = float(npc1_motion_offset)
            elif action.startswith("npc4+motion+6+speed+"):
                npc1_motion_speed = action.replace("npc4+motion+6+speed+", "")
                template["npcList"][3]["motion"][6]["speed"] = float(npc1_motion_speed)
            elif action.startswith("npc4+destination+lane_position+lane_323+"):
                npc2_dest_offset = action.replace("npc4+destination+lane_position+lane_323+", "")
                template["npcList"][3]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            else:
                assert False, "No matching for action: " + action
    return template

def generate_actions_space(path):
    action_space = {}
    with open(path) as f:
        data = json.load(f)
        for scenario in data:
            print('Handling ' + scenario['ScenarioName'])
            make_env_actions_space(scenario, action_space)
            make_ego_actions_space(scenario, action_space)
            make_npc_actions_space(scenario, action_space)
    return action_space

def gen_dataset_from_rawdata(session):
    action_seqs = None
    raw_data_path = '../../rawdata/one_scenario/testset_for_' + session + '.json'
    action_dataset_path = '../data/a_testset_for_' + session + '.json'
    action_space_path = '../data/space_for_' + session + '.json'

    # action_seqs = generate_actions(raw_data_path)
    action_space = generate_actions_space(raw_data_path)
    # For Debugging
    # with open(action_dataset_path, 'w', encoding='utf-8') as f:
    #     json.dump(action_seqs, f, ensure_ascii=False, indent=4)
    with open(action_space_path, 'w', encoding='utf-8') as f:
        for key, value in action_space.items():
            action_space[key] = sorted(list(value))
        json.dump(action_space, f, ensure_ascii=False, indent=4)
    return action_seqs


def generate_scenarios_batch(session):
    test_cases_batch = []
    # data_path = '../data/a_testset_for_{}.json'.format(session)
    data_path = "/home/xdzhang/work/shortgun/testing_engines/gflownet/generator/data/one_action_sequence.json"
    with open(data_path) as file:
        dataset = json.load(file)
        for item in dataset:
            test_cases_batch.append(decode(item, session))
    result_path = '../data/Scenarios_{}.json'.format(session)
    with open(result_path, 'w') as wf:
        json.dump(test_cases_batch, wf, indent=4)
    return test_cases_batch

def normalization_space(action_space):
    pass


if __name__ == '__main__':
    # sessions = ['single_direction', 'double_direction', 'lane_change']
    sessions = ['t_junction']
    for session in sessions:
        print("Handling {}".format(session))
        gen_dataset_from_rawdata(session)
        # generate_scenarios_batch(session)