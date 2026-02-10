import rtamt
import os
import sys
import numpy as np
from TracePreprocess import Trace
import json
import copy

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
        
        rule38_1 = self.prepare_for_rule38_1()
        rule38_2 = self.prepare_for_rule38_2()
        rule38_3 = self.prepare_for_rule38_3() #for the normal red,yelow,green traffic lights
        rule38_3_1 = self.prepare_for_rule38_3_1()
        rule38_3_2 = self.prepare_for_rule38_3_2()
        rule38 = self.prepare_for_rule38()
        rule42 = self.prepare_for_rule42()     #for the blink yellow light
        rule44 = self.prepare_for_rule44()     #for the lane change and speed limit
        rule45 = self.prepare_for_rule45()     #for pure speed limit
        rule46_2 = self.prepare_for_rule46_2()
        rule46_3 = self.prepare_for_rule46_3()
        rule47 = self.prepare_for_rule47()
        rule50 = self.prepare_for_rule50()
        rule51_3 = self.prepare_for_rule51_3()
        rule51_4 = self.prepare_for_rule51_4()
        rule51_5 = self.prepare_for_rule51_5()
        rule51_6 = self.prepare_for_rule51_6()
        rule51_7 = self.prepare_for_rule51_7()
        rule52 = self.prepare_for_rule52()
        rule53 = self.prepare_for_rule53()
        rule57 = self.prepare_for_rule57()
        rule58 = self.prepare_for_rule58()
        rule59 = self.prepare_for_rule59()
        rule62 = self.prepare_for_rule62()
        rule63 = self.prepare_for_rule63()

        self.muti_traffic_rules["rule38_1"] = rule38_1
        self.muti_traffic_rules["rule38_2"] = rule38_2
        self.muti_traffic_rules["rule38_3"] = rule38_3
        self.muti_traffic_rules["rule38_3_1"] = rule38_3_1
        self.muti_traffic_rules["rule38_3_2"] = rule38_3_2
        self.muti_traffic_rules["rule38"] = rule38
        self.muti_traffic_rules["rule42"] = rule42
        self.muti_traffic_rules["rule44"] = rule44
        self.muti_traffic_rules["rule45"] = rule45
        self.muti_traffic_rules["rule46_2"] = rule46_2
        self.muti_traffic_rules["rule46_3"] = rule46_3
        self.muti_traffic_rules["rule47"] = rule47
        self.muti_traffic_rules["rule50"] = rule50
        self.muti_traffic_rules["rule51_3"] = rule51_3
        self.muti_traffic_rules["rule51_4"] = rule51_4
        self.muti_traffic_rules["rule51_5"] = rule51_5
        self.muti_traffic_rules["rule51_6"] = rule51_6
        self.muti_traffic_rules["rule51_7"] = rule51_7
        self.muti_traffic_rules["rule52"] = rule52
        self.muti_traffic_rules["rule53"] = rule53
        self.muti_traffic_rules["rule57"] = rule57
        self.muti_traffic_rules["rule58"] = rule58
        self.muti_traffic_rules["rule59"] = rule59
        self.muti_traffic_rules["rule62"] = rule62
        self.muti_traffic_rules["rule63"] = rule63

    def prepare_for_rule38_1(self):              
        #GREEN = 3; 
        traffic_rule = '(\
                                always(((trafficLightAheadcolor == 3) and \
                                    ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                                    (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)) \
                                    implies ( eventually[0,2](speed > 0.5) ))\
                                )'
        return traffic_rule

    def prepare_for_rule38_2(self):              
        #YELLOW = 2;
        traffic_rule = '(\
                                always(( ((trafficLightAheadcolor == 2) and \
                                    ((stoplineAhead == 0) or (currentLanenumber == 0))) \
                                    implies ( eventually[0,2](speed > 0.5) )) and \
                                    (((trafficLightAheadcolor == 2) and\
                                    (stoplineAhead >= 0.5) and\
                                    (stoplineAhead <= 3.5) and\
                                    (currentLanenumber > 0)) \
                                    implies ( eventually[0,3](speed < 0.5) ) )) \
                                )'
        return traffic_rule

    def prepare_for_rule38_3(self):              
        #RED = 1;   
        traffic_rule = '(\
                                always((((trafficLightAheadcolor == 1) and \
                                    ((stoplineAhead <= 2) or (junctionAhead <= 2)) and\
                                    (currentLanenumber > 0) and \
                                    (direction <= 1)) \
                                    implies ( eventually[0,3](speed < 0.5) )) and \
                                    (((trafficLightAheadcolor == 1) and \
                                    ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                                    (direction == 2) and (PriorityNPCAhead == 0) and \
                                    (currentLanenumber > 0) and \
                                    (PriorityPedsAhead == 0) ) \
                                    implies ( eventually[0,2](speed > 0.5) )) ) \
                                )'
        return traffic_rule

    def prepare_for_rule38_3_1(self):
        traffic_rule = '(\
                            always((((trafficLightAheadcolor == 1) and \
                                ((stoplineAhead <= 2) or (junctionAhead <= 2)) and\
                                (currentLanenumber > 0) and \
                                (direction <= 1)) \
                                implies ( eventually[0,3](speed < 0.5) )))\
                            )'
        return traffic_rule
    
    def prepare_for_rule38_3_2(self):
        traffic_rule = '(\
                            always((((trafficLightAheadcolor == 1) and \
                            ((stoplineAhead <= 2) or (junctionAhead <= 2)) and \
                            (direction == 2) and (PriorityNPCAhead == 0) and \
                            (currentLanenumber > 0) and \
                            (PriorityPedsAhead == 0) ) \
                            implies ( eventually[0,2](speed > 0.5) ))) \
                        )'
        return traffic_rule

    def prepare_for_rule38(self):              
        # message TrafficLight {
        #   enum Color {
        #     UNKNOWN = 0;
        #     RED = 1;
        #     YELLOW = 2;
        #     GREEN = 3;
        #     BLACK = 4;
        #   };       
        # we should put different weight on different variables!
        traffic_rule = '(always(((trafficLightAheadcolor == 3) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0)) implies ( speed >= 0.5 ))   and \
                                always((((trafficLightAheadcolor == 2) and ((stoplineAhead == 0) or (stoplineAhead > 50))) implies ( speed > 0.5 )) and \
                                        (((trafficLightAheadcolor == 2) and (stoplineAhead <= 2)) implies (speed < 0.5)) ) and \
                                always((((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction <= 1)) implies ( speed < 0.5 )) and \
                                        (((trafficLightAheadcolor == 1) and ((stoplineAhead <= 2) or (junctionAhead <= 2)) and (direction == 2) and (PriorityNPCAhead == 0) and (PriorityPedsAhead == 0) ) implies ( speed >= 0.5 )) ) \
                                )'
        return traffic_rule

    def prepare_for_rule42(self):
        # \begin{aligned}
        #     & G(((trafficLightAhead.color = yellow \land \\
        #     & trafficLightAhead.blink) \lor \\
        #     & (trafficLightAhead.direction.color = yellow \land \\
        #     & trafficLightAhead.direction.blink)) \land \\
        #     & ( stoplineAhead(realvalue) \lor junctionAhead(realvalue) )\\
        #     & \implies    speed < realvalue )
        # \end{aligned}          
        traffic_rule = '(always(((trafficLightAheadcolor == 2) and \
                                (trafficLightAheadblink == 1) and \
                                ((stoplineAhead <= 1) or (junctionAhead <= 1)))\
                                implies (speed < 5))\
                                )'
        return traffic_rule

    def prepare_for_rule44(self):
        # \begin{aligned}
        #     & G(currentLane.number \geq 2  \implies \\
        #     & (speed \geq speedLimit.lowerLimit \land  \\
        #     & speed \leq speedLimit.upperLimit)) \land \\
        #     & G(isLaneChanging \land   currentLane.number \geq 2 \\
        #     & \implies  \lnot PriorityNPCAhead)
        # \end{aligned}          
        traffic_rule = '(always((currentLanenumber >= 2)  implies ((speed >= speedLimitlowerLimit) and (speed <= speedLimitupperLimit))) and \
                                always(((isLaneChanging == 1) and (currentLanenumber >= 2)) implies  (PriorityNPCAhead == 0 )))'
        return traffic_rule

    def prepare_for_rule45(self):
        # \begin{aligned}
        #     & G(speed \geq speedLimit.lowerLimit  \land \\
        #     & speed \leq speedLimit.upperLimit )
        # \end{aligned}    
        traffic_rule = '(always((speed >= speedLimitlowerLimit) and (speed <= speedLimitupperLimit)))'
        return traffic_rule

    def prepare_for_rule46_2(self):
        # \begin{aligned}
        #     & G( (direction \neq forward) \lor isTurningAround) \\
        #     & \implies   speed \leq 30 )
        # \end{aligned}
        traffic_rule = '(always(((direction == 1) or (direction == 2) or (isTurningAround == 1))\
                                implies (speed <= 30)))'
        return traffic_rule

    def prepare_for_rule46_3(self):
        # \begin{aligned}
        #     & G((Weather.rain \geq 0.5 \lor Weather.fog \geq 0.5 \\
        #     & \lor  Weather.snow \geq 0.5) \land Weather.visibility \leq 50 \\
        #     & \implies speed \leq 30)
        # \end{aligned}
        traffic_rule = '(always(((rain >= 0.5) or (fog >= 0.5) or (snow >= 0.5))\
                                implies (speed <= 30)))'

        return traffic_rule

    def prepare_for_rule47(self):
        # $$
        # \begin{aligned}
            # & G(isOverTaking \implies  turnSignal = left \land \\
            # & (F[-realvalue,\ realvalue](hornOn) \lor \\
            # & ( highBeamOn \land (highBeamOn \\
            # & \implies   F[0,\ realvalue](lowBeamOn) )) \lor \\
            # & ( lowBeamOn \land (lowBeamOn \\
            # & \implies   F[0,\ realvalue](highBeamOn) )))  \land  \\
            # & F[0,\ realvalue]( (turnSignal = right \land \\
            # & isLaneChanging \implies NearestNPC(realvalue) \\
            # & \land isLaneChanging) )
        # \end{aligned}
        # $$
        traffic_rule = '(always((isOverTaking == 1)\
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

        return traffic_rule

    def prepare_for_rule50(self):
        # \begin{aligned}
        #     & G(speed \geq speedLimit.lowerLimit  \land \\
        #     & speed \leq speedLimit.upperLimit )
        # \end{aligned}    
        traffic_rule = '(always ((not (gear==2))))'
        # traffic_rule = '(always (gear==1))'
        return traffic_rule

    def prepare_for_rule51_3(self):
        traffic_rule = "(always ((((((((trafficLightAheadcolor==3) and (direction==1)) and (Time<=20.0)) and (Time>=7.0))) -> ((turnSignal==1))) and (((((trafficLightAheadcolor==3) and (direction==1)) and (((Time>=20.0) or (Time<=7.0))))) -> (((turnSignal==1) and (lowBeamOn==1)))))))"
        return traffic_rule

    def prepare_for_rule51_4(self):
        traffic_rule = "(always ((((trafficLightAheadcolor==3) and (((not (NPCAheadAhead<=8.0)) or (((((NPCAheadAhead<=8.0) -> (eventually[0,2] ((NPCAheadspeed>0.5))))) and (NPCAheadAhead<=8.0)))))) -> (((eventually[0,3] ((speed>0.5)))) and (not (NPCAheadAhead<=0.5))))))"
        return traffic_rule

    def prepare_for_rule51_5(self):
        traffic_rule = "(always ((((trafficLightAheadcolor==1) and ((((stoplineAhead<=2.0) or (junctionAhead<=2.0)) or (NPCAheadAhead<=0.5)))) -> (eventually[0,2] ((speed < 0.5))))))"
        return traffic_rule

    def prepare_for_rule51_6(self):
        traffic_rule = "(always ((((((direction==2) and (NPCAheadAhead<=2.0)) and ((eventually[0,2] ((NPCAheadspeed<0.5)))))) -> (eventually[0,3] ((speed<0.5))))))"
        return traffic_rule

    def prepare_for_rule51_7(self):
        traffic_rule = "(always (((((((direction==2) or (direction==1))) and (((PriorityNPCAhead==1) or (PriorityPedsAhead==1))))) -> (eventually[0,2] ((speed<0.5))))))"
        return traffic_rule

    def prepare_for_rule52(self):
        traffic_rule = "(always (((((signalAhead==0 and ((PriorityNPCAhead==1 or PriorityPedsAhead==1))) and junctionAhead<=1.0)) -> (eventually[0,2] (speed<0.5)))))"
        return traffic_rule

    def prepare_for_rule53(self):
        traffic_rule = "(always ((((isTrafficJam==1 and (((NPCAheadspeed<0.5 or NPCAheadAhead<=0.5) or junctionAhead<=1.0)))) -> (eventually[0,2] (speed<0.5)))))"
        return traffic_rule

    def prepare_for_rule57(self):
        traffic_rule = "((always ((direction==1 -> turnSignal==1))) and (always ((direction==2 -> turnSignal==2))))"
        return traffic_rule

    def prepare_for_rule58(self):
        traffic_rule = "(always ((((((((((not streetLightOn==1) and ((Time>=20.0 or Time<=7.0)))) or (((rain>=0.5 or fog>=0.5) or snow>=0.5))) and (not NPCAheadAhead<=10.0))) -> highBeamOn==1) and (NPCAheadAhead<=10.0 -> (not highBeamOn==1))) and (fog>=0.5 -> ((fogLightOn==1 and warningflashOn==1))))))"
        return traffic_rule

    def prepare_for_rule59(self):
        traffic_rule = "(always (((((crosswalkAhead<=5.0 or ((signalAhead==0 and junctionAhead<=1.0)))) and ((Time>=20.0 or Time<=7.0))) -> ((eventually[0,3] ((highBeamOn==1 and ((highBeamOn==1 -> (eventually[0,3] (lowBeamOn==1))))))) or (eventually[0,3] ((lowBeamOn==1 and ((lowBeamOn==1 -> (eventually[0,3] (highBeamOn==1)))))))))))"
        return traffic_rule

    def prepare_for_rule62(self):
        traffic_rule = "(always (((not honkingAllowed==1) -> (not hornOn==1))))"
        return traffic_rule
    
    def prepare_for_rule63(self):
        traffic_rule ="(always (speed < 60))"
        return traffic_rule

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
            result[key] = rob[0][1]
            del spec
        return result

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 1:
        print("trace filename missing")
        exit()
    elif not os.path.exists(args[1]):
        print("file does not exist")
        exit()
    input_file = args[1]
    with open(input_file) as f:
        data = json.load(f)  # read as a msg from apollo via websocket
        scenario_name = data['ScenarioName']
        monitor = Monitor(data)
        judge_result = monitor.continuous_monitor_for_muti_traffic_rules()
        print( scenario_name, '\n', judge_result)
        
