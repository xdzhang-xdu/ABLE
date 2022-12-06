import copy
import math
import os
import random
import shutil
import sys
import time
import websockets
import json
import asyncio
from datetime import datetime
import logging

from testing_engines.gflownet.generator.proxy.proxy_config import proxy_args
from testing_engines.gflownet.generator.proxy.train_proxy import train_proxy
from testing_engines.gflownet.generator.generative_model.main import generate_samples_with_gfn
from testing_engines.gflownet.generator.pre_process.transform_actions import decode, encode
from testing_engines.gflownet.lib.monitor import Monitor
from testing_engines.gflownet.path_config import path_args
from testing_engines.gflownet.tools.remove_useless_action import remove_useless_action


async def test_one_scenario(scenario_json, specs, covered_specs, reward, directory=None) -> object:
    uri = "ws://localhost:8000"  # The Ip and port for our customized bridge.
    async with websockets.connect(uri, max_size=300000000, ping_interval=None) as websocket:
        # Initialize files
        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
        await websocket.send(init_msg)
        while True:
            msg = await websocket.recv()
            msg = json.loads(msg)
            # print(msg['TYPE'])
            if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                if msg['DATA']:
                    logging.info('Running Scenario: {}'.format(scenario_json["ScenarioName"]))
                    send_command_msg = {'CMD': "CMD_NEW_TEST", 'DATA': scenario_json}
                    await websocket.send(json.dumps(send_command_msg))
                else:
                    time.sleep(3)
                    init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                    await websocket.send(init_msg)
            elif msg['TYPE'] == 'KEEP_SERVER_AND_CLIENT_ALIVE':
                send_msg = {'CMD': "KEEP_SERVER_AND_CLIENT_ALIVE", 'DATA': None}
                await websocket.send(json.dumps(send_msg))
            elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                print("Try to reconnect.")
                time.sleep(3)
                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                await websocket.send(init_msg)
            elif msg['TYPE'] == 'TEST_COMPLETED':
                output_trace = msg['DATA']
                dt_string = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                file = directory + '/data/result' + dt_string + '.json'
                with open(file, 'w') as outfile:
                    json.dump(output_trace, outfile, indent=2)
                logging.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                if not output_trace['destinationReached']:
                    with open(directory + '/Incompleted.txt', 'a') as f:
                        json.dump(scenario_json, f, indent=2)
                        f.write('\n')
                if len(output_trace['trace']) > 1:
                    if 'Accident!' in output_trace["testFailures"]:
                        with open(directory + '/AccidentTestCase.txt', 'a') as bug_file:
                            now = datetime.now()
                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                            string_index = "Time:" + dt_string + ", Scenario: " + scenario_json["ScenarioName"] + \
                                           ", Bug: " + str(output_trace["testFailures"]) + '\n'
                            bug_file.write(string_index)
                            json.dump(output_trace, bug_file, indent=2)
                            bug_file.write('\n')
                    monitor = Monitor(output_trace, 0)
                    for spec in specs:
                        if spec in covered_specs:
                            continue
                        robustness = monitor.continuous_monitor2(spec)
                        if robustness < 0.0:
                            continue
                        covered_specs.append(spec)
                        with open(directory + '/violationTestCase.txt', 'a') as violation_file:
                            now = datetime.now()
                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                            string_index = "Time:" + dt_string + ". Scenario: " + scenario_json["ScenarioName"] + '\n'
                            violation_file.write(string_index)
                            string_index2 = "The detailed fitness values:" + str(robustness) + '\n'
                            violation_file.write(string_index2)
                            # bug_file.write(spec)
                            json.dump(output_trace, violation_file, indent=2)
                            violation_file.write('\n')

                elif len(output_trace['trace']) == 1:
                    logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                        output_trace['destinationReached'], output_trace['minEgoObsDist']))
                else:
                    logging.info("No trace for the test cases!")
                    with open(directory + '/NoTrace.txt', 'a') as f:
                        now = datetime.now()
                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        f.write("Time: {}, Scenario: {}".format(dt_string, scenario_json["ScenarioName"]))
                        json.dump(scenario_json, f, indent=2)
                        f.write('\n')
                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                await websocket.send(init_msg)
                break
            else:
                print("Incorrect response.")
                break


async def law_complying_degree(scenario_json, spec, directory=None) -> object:
    uri = "ws://localhost:8000"  # The Ip and port for our customized bridge.
    async with websockets.connect(uri, max_size=300000000, ping_interval=None) as websocket:
        # Initialize files
        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
        await websocket.send(init_msg)
        while True:
            msg = await websocket.recv()
            msg = json.loads(msg)
            # print(msg['TYPE'])
            if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                if msg['DATA']:
                    logging.info('Running Scenario: {}'.format(scenario_json["ScenarioName"]))
                    send_command_msg = {'CMD': "CMD_NEW_TEST", 'DATA': scenario_json}
                    await websocket.send(json.dumps(send_command_msg))
                else:
                    time.sleep(3)
                    init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                    await websocket.send(init_msg)
            elif msg['TYPE'] == 'KEEP_SERVER_AND_CLIENT_ALIVE':
                send_msg = {'CMD': "KEEP_SERVER_AND_CLIENT_ALIVE", 'DATA': None}
                await websocket.send(json.dumps(send_msg))
            elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                print("Try to reconnect.")
                time.sleep(3)
                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                await websocket.send(init_msg)
            elif msg['TYPE'] == 'TEST_COMPLETED':
                output_trace = msg['DATA']
                dt_string = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                file = directory + '/data/result' + dt_string + '.json'
                with open(file, 'w') as outfile:
                    json.dump(output_trace, outfile, indent=2)
                logging.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                if not output_trace['destinationReached']:
                    with open(directory + '/Incompleted.txt', 'a') as f:
                        json.dump(scenario_json, f, indent=2)
                        f.write('\n')
                if len(output_trace['trace']) > 1:
                    if 'Accident!' in output_trace["testFailures"]:
                        with open(directory + '/AccidentTestCase.txt', 'a') as bug_file:
                            now = datetime.now()
                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                            string_index = "Time:" + dt_string + ", Scenario: " + scenario_json["ScenarioName"] + \
                                           ", Bug: " + str(output_trace["testFailures"]) + '\n'
                            bug_file.write(string_index)
                            json.dump(output_trace, bug_file, indent=2)
                            bug_file.write('\n')
                    monitor = Monitor(output_trace, 0)
                    robustness = monitor.continuous_monitor2(spec)
                    return True, -robustness
                elif len(output_trace['trace']) == 1:
                    logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                        output_trace['destinationReached'], output_trace['minEgoObsDist']))
                else:
                    logging.info("No trace for the test cases!")
                    with open(directory + '/NoTrace.txt', 'a') as f:
                        now = datetime.now()
                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        f.write("Time: {}, Scenario: {}".format(dt_string, scenario_json["ScenarioName"]))
                        json.dump(scenario_json, f, indent=2)
                        f.write('\n')
                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                await websocket.send(init_msg)
                break
            else:
                print("Incorrect response.")
                break
        return False, 0.0


async def restart_module(module) -> object:
    uri = "ws://localhost:8000"  # The Ip and port for our customized bridge.
    async with websockets.connect(uri, max_size=300000000, ping_interval=None) as websocket:
        msg = json.dumps({'CMD': 'RESTART_MODULE', 'Module': module})
        await websocket.send(msg)
        print('sent ', msg)
        while True:
            msg = await websocket.recv()
            print('recieved ', msg)
            msg = json.loads(msg)
            if msg['TYPE'] == 'RESTART_MODULE_FINISHED':
                send_msg = {'CMD': "KEEP_SERVER_AND_CLIENT_ALIVE", 'DATA': None}
                await websocket.send(json.dumps(send_msg))
            elif msg['TYPE'] == 'KEEP_SERVER_AND_CLIENT_ALIVE':
                break
            else:
                assert 0, 'Wrong respond.'


def get_history_scenarios(session):
    with open(path_args.train_data_path.format(session)) as file:
        dataset = json.load(file)
    return dataset


def generate_scenarios_batch(dataset, session):
    # Train model to generate new scenarios to files
    while True:
        train_proxy(proxy_args, dataset, session)
        new_batch = generate_samples_with_gfn(dataset, session)
        if len(new_batch) != 1:
            break
    # For debug
    with open(path_args.new_batch_path.format(session), 'w', encoding='utf-8') as file:
        json.dump(new_batch, file, indent=4)
    #
    test_cases_batch = []
    for item in new_batch:
        test_cases_batch.append(decode(item, session))
    return test_cases_batch


def debug_new_batch(session):
    with open(path_args.new_batch_path.format(session)) as file:
        dataset = json.load(file)
    #
    test_cases_batch = []
    for item in dataset:
        test_cases_batch.append(decode(item, session))
    return test_cases_batch


"""
For debugging single scenario
"""


def load_violation_testcases(spec, session):
    validate_test_path = "validate/{}_new_covered.json".format(session)
    with open(validate_test_path) as file:
        json_obj = json.load(file)
        return json_obj[spec]


def load_specifications():
    with open(path_args.spec_path) as file:
        specs = json.load(file)
    del specs["all_rules"]
    table = dict()
    for idx, spec in enumerate(specs.values()):
        table[spec] = idx + 1
    return list(specs.values()), table


def load_target_specs():
    return ['eventually(((direction==1)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))',
            'eventually((direction==1)and(not(speed<=30)))',
            'eventually(((direction==2)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))',
            'eventually(((isLaneChanging==1)and(currentLanenumber>=2))and(PriorityNPCAhead==1))',
            'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(always[0,3](not(speed>0.5))))',
            'eventually(((trafficLightAheadcolor==3)and((eventually[0,2](NPCAheadspeed>0.5))and(NPCAheadAhead<=8.0)))and(NPCAheadAhead<=0.5))']


def test_scenario_batch(testcases, remained_specs, file_directory):
    covered_specs = list()
    for item in testcases[:]:
        reward = [-100000.0] * 82
        loop = asyncio.get_event_loop()
        # loop.run_until_complete(
        #     asyncio.gather(asyncio.gather(
        #         test_one_scenario(item, remained_specs, covered_specs, reward, directory=file_directory))))
        # Restart modules
        modules = [
            'Localization',
            'Transform',
            'Routing',
            'Prediction',
            'Planning',
            'Camera',
            'Traffic Light',
            'Control'
        ]
        loop.run_until_complete(asyncio.gather(asyncio.gather(restart_module(modules[4]))))
    return covered_specs


def invoke_tester(testcase, specs, file_directory):
    covered_specs = list()
    reward = [-100000.0] * 82
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_one_scenario(testcase, specs, covered_specs, reward, directory=file_directory))
    return covered_specs


def debug_session(session, testcases, remained_specs):
    log_direct = path_args.debug_result_direct.format(session)
    # Set testing result or data paths
    if not os.path.exists(log_direct):
        os.makedirs(log_direct)
    # else:
    #     shutil.rmtree(log_direct)
    if not os.path.exists(log_direct + '/data'):
        os.makedirs(log_direct + '/data')
    # Set logger
    logging_file = log_direct + '/test.log'
    file_handler = logging.FileHandler(logging_file, mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.INFO, handlers=[stdout_handler, file_handler],
                        format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logging.info("Current Session: {}".format(session))

    for _ in range(100):
        covered_specs = test_scenario_batch(testcases, remained_specs, log_direct)
        if len(covered_specs) != 0:
            print("Repay is successful.")
            break
        else:
            print("Continue....")


def run_bug_scenario(testcase, specs):
    # Set testing result or data paths
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    # else:
    #     shutil.rmtree(log_direct)
    if not os.path.exists(log_directory + '/data'):
        os.makedirs(log_directory + '/data')
    # Set logger
    logging_file = log_directory + '/test.log'
    file_handler = logging.FileHandler(logging_file, mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.INFO, handlers=[stdout_handler, file_handler],
                        format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    covered_specs = set()
    for _ in range(5):
        covered_specs_one = invoke_tester(testcase, specs, log_directory)
        covered_specs = covered_specs | set(covered_specs_one)
    return list(covered_specs)


def load_bug_scenarios():
    bug_scenarios = dict()
    data_path = "/home/xdzhang/ABLE/test_cases/buggy_scenarios"
    for root, _, data_files in os.walk(data_path):
        for data_file in data_files:
            if not data_file.endswith('.json'):
                continue
            with open(os.path.join(root, data_file)) as f:
                print('Processing ', os.path.join(root, data_file))
                data = json.load(f)
                if "groundTruthPerception" in data:
                    data.pop("groundTruthPerception")
                if "testFailures" in data:
                    data.pop("testFailures")
                if "testResult" in data:
                    data.pop("testResult")
                if "minEgoObsDist" in data:
                    data.pop("minEgoObsDist")
                if "destinationReached" in data:
                    data.pop("destinationReached")
                if "trace" in data:
                    data.pop("trace")
                bug_scenarios[os.path.join(root, data_file)] = data
    return bug_scenarios


def analyze_bugs():
    bug_scenarios = load_bug_scenarios()
    all_specs, _ = load_specifications()
    bug_data = dict()
    for scenario_path, scenario_json in bug_scenarios.items():
        covered_specs = run_bug_scenario(scenario_json, all_specs)
        bug_data[scenario_path] = covered_specs

    bug_data_path = "fix_data/path_specs.json"
    with open(bug_data_path, 'w') as fp:
        json.dump(bug_data, fp)


def get_original_parameters():
    para_path = "/home/xdzhang/ABLE/testing_engines/gflownet/fix_data/original_parameters.json"
    with open(para_path, "r") as f:
        data = json.load(f)
    return data


def get_breaking_scenarios():
    break_path = "/home/xdzhang/ABLE/testing_engines/gflownet/fix_data/breaking_scenarios.json"
    with open(break_path, "r") as f:
        data = json.load(f)
    return data


def get_passed_scenarios():
    return dict()


def apply_change_to_ads(configuration):
    configuration_path = "/home/xdzhang/apollo/modules/prediction/conf/prediction.conf"
    with open(configuration_path, "r") as f:
        configs = f.readlines()
        tmp_configs = configs[:len(configs)-len(configuration)]
        for para, value in configuration.items():
            tmp_configs.append("--{}={}\n".format(para, value))
        new_config = "".join(tmp_configs)
    with open(configuration_path, "w") as f:
        f.write(new_config)


def is_harmless_and_relevant(passed_scenarios, breaking_scenarios):
    print("Checking passed scenarios...")
    for scenario_path, spec in passed_scenarios.items():
        with open(scenario_path, "r") as f:
            scenario_json = json.load(f)
        loop = asyncio.get_event_loop()
        flag, degree = loop.run_until_complete(law_complying_degree(scenario_json, spec, directory=log_directory))
        if flag is True and degree < 0.0:
            return False

    print("Checking breaking scenarios...")
    at_least_one = False
    for scenario_path, spec in breaking_scenarios.items():
        with open(scenario_path, "r") as f:
            scenario_json = json.load(f)
        loop = asyncio.get_event_loop()
        flag, degree = loop.run_until_complete(law_complying_degree(scenario_json, spec, directory=log_directory))
        print("current change brings law complying degree: {}".format(degree))
        if flag is True and degree >= 0.0:
            at_least_one = True
            break
    return at_least_one


def cause_analysis(original_parameters, passed_scenarios, breaking_scenarios):
    relevant_parameters = []
    for para, value in original_parameters.items():
        changed_value = value * 1.5
        changed_configuration = copy.deepcopy(original_parameters)
        changed_configuration[para] = changed_value
        apply_change_to_ads(changed_configuration)
        print("### Verifying Parameter \"{}\" {} -> {}".format(para, value, changed_value))
        if is_harmless_and_relevant(passed_scenarios, breaking_scenarios):
            relevant_parameters.append((para, value))
    return relevant_parameters


def mutate(relevant_parameters):
    ops = [1, 0.95, 1.05, 0.9, 1.1]
    new_individual = []
    for item in relevant_parameters:
        index = random.randint(0, len(ops) - 1)
        new_individual.append((item[0], item[1]*ops[index]))
    return new_individual


def euclidean_distance(original_parameters, changed_parameters):
    sum_dist = 0.0
    for para, value in changed_parameters:
        sum_dist = sum_dist + math.pow((value - original_parameters[para])/value, 2)
    return math.sqrt(sum_dist)


def compute_fitness(original_parameters, generation, breaking_scenarios):
    tmp_generation = copy.deepcopy(generation)
    generation.clear()
    for individual in tmp_generation:
        configuration = copy.deepcopy(original_parameters)
        for para, value in individual[0]:
            configuration[para] = value
        apply_change_to_ads(configuration)
        degree = 0.0
        for scenario_path, spec in breaking_scenarios.items():
            with open(scenario_path, "r") as f:
                scenario_json = json.load(f)
            loop = asyncio.get_event_loop()
            degree = degree + loop.run_until_complete(law_complying_degree(scenario_json, spec, directory=log_directory))
            # degree = degree + random.random()
        distance = euclidean_distance(original_parameters, individual[0])
        fitness = degree / math.exp(distance)
        print(individual, "-- distance {}, fitness {}".format(distance, fitness))
        generation.append((individual[0], fitness))


def misconfiguration_fix(original_parameters, relevant_parameters, breaking_scenarios):
    # initialization
    generation = []
    for p in range(num_population):
        new_individual = mutate(relevant_parameters)
        generation.append((new_individual, 0.0))

    for g in range(num_generation):
        # compute fitness
        compute_fitness(original_parameters, generation, breaking_scenarios)
        # selection
        sorted_generation = sorted(generation, key=lambda x: x[1])
        generation = sorted_generation[num_population//2:]
        if g == num_generation - 1:
            break
        # crossover and mutation
        for i in range(num_population//2):
            new_individual = mutate(generation[i][0])
            generation.append((new_individual, 0.0))
        random.shuffle(generation)
        for i in range(num_population//2):
            a = generation[i][0]
            b = generation[i + num_population//2][0]
            c = a[:len(a)//2] + b[len(b)//2:]
            d = b[:len(b)//2] + a[len(a)//2:]
            generation[i] = (c, 0.0)
            generation[i + num_population // 2] = (d, 0.0)
    print(generation)


def fix_bugs():
    breaking_scenarios = get_breaking_scenarios()
    passed_scenarios = get_passed_scenarios()
    original_parameters = get_original_parameters()
    print("Root cause analysis....")
    relevant_parameters = cause_analysis(original_parameters, passed_scenarios, breaking_scenarios)
    # relevant_parameters = [('still_obstacle_speed_threshold', 0.99), ('still_pedestrian_speed_threshold', 0.2)]
    print("Misconfiguration fixing....")
    misconfiguration_fix(original_parameters, relevant_parameters, breaking_scenarios)


"""
" specs formula -> the index in the json file
"""
specs_to_index = dict()
specs_weight = [1] * 81


num_population = 20
num_generation = 20
log_directory = "/home/xdzhang/test_data"

if __name__ == "__main__":
    analyze_bugs()
    # fix_bugs()
    exit(98)

    start = datetime.now()
    sessions = ['double_direction', 'single_direction', 'lane_change', 't_junction']
    # sessions = ['lane_change']
    session = 'lane_change'
    target_spec = 'eventually(((direction==1)and(PriorityNPCAhead==1))and(always[0,2](not(speed<0.5))))'
    new_testcases = load_violation_testcases(target_spec, session)
    # print(len(new_testcases), new_testcases)
    debug_session(session, new_testcases, [target_spec])
