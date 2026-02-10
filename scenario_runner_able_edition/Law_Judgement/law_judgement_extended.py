import os
import sys
import json
import copy
import numpy as np
import rtamt

from TracePreprocess import Trace

class Monitor:
    def __init__(self, returned_msg):
        self.original_data = copy.deepcopy(returned_msg['trace'])
        self.data = dict()
        self.c_data = dict()
        self.weather_raw = returned_msg["weather"]
        self.time_raw = returned_msg["time"]

        self.item_names_of_variable_of_APIS = []
        self.muti_traffic_rules = dict()

        self.preprocessed_data = Trace(returned_msg)
        self.prepare_for_rules()

        self.violations = None
        self.prepare_violations()

    def prepare_traffic_rule_related_APIs(self, _time ,state_len , _var_data, name_of_vaiable):
        self.c_data[name_of_vaiable] = [[_time[i], _var_data[i]] for i in range(state_len)]
        self.data[name_of_vaiable] = _var_data

    def prepare_for_rules(self):
        state_len = len(self.original_data)
        _time = self.preprocessed_data.trace['time']
        self.c_data['time'] = [[i, _time[i]] for i in range(state_len)]

        self.data['time'] = [i for i in range(state_len)]
        self.data['t'] = self.preprocessed_data.trace['time']
        TRACE = self.preprocessed_data.trace

        for key in TRACE["ego-forTrafficRule"]:
            name_of_vaiable = str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["ego-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["ego-driving-forTrafficRule"]:
            name_of_vaiable = str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["ego-driving-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)
        
        for key in TRACE["currentlane-forTrafficRule"]:
            name_of_vaiable = 'currentLane' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["currentlane-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["speedLimit-forTrafficRule"]:
            name_of_vaiable = 'speedLimit' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["speedLimit-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["road-forTrafficRule"]:
            name_of_vaiable = str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len ,  TRACE["road-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["specialLocationAhead-forTrafficRule"]:
            name_of_vaiable = 'specialLocationAhead' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["specialLocationAhead-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["trafficLightAhead-forTrafficRule"]:
            name_of_vaiable = 'trafficLightAhead' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["trafficLightAhead-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)


        for key in TRACE["traffic-forTrafficRule"]:
            name_of_vaiable = str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["traffic-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["NPCAhead-forTrafficRule"]:
            name_of_vaiable = 'NPCAhead' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["NPCAhead-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["NearestNPC-forTrafficRule"]:
            name_of_vaiable = 'NearestNPC' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["NearestNPC-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["NPCOpposite-forTrafficRule"]:
            name_of_vaiable = 'NPCOpposite' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["NPCOpposite-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in self.weather_raw:
            name_of_vaiable = str(key)
            data = [self.weather_raw[key]] * state_len
            self.prepare_traffic_rule_related_APIs( _time ,state_len , data, name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        for key in TRACE["trafficLightAhead-arrow-direction-forTrafficRule"]:
            name_of_vaiable = 'trafficLightAheadArrowDirection' + str(key)
            self.prepare_traffic_rule_related_APIs( _time ,state_len , TRACE["trafficLightAhead-arrow-direction-forTrafficRule"][key], name_of_vaiable)
            self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        name_of_vaiable = 'snow'
        data = [0] * state_len
        self.prepare_traffic_rule_related_APIs( _time ,state_len , data, name_of_vaiable)
        self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        name_of_vaiable = 'visibility'
        data = [100] * state_len
        self.prepare_traffic_rule_related_APIs( _time ,state_len , data, name_of_vaiable)
        self.item_names_of_variable_of_APIS.append(name_of_vaiable)


        name_of_vaiable = 'Time'
        data = [int(self.time_raw['hour']) + int(self.time_raw['minute'])/60 ] * state_len
        self.prepare_traffic_rule_related_APIs( _time ,state_len , data, name_of_vaiable)
        self.item_names_of_variable_of_APIS.append(name_of_vaiable)

        self.muti_traffic_rules["rule38"] = '( \
            always(((trafficLightAheadcolor == 3) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)) implies ( speed >= 0.5 ))   and \
                always((((trafficLightAheadcolor == 2) and ((stoplineAhead == 0) or (stoplineAhead > 50))) implies ( speed > 0.5 )) and \
                        (((trafficLightAheadcolor == 2) and (stoplineAhead <= 2)) implies (speed < 0.5)) ) and \
                always((((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction <= 1)) implies ( speed < 0.5 )) and \
                        (((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction == 2) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0) ) implies ( speed >= 0.5 )) ) \
        )'
        #GREEN = 3;
        self.muti_traffic_rules["rule38_1"] = '( \
            always(((trafficLightAheadcolor == 3) and \
                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)) \
                implies ( eventually[0,2](speed > 0.5)))\
        )'
        self.muti_traffic_rules["rule38_1_1"] = '( \
            ((trafficLightAheadcolor == 3) and \
            ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
            (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0))\
        )'
        self.muti_traffic_rules["rule38_1_2"] = '( \
            eventually[0,2](speed > 0.5) \
        )'
        #YELLOW = 2;
        self.muti_traffic_rules["rule38_2"] = '( \
            always(( ((trafficLightAheadcolor == 2) and \
                ((stoplineAhead == 0) or (currentLanenumber == 0))) \
                implies ( eventually[0,2](speed > 0.5) )) and \
                (((trafficLightAheadcolor == 2) and\
                (stoplineAhead >= 0.5) and\
                (stoplineAhead <= 3.5) and\
                (currentLanenumber > 0)) \
                implies ( eventually[0,3](speed < 0.5)))) \
        )'
        self.muti_traffic_rules["rule38_2_1"] = '( \
            ( (trafficLightAheadcolor == 2) and \
                ((stoplineAhead == 0) or (currentLanenumber == 0)) ) \
                implies (eventually[0,2](speed > 0.5)) \
        )'
        self.muti_traffic_rules["rule38_2_2"] = '( \
            ( (trafficLightAheadcolor == 2) and\
                (stoplineAhead >= 0.5) and\
                (stoplineAhead <= 3.5) and\
                (currentLanenumber > 0) ) \
                implies (eventually[0,3](speed < 0.5)) \
        )'
        #RED = 1;
        self.muti_traffic_rules["rule38_3"] = '( \
            always((((trafficLightAheadcolor == 1) and \
                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and\
                (currentLanenumber > 0) and \
                (direction <= 1)) \
                implies ( eventually[0,3](speed < 0.5) )) and \
                (((trafficLightAheadcolor == 1) and \
                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                (direction == 2) and (PriorityNPCAhead == 0) and \
                (currentLanenumber > 0) and \
                (PriorityPedsAhead == 0)) \
                implies ( eventually[0,2](speed > 0.5)))) \
        )'
        self.muti_traffic_rules["rule38_3_1"] = '( \
            always((((trafficLightAheadcolor == 1) and \
                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and\
                (currentLanenumber > 0) and \
                (direction <= 1)) \
                implies (eventually[0,3](speed < 0.5))))\
        )'
        self.muti_traffic_rules["rule38_3_2"] = '( \
            always((((trafficLightAheadcolor == 1) and \
                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                (direction == 2) and (PriorityNPCAhead == 0) and \
                (currentLanenumber > 0) and \
                (PriorityPedsAhead == 0) ) \
                implies ( eventually[0,2](speed > 0.5) ))) \
        )'

        #for the blink yellow light
        self.muti_traffic_rules["rule42"] = '( \
            always(((trafficLightAheadcolor == 2) and \
                (trafficLightAheadblink == 1) and \
                ((stoplineAhead <= 1) or (junctionAhead <= 1)))\
                implies (speed < 5))\
        )'

        #for the lane change and speed limit
        self.muti_traffic_rules["rule44"] = '( \
            always((currentLanenumber >= 2) implies ((speed >= speedLimitlowerLimit) and (speed <= speedLimitupperLimit))) and \
            always(((isLaneChanging == 1) and (currentLanenumber >= 2)) implies  (PriorityNPCAhead == 0 ))\
        )'
        self.muti_traffic_rules["rule44_1"] = '(currentLanenumber >= 2)'
        self.muti_traffic_rules["rule44_2"] = '( \
            (speed >= speedLimitlowerLimit) and (speed <= speedLimitupperLimit) \
        )'
        self.muti_traffic_rules["rule44_3"] = '( \
            (isLaneChanging == 1) and (currentLanenumber >= 2) \
        )'
        self.muti_traffic_rules["rule44_4"] = '( \
            always((currentLanenumber >= 2) implies ((speed >= speedLimitlowerLimit) and (speed <= speedLimitupperLimit))) \
        )'
        self.muti_traffic_rules["rule44_5"] = '( \
            always(((isLaneChanging == 1) and (currentLanenumber >= 2)) implies (PriorityNPCAhead == 0)) \
        )'

        #for pure speed limit
        self.muti_traffic_rules["rule45"] = '(always((speed >= speedLimitlowerLimit) and (speed <= speedLimitupperLimit)))'

        self.muti_traffic_rules["rule46"] = '(\
            always(((direction == 1) or (direction == 2) or (isTurningAround == 1)) implies (speed <= 30)) and\
            always(((rain >= 0.5) or (fog >= 0.5) or (snow >= 0.5)) implies (speed <= 30))\
        )'
        self.muti_traffic_rules["rule46_2"] = '(\
            always(((direction == 1) or (direction == 2) or (isTurningAround == 1)) implies (speed <= 30))\
        )'
        self.muti_traffic_rules["rule46_3"] = '(\
            always(((rain >= 0.5) or (fog >= 0.5) or (snow >= 0.5)) implies (speed <= 30))\
        )'

        self.muti_traffic_rules["rule47"] = '(\
            always((isOverTaking == 1)\
                implies ( (turnSignal == 1) and \
                    ((eventually[-1, 2](hornOn == 1)) or \
                        ( \
                        ((highBeamOn == 1 ) and \
                            ((highBeamOn == 1) implies (eventually[0, 2](lowBeamOn == 1))) ) or \
                        ((lowBeamOn == 1 ) and \
                            ((lowBeamOn == 1) implies (eventually[0, 2](highBeamOn == 1))) ) \
                        )\
                    ) and \
                    F[0, 10]( (turnSignal == 2) and \
                        (((isLaneChanging == 1) implies (NearestNPCAhead >= 5)) and (isLaneChanging == 1) ) ) ))\
        )'
        self.muti_traffic_rules["rule47_1"] = '(\
            (turnSignal == 1) and \
                ((eventually[-1, 2](hornOn == 1)) or \
                    ( \
                    ((highBeamOn == 1 ) and \
                        ((highBeamOn == 1) implies (eventually[0, 2](lowBeamOn == 1))) ) or \
                    ((lowBeamOn == 1 ) and \
                        ((lowBeamOn == 1) implies (eventually[0, 2](highBeamOn == 1))) ) \
                    )\
                ) and \
                F[0, 10]( (turnSignal == 2) and \
                    (((isLaneChanging == 1) implies (NearestNPCAhead >= 5)) and (isLaneChanging == 1) ) )\
        )'

        self.muti_traffic_rules["rule50"] = '(always((not (gear==2))))'

        self.muti_traffic_rules["rule51_3"] = "(always ((((((((trafficLightAheadcolor==3) and (direction==1)) and (Time<=20.0)) and (Time>=7.0))) -> ((turnSignal==1))) and (((((trafficLightAheadcolor==3) and (direction==1)) and (((Time>=20.0) or (Time<=7.0))))) -> (((turnSignal==1) and (lowBeamOn==1)))))))"
        self.muti_traffic_rules["rule51_3_1"] = "((((((trafficLightAheadcolor==3) and (direction==1)) and (Time<=20.0)) and (Time>=7.0))) -> ((turnSignal==1)))"
        self.muti_traffic_rules["rule51_3_2"] = "(((((trafficLightAheadcolor==3) and (direction==1)) and (((Time>=20.0) or (Time<=7.0))))) -> (((turnSignal==1) and (lowBeamOn==1))))"
        self.muti_traffic_rules["rule51_4"] = "(always ((((trafficLightAheadcolor==3) and (((not (NPCAheadAhead<=8.0)) or (((((NPCAheadAhead<=8.0) -> (eventually[0,2] ((NPCAheadspeed>0.5))))) and (NPCAheadAhead<=8.0)))))) -> (((eventually[0,3] ((speed>0.5)))) and (not (NPCAheadAhead<=0.5))))))"
        self.muti_traffic_rules["rule51_4_1"] = "((trafficLightAheadcolor==3) and (((not (NPCAheadAhead<=8.0)) or (((((NPCAheadAhead<=8.0) -> (eventually[0,2] ((NPCAheadspeed>0.5))))) and (NPCAheadAhead<=8.0))))))"
        self.muti_traffic_rules["rule51_4_2"] = "((eventually[0,3] (speed>0.5)) and (not (NPCAheadAhead<=0.5)))"
        self.muti_traffic_rules["rule51_5"] = "(always ((((trafficLightAheadcolor==1) and ((((stoplineAhead<=2.0) or (junctionAhead<=2.0)) or (NPCAheadAhead<=0.5)))) -> (eventually[0,2] ((speed < 0.5))))))"
        self.muti_traffic_rules["rule51_5_1"] = "((trafficLightAheadcolor==1) and ((((stoplineAhead<=2.0) or (junctionAhead<=2.0)) or (NPCAheadAhead<=0.5))))"
        self.muti_traffic_rules["rule51_5_2"] = "(eventually[0,2] ((speed < 0.5)))"
        self.muti_traffic_rules["rule51_6"] = "(always ((((((direction==2) and (NPCAheadAhead<=2.0)) and ((eventually[0,2] ((NPCAheadspeed<0.5)))))) -> (eventually[0,3] ((speed<0.5))))))"
        self.muti_traffic_rules["rule51_7"] = "(always (((((((direction==2) or (direction==1))) and (((PriorityNPCAhead==1) or (PriorityPedsAhead==1))))) -> (eventually[0,2] ((speed<0.5))))))"

        self.muti_traffic_rules["rule52"] = "(always (((((signalAhead==0 and ((PriorityNPCAhead==1 or PriorityPedsAhead==1))) and junctionAhead<=1.0)) -> (eventually[0,2] (speed<0.5)))))"

        self.muti_traffic_rules["rule53"] = "(always ((((isTrafficJam==1 and (((NPCAheadspeed<0.5 or NPCAheadAhead<=0.5) or junctionAhead<=1.0)))) -> (eventually[0,2] (speed<0.5)))))"

        self.muti_traffic_rules["rule57"] = "((always ((direction==1 -> turnSignal==1))) and (always ((direction==2 -> turnSignal==2))))"
        self.muti_traffic_rules["rule57_1"] = "(always (direction==1 -> turnSignal==1))"
        self.muti_traffic_rules["rule57_2"] = "(always (direction==2 -> turnSignal==2))"

        self.muti_traffic_rules["rule58"] = "(always ((((((((((not streetLightOn==1) and ((Time>=20.0 or Time<=7.0)))) or (((rain>=0.5 or fog>=0.5) or snow>=0.5))) and (not NPCAheadAhead<=10.0))) -> highBeamOn==1) and (NPCAheadAhead<=10.0 -> (not highBeamOn==1))) and (fog>=0.5 -> ((fogLightOn==1 and warningflashOn==1))))))"
        self.muti_traffic_rules["rule58_1"] = "(((( ( ((not streetLightOn==1) and (Time>=20.0 or Time<=7.0)) or ((rain>=0.5 or fog>=0.5) or snow>=0.5) ) and (not NPCAheadAhead<=10.0))) -> highBeamOn==1))"
        self.muti_traffic_rules["rule58_1_1"] = "( ((not streetLightOn==1) and (Time>=20.0 or Time<=7.0)) or ((rain>=0.5 or fog>=0.5) or snow>=0.5) )"
        self.muti_traffic_rules["rule58_2"] = "(NPCAheadAhead<=10.0 -> (not highBeamOn==1))"
        self.muti_traffic_rules["rule58_3"] = "(fog>=0.5 -> (fogLightOn==1 and warningflashOn==1))"

        self.muti_traffic_rules["rule59"] = "(always (((((crosswalkAhead<=5.0 or ((signalAhead==0 and junctionAhead<=1.0)))) and ((Time>=20.0 or Time<=7.0))) -> ((eventually[0,3] ((highBeamOn==1 and ((highBeamOn==1 -> (eventually[0,3] (lowBeamOn==1))))))) or (eventually[0,3] ((lowBeamOn==1 and ((lowBeamOn==1 -> (eventually[0,3] (highBeamOn==1)))))))))))"
        self.muti_traffic_rules["rule59_1"] = "( (crosswalkAhead<=5.0 or (signalAhead==0 and junctionAhead<=1.0)) and (Time>=20.0 or Time<=7.0) )"
        self.muti_traffic_rules["rule59_2"] = "(((eventually[0,3] ((highBeamOn==1 and ((highBeamOn==1 -> (eventually[0,3] (lowBeamOn==1))))))) or (eventually[0,3] ((lowBeamOn==1 and ((lowBeamOn==1 -> (eventually[0,3] (highBeamOn==1)))))))))"

        self.muti_traffic_rules["rule62"] = "(always (((not honkingAllowed==1) -> (not hornOn==1))))"

    def prepare_violations(self):
        with open("violation_formulae.json", "r") as file_formulae:
            violations = json.load(file_formulae)
            #del violations["all_rules"]
            self.violations = violations

    def continuous_monitor_for_muti_traffic_rules(self):
        result = dict()
        for key in self.muti_traffic_rules:
            spec = rtamt.StlDenseTimeSpecification(semantics=rtamt.Semantics.STANDARD)
            for item in self.item_names_of_variable_of_APIS:
                spec.declare_var(item, 'float')
            spec.spec = self.muti_traffic_rules[key]
            # print(key, self.muti_traffic_rules[key])
            try:
                spec.parse()
                # spec.pastify()
            except rtamt.STLParseException as err:
                print('STL Parse Exception: {}'.format(err))
                sys.exit()
            _data = [[var, self.c_data[var]] for var in self.item_names_of_variable_of_APIS]
            rob = spec.evaluate(*_data)
            column = [row[1] for row in rob]
            robustness = min(column)
            result[key] = robustness
            del spec
        return result

    def continuous_monitor_for_violations(self, allow_vehicle_light=False):
        vehicle_light_related = [
            "highBeamOn",
            "lowBeamOn",
            "fogLightOn",
            "warningflashOn",
            "turnSignal",
        ]

        list_violations = {}
        for violation in self.violations:
            spec = rtamt.StlDenseTimeSpecification(semantics=rtamt.Semantics.STANDARD)
            for item in self.item_names_of_variable_of_APIS:
                spec.declare_var(item, 'float')
            spec.spec = self.violations[violation]
            try:
                spec.parse()
                # spec.pastify()
            except rtamt.STLParseException as err:
                print('STL Parse Exception: {}'.format(err))
                sys.exit()
            _data = [[var, self.c_data[var]] for var in self.item_names_of_variable_of_APIS]
            rewards = spec.evaluate(*_data)
            column = [row[1] for row in rewards]
            list_violations[violation] = max(column)
            del spec
            violation_clause = self.violations[violation]

            for vehicle_light_attr in vehicle_light_related:
                if vehicle_light_attr in violation_clause:
                    list_violations[violation] = -1.0
                    break

        return list_violations

def get_trace(input_file):
    with open("trace/" + input_file.replace('traceset', 'trace')) as trace_file:
        data = json.load(trace_file)
        return data['trace']

if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1 and os.path.isfile(args[1]):
        input_file = args[1]
        with open(input_file) as f:
            scenario = json.load(f)
            print(scenario['ScenarioName'])

            monitor = Monitor(scenario)

            list_violations = monitor.continuous_monitor_for_violations()
            list_name = list(list_violations.keys())
            list_reward = list(list_violations.values())
            list_reward[0] = max(list_reward[1:])
            print(list_reward[0])
            for idx in range(len(list_reward[1:])):
                if "sub_law_violation" in list_name[idx+1] and list_reward[idx+1] < 0:
                    continue
                print(list_name[idx+1], list_reward[idx+1])
    else:
        print("trace file does not exist.")