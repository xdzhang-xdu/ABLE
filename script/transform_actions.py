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
    level = 0
    interval_num = 5
    scale = 1.0 / interval_num
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

def makeEgoActions(scenario, actionSeq):
    actionSeq.append('ego+start+lane_position+' + returnOffsetLevel(scenario['ego']['start']['lane_position']))
    actionSeq.append('ego+start+speed+' + returnSpeedLevel(scenario['ego']['start']['speed']))
    actionSeq.append('ego+destination+lane_position+' + returnOffsetLevel(scenario['ego']['destination']['lane_position']))
    actionSeq.append('ego+destination+speed+' + returnSpeedLevel(scenario['ego']['destination']['speed']))

def makeNPCActions(scenario, actionSeq):
    for npc in scenario['npcList']:
        npcid = npc['ID']
        actionSeq.append(npcid + '+start+lane_position+' + returnOffsetLevel(npc['start']['lane_position']))
        actionSeq.append(npcid + '+start+speed+' + returnSpeedLevel(npc['start']['speed']))
        for i, waypoint in enumerate(npc['motion']):
            actionSeq.append(npcid + 'motion+' + str(i) + '+lane_position+' + returnOffsetLevel(waypoint['lane_position']))
            actionSeq.append(npcid + 'motion+' + str(i) + '+speed+' + returnSpeedLevel(waypoint['speed']))
        actionSeq.append(npcid + '+destination+lane_position+' + returnOffsetLevel(npc['destination']['lane_position']))
        actionSeq.append(npcid + '+destination+speed+' + returnSpeedLevel(npc['destination']['speed']))

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

if __name__ == '__main__':
    for root, _, files in os.walk('C:/xdzhang/traffic_rule_dataset/one_scenario'):
        for file in files:
            if not (file.endswith('.json') and file.startswith('testset')):
                continue
            print('File ' + file)
            action_seqs = transform_actions(os.path.join(root, file))
            with open(os.path.join(root, 'a_' + file), 'w', encoding='utf-8') as f:
                json.dump(action_seqs, f, ensure_ascii=False, indent=4)
