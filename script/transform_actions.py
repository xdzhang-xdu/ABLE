import json
import os


def returnWeatherLevel(value):
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

def returnOffsetLevel(position):
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

def returnSpeedLevel(value):
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

def makeEnvActions(scenario, actionSeq):
    # Minute is not considered
    actionSeq.append('time+' + str(scenario['time']['hour']))
    actionSeq.append('weather+rain+' + returnWeatherLevel(scenario['weather']['rain']))
    actionSeq.append('weather+wetness+' + returnWeatherLevel(scenario['weather']['wetness']))
    actionSeq.append('weather+fog+' + returnWeatherLevel(scenario['weather']['fog']))

def makeEnvActionsSpace(scenario, actionSpace):
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

def makeEgoActions(scenario, actionSeq):
    pos = scenario['ego']['start']['lane_position']
    actionSeq.append('ego+start+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
    actionSeq.append('ego+start+speed+' + str(round(scenario['ego']['start']['speed'], 0)))
    pos = scenario['ego']['destination']['lane_position']
    actionSeq.append('ego+destination+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
    actionSeq.append('ego+destination+speed+' + str(round(scenario['ego']['destination']['speed'], 0)))


def makeEgoActionsSpace(scenario, actionSpace):
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

def makeNPCActions(scenario, actionSeq):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        pos = npc['start']['lane_position']
        actionSeq.append(npcid + '+start+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
        actionSeq.append(npcid + '+start+speed+' + str(round(npc['start']['speed'], 0)))
        for i, waypoint in enumerate(npc['motion']):
            pos = waypoint['lane_position']
            actionSeq.append(npcid + 'motion+' + str(i) + '+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
            actionSeq.append(npcid + 'motion+' + str(i) + '+speed+' + str(round(waypoint['speed'], 0)))
        pos = npc['destination']['lane_position']
        actionSeq.append(npcid + '+destination+lane_position+' + pos['lane'] + '+' + str(round(pos['offset'], 0)))
        actionSeq.append(npcid + '+destination+speed+' + str(round(npc['destination']['speed'], 0)))

def makeNPCActionsSpace(scenario, actionSpace):
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
            type_name = npcid + 'motion+' + str(i) + '+lane_position+' + waypoint['lane_position']['lane'] + '+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(round(waypoint['lane_position']['offset'], 0))
            type_name = npcid + 'motion+' + str(i) + '+speed+'
            if type_name not in actionSpace:
                actionSpace[type_name] = set()
            actionSpace[type_name].add(round(waypoint['speed'], 0))
        lp = npc['destination']['lane_position']
        type_name = npcid + '+destination+lane_position+' + lp['lane'] + '+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(round(lp['offset'],0))
        type_name = npcid + '+destination+speed+'
        if type_name not in actionSpace:
            actionSpace[type_name] = set()
        actionSpace[type_name].add(round(npc['destination']['speed'], 0))

def makePedestrainActions(scenario, actionSeq):
    pass

def makeObstacleActions(scenario, actionSeq):
    pass

def transform_actions(path):
    action_sequences = []
    with open(path) as f:
        data = json.load(f)
        for scenario in data:
            print('Handling ' + scenario['ScenarioName'])
            for_one_scenario = {'ScenarioName': scenario['ScenarioName']}
            actions = []
            makeEnvActions(scenario, actions)
            makeEgoActions(scenario, actions)
            makeNPCActions(scenario, actions)
            makePedestrainActions(scenario, actions)
            makeObstacleActions(scenario, actions)
            for_one_scenario['actions'] = actions
            for_one_scenario['robustness'] = scenario['robustness']
            action_sequences.append(for_one_scenario)
    return action_sequences

def transform_actions_space(path):
    action_space = {}
    with open(path) as f:
        data = json.load(f)
        for scenario in data:
            print('Handling ' + scenario['ScenarioName'])
            makeEnvActionsSpace(scenario, action_space)
            makeEgoActionsSpace(scenario, action_space)
            makeNPCActionsSpace(scenario, action_space)
            makePedestrainActions(scenario, action_space)
            makeObstacleActions(scenario, action_space)
    return action_space


def normalization_space(action_space):
    pass
if __name__ == '__main__':
    datapath = '/home/xdzhang/work/LawBreaker-SourceCode/engines/gflownet/one_scenario/testset_for_double_direction.json'
    dataspacepath = '/home/xdzhang/work/LawBreaker-SourceCode/engines/gflownet/one_scenario/space_for_double_direction.json'
    dataset = '/home/xdzhang/work/LawBreaker-SourceCode/engines/gflownet/code/data/a_testset_for_double_direction.json'
    action_space = transform_actions_space(datapath)

    action_seqs = transform_actions(datapath)
    with open(dataset, 'w', encoding='utf-8') as f:
        json.dump(action_seqs, f, ensure_ascii=False, indent=4)

    with open(dataspacepath, 'w', encoding='utf-8') as f:
        for key, value in action_space.items():
            action_space[key] = sorted(list(value))
        json.dump(action_space, f, ensure_ascii=False, indent=4)
    # for root, _, files in os.walk('C:/xdzhang/traffic_rule_dataset/one_scenario'):
    #     for file in files:
    #         if not (file.endswith('.json') and file.startswith('testset')):
    #             continue
    #         print('File ' + file)
    #         action_seqs = transform_actions(os.path.join(root, file))
    #         with open(os.path.join(root, 'a_' + file), 'w', encoding='utf-8') as f:
    #             json.dump(action_seqs, f, ensure_ascii=False, indent=4)
