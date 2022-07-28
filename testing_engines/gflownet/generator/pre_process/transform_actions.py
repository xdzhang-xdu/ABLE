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
    with open(template_path) as file:
        template = json.load(file)
        template["ScenarioName"] = action_sequence["ScenarioName"]
        for action in action_sequence["actions"]:
            if action.startswith("time+"):
                hour = action.replace("time+", "")
                template["time"]["hour"] = int(hour)
            if action.startswith("weather+rain+"):
                rain = action.replace("weather+rain+", "")
                template["weather"]["rain"] = float(rain)
            if action.startswith("weather+wetness+"):
                wetness = action.replace("weather+wetness+", "")
                template["weather"]["wetness"] = float(wetness)
            if action.startswith("weather+fog+"):
                fog = action.replace("weather+fog+", "")
                template["weather"]["fog"] = float(fog)
            # EGO car
            if action.startswith("ego+start+lane_position+lane_540+"):
                start_offset = action.replace("ego+start+lane_position+lane_540+", "")
                template["ego"]["start"]["lane_position"]["offset"] = float(start_offset)
            if action.startswith("ego+start+speed+"):
                start_speed = action.replace("ego+start+speed+", "")
                template["ego"]["start"]["speed"] = float(start_speed)
            if action.startswith("ego+destination+lane_position+lane_572+"):
                dest_offset = action.replace("ego+destination+lane_position+lane_572+", "")
                template["ego"]["destination"]["lane_position"]["offset"] = float(dest_offset)
            if action.startswith("ego+destination+speed+"):
                dest_speed = action.replace("ego+destination+speed+", "")
                template["ego"]["destination"]["speed"] = float(dest_speed)
            # NPC1
            if action.startswith("npc1+start+lane_position+lane_574+"):
                npc1_start_offset = action.replace("npc1+start+lane_position+lane_574+", "")
                template["npcList"][0]["start"]["lane_position"]["offset"] = float(npc1_start_offset)
            if action.startswith("npc1+start+speed+"):
                npc1_start_speed = action.replace("npc1+start+speed+", "")
                template["npcList"][0]["start"]["speed"] = float(npc1_start_speed)
            if action.startswith("npc1motion+0+lane_position+lane_569+"):
                npc1_motion_offset = action.replace("npc1motion+0+lane_position+lane_569+", "")
                template["npcList"][0]["motion"][0]["lane_position"]["offset"] = float(npc1_motion_offset)
            if action.startswith("npc1motion+0+speed+"):
                npc1_motion_speed = action.replace("npc1motion+0+speed+", "")
                template["npcList"][0]["motion"][0]["speed"] = float(npc1_motion_speed)
            if action.startswith("npc1+destination+lane_position+lane_569+"):
                npc1_dest_offset = action.replace("npc1+destination+lane_position+lane_569+", "")
                template["npcList"][0]["destination"]["lane_position"]["offset"] = float(npc1_dest_offset)
            if action.startswith("npc1+destination+speed+"):
                npc1_dest_speed = action.replace("npc1+destination+speed+", "")
                template["npcList"][0]["destination"]["speed"] = float(npc1_dest_speed)
            # NPC2
            if action.startswith("npc2+start+lane_position+lane_574+"):
                npc2_start_offset = action.replace("npc2+start+lane_position+lane_574+", "")
                template["npcList"][1]["start"]["lane_position"]["offset"] = float(npc2_start_offset)
            if action.startswith("npc2+start+speed+"):
                npc2_start_speed = action.replace("npc2+start+speed+", "")
                template["npcList"][1]["start"]["speed"] = float(npc2_start_speed)
            if action.startswith("npc2motion+0+lane_position+lane_569+"):
                npc2_motion_offset = action.replace("npc2motion+0+lane_position+lane_569+", "")
                template["npcList"][1]["motion"][0]["lane_position"]["offset"] = float(npc2_motion_offset)
            if action.startswith("npc2motion+0+speed+"):
                npc2_motion_speed = action.replace("npc2motion+0+speed+", "")
                template["npcList"][1]["motion"][0]["speed"] = float(npc2_motion_speed)
            if action.startswith("npc2+destination+lane_position+lane_569+"):
                npc2_dest_offset = action.replace("npc2+destination+lane_position+lane_569+", "")
                template["npcList"][1]["destination"]["lane_position"]["offset"] = float(npc2_dest_offset)
            if action.startswith("npc2+destination+speed+"):
                npc2_dest_speed = action.replace("npc2+destination+speed+", "")
                template["npcList"][1]["destination"]["speed"] = float(npc2_dest_speed)
            # NPC3
            if action.startswith("npc3+start+lane_position+lane_574+"):
                npc3_start_offset = action.replace("npc3+start+lane_position+lane_574+", "")
                template["npcList"][2]["start"]["lane_position"]["offset"] = float(npc3_start_offset)
            if action.startswith("npc3+start+speed+"):
                npc3_start_speed = action.replace("npc3+start+speed+", "")
                template["npcList"][2]["start"]["speed"] = float(npc3_start_speed)
            if action.startswith("npc3motion+0+lane_position+lane_569+"):
                npc3_motion_offset = action.replace("npc3motion+0+lane_position+lane_569+", "")
                template["npcList"][2]["motion"][0]["lane_position"]["offset"] = float(npc3_motion_offset)
            if action.startswith("npc3motion+0+speed+"):
                npc3_motion_speed = action.replace("npc3motion+0+speed+", "")
                template["npcList"][2]["motion"][0]["speed"] = float(npc3_motion_speed)
            if action.startswith("npc3+destination+lane_position+lane_569+"):
                npc3_dest_offset = action.replace("npc3+destination+lane_position+lane_569+", "")
                template["npcList"][2]["destination"]["lane_position"]["offset"] = float(npc3_dest_offset)
            if action.startswith("npc3+destination+speed+"):
                npc3_dest_speed = action.replace("npc3+destination+speed+", "")
                template["npcList"][2]["destination"]["speed"] = float(npc3_dest_speed)
            # NPC4
            if action.startswith("npc4+start+lane_position+lane_574+"):
                npc4_start_offset = action.replace("npc4+start+lane_position+lane_574+", "")
                template["npcList"][3]["start"]["lane_position"]["offset"] = float(npc4_start_offset)
            if action.startswith("npc4+start+speed+"):
                npc4_start_speed = action.replace("npc4+start+speed+", "")
                template["npcList"][3]["start"]["speed"] = float(npc4_start_speed)
            if action.startswith("npc4motion+0+lane_position+lane_569+"):
                npc4_motion_offset = action.replace("npc4motion+0+lane_position+lane_569+", "")
                template["npcList"][3]["motion"][0]["lane_position"]["offset"] = float(npc4_motion_offset)
            if action.startswith("npc4motion+0+speed+"):
                npc4_motion_speed = action.replace("npc4motion+0+speed+", "")
                template["npcList"][3]["motion"][0]["speed"] = float(npc4_motion_speed)
            if action.startswith("npc4+destination+lane_position+lane_569+"):
                npc4_dest_offset = action.replace("npc4+destination+lane_position+lane_569+", "")
                template["npcList"][3]["destination"]["lane_position"]["offset"] = float(npc4_dest_offset)
            if action.startswith("npc4+destination+speed+"):
                npc4_dest_speed = action.replace("npc4+destination+speed+", "")
                template["npcList"][3]["destination"]["speed"] = float(npc4_dest_speed)
            # NPC5
            if action.startswith("npc5+start+lane_position+lane_574+"):
                npc5_start_offset = action.replace("npc5+start+lane_position+lane_574+", "")
                template["npcList"][4]["start"]["lane_position"]["offset"] = float(npc5_start_offset)
            if action.startswith("npc5+start+speed+"):
                npc5_start_speed = action.replace("npc5+start+speed+", "")
                template["npcList"][4]["start"]["speed"] = float(npc5_start_speed)
            if action.startswith("npc5motion+0+lane_position+lane_569+"):
                npc5_motion_offset = action.replace("npc5motion+0+lane_position+lane_569+", "")
                template["npcList"][4]["motion"][0]["lane_position"]["offset"] = float(npc5_motion_offset)
            if action.startswith("npc5motion+0+speed+"):
                npc5_motion_speed = action.replace("npc5motion+0+speed+", "")
                template["npcList"][4]["motion"][0]["speed"] = float(npc5_motion_speed)
            if action.startswith("npc5+destination+lane_position+lane_569+"):
                npc5_dest_offset = action.replace("npc5+destination+lane_position+lane_569+", "")
                template["npcList"][4]["destination"]["lane_position"]["offset"] = float(npc5_dest_offset)
            if action.startswith("npc5+destination+speed+"):
                npc5_dest_speed = action.replace("npc5+destination+speed+", "")
                template["npcList"][4]["destination"]["speed"] = float(npc5_dest_speed)
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
    raw_data_path = '../../one_scenario/testset_for_' + session + '.json'
    action_dataset_path = '../../code/data/a_testset_for_' + session + '.json'
    action_space_path = '../../code/data/space_for_' + session + '.json'

    action_seqs = generate_actions(raw_data_path)
    action_space = generate_actions_space(raw_data_path)
    # For Debugging
    with open(action_dataset_path, 'w', encoding='utf-8') as f:
        json.dump(action_seqs, f, ensure_ascii=False, indent=4)
    with open(action_space_path, 'w', encoding='utf-8') as f:
        for key, value in action_space.items():
            action_space[key] = sorted(list(value))
        json.dump(action_space, f, ensure_ascii=False, indent=4)
    return action_seqs


def normalization_space(action_space):
    pass


if __name__ == '__main__':
    sessions = ['single_direction', 'double_direction', 'lane_change']
    for session in sessions:
        gen_dataset_from_rawdata(session)