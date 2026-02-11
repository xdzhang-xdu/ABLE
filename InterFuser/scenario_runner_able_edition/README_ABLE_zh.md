1.前提准备

1.1.安装Carla

1.1.1.
解压Carla压缩包（版本0.9.13）到/home/xxx

配置环境变量到~/.bashrc：
export CARLA_ROOT=/home/xxx/CARLA_0.9.13
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.13-py3.7-linux-x86_64.egg:${CARLA_ROOT}/PythonAPI:${CARLA_ROOT}/PythonAPI/carla:${CARLA_ROOT}/PythonAPI/carla/agents:${CARLA_ROOT}/PythonAPI/carla/agents/navigation:${CARLA_ROOT}/PythonAPI/examples
保存后运行
source ~/.bashrc

1.1.2.修改Carla部分PythonAPI代码
打开CARLA_0.9.13/PythonAPI/carla/agents/navigation/behavior_agent.py，定位到代码
elif self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
（应该在第291行），修改为
elif self._incoming_waypoint and self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
这样是为了处理behavior agent的空引用bug。

把scenario_runner_able_edition/patch_for_carla中的local_planner.py和controller.py复制到
CARLA_0.9.13/PythonAPI/carla/agents/navigation/（请自行备份原文件）代替原有的local_planner.py和controller.py，
前者是为了重放场景时避免npc已靠近waypoint但不被认为已抵达而造成npc原地打转的行为，
后者是为了使车辆在遇到路径点处于两侧，behavior agent刹车转向导致车辆无法运动的bug。

1.2.安装ADS以及bridge
以下所有文件替换前请记得保存原文件。

1.2.1.安装Apollo
请按照https://github.com/MaisJamal/carla_apollo_bridge中的介绍安装Apollo以及相应的bridge，确保Apollo和Carla能够正常通信。当bridge启动了pygame的窗口、Dreamview中出现地图、启动Apollo的定位模块后能正确匹配道路后Apollo安装即为成功。此时可以在Dreamview中打开规划、控制、感知、预测模块，并手动规划目的地，尝试让Apollo在Carla中行驶。
另外，在编译Apollo时，需要把apollo_routing_sender/中的speed_limit_dicider.cc以及trajectory_stitcher.cc替换Apollo中原有的源码，并把control_conf.pb.txt替换控制模块中原有的参数配置文件，使Apollo的驾驶更加流畅和准确。在编译完成后，把apollo_routing_sender/中的carla_town05和carla_town06复制到Apollo的地图模块文件夹中，Apollo才能正确识别Carla地图以及定位。在安装了imap(https://github.com/daohu527/imap)的情况下，运行xodr2bin_7.0.sh与xodr2bin_8.0.sh可以在不同版本的Apollo中把xodr格式的Carla地图转换为Apollo需要的bin格式地图。

1.2.2.安装Autoware
请按照https://github.com/hatem-darweesh/op_bridge/tree/ros2-humble中的介绍安装Autoware以及相应的bridge。我们采用的Autoware是Universe以及ROS2 Humble。
另外，在编译Autoware时，需要把autoware_routing_sender/中的src_minimum/下的所有文件按照相应的目录结构复制到Autoware相应的源码目录中，加快Autoware定位模块的启动速度与精度。autoware_routing_sender/中的yaml文件和cpp文件也需要替换Autoware中的同名文件，以解决Autoware无法行驶的问题。

1.2.3.安装InterFuser
请按照https://github.com/opendilab/InterFuser中的介绍安装InterFuser。由于InterFuser与场景控制的脚本紧耦合，因此需要切换到InterFuser/下作为独立的工作目录。

2.训练GFlowNet并生成场景文件

2.1.运行OSC场景脚本，在Carla中驾驶车辆，并生成场景文件

2.1.1.启动Carla
在终端中运行
./CARLA_0.9.13/CarlaUE4.sh
启动Carla。运行Carla不需要进入conda环境，但其余步骤均需要进入一个具体的conda环境完成。

2.1.2.配置运行场景的conda环境
输入命令
conda create -n srunner python==3.7
创建名为srunner的conda环境，python版本为3.7。进入环境输入
pip3 install -r requirements_srunner.txt
然后再额外安装以下两个包：
pip3 install websocket
pip3 install websocket-client
这是因为python仿真脚本需要通过websocket来与Apollo进行通信，完成启动模块和设置目的地等操作。对于Autoware而言，我们通过ros2的命令直接设置目的地，因此无需其他python包。

关于srunner的其他内容见scenario_runner_able_edition/READ_ME.md

输入命令
cd scenario_runner_able_edition
conda activate srunner
以scenario_runner_able_edition为工作目录，srunner为conda环境。

2.1.3.运行OSC场景脚本
首先运行scenario_runner_able_edition/manual_control.py来控制ego主车。

输入命令
python3 scenario_runner.py --sync --reloadWorld --osc able_osc_scenarios/avunit_s1.osc
以在Carla中运行osc场景脚本。可参考OpenSCENARIO2.0规范自行编写场景脚本。

要运行其他场景，可以使用命令
python3 scenario_runner.py --scenario FollowLeadingVehicle_1 --reloadWorld
即可运行scenario_runner_able_edition/srunner/examples/中xml格式的场景脚本。scenario_runner_able_edition/srunner/examples/中也含有srunner自带的osc场景脚本。

场景运行结束后会在scenario_runner_able_edition/trace中生成带有场景名称和顺序编号的场景文件。这些场景文件为json格式，包括了npc车辆的一些路径点，以及关于ego车辆详细的驾驶过程记录。

2.2.构造场景训练集

2.2.1.配置交通规则计算的conda环境
输入命令
conda create -n law python==3.7
创建名为law的conda环境，python版本3.7。进入环境输入
pip3 install -r requirements_law.txt
如果出现包兼容性问题，把出错的注释掉再重新运行一遍pip命令即可。

关于交通规则计算的其他内容见scenario_runner_able_edition/Law_judgement/readme.md

输入命令
cd scenario_runner_able_edition/Law_judgement
conda activate srunner
以Law_judgement为工作目录，law为conda环境。

2.2.2.构造遗传算法初始种群
运行python3 TestCaseRandom.py，把scenario_runner_able_edition/Law_judgement/trace中的场景文件进行随机化，输出到scenario_runner_able_edition/Law_judgement/traceset_randomized/。

2.2.3.运行遗传算法
运行GeneticAlgorithm.py，把scenario_runner_able_edition/Law_judgement/traceset_randomized/中的每个场景文件作为一个初始种群，经过遗传算法，输出到scenario_runner_able_edition/Law_judgement/traceset_mutated/。输出的每个场景文件包含了全部代际的种群，作为场景训练集。
运行遗传算法过程中需要在Carla仿真中运行ADS，记录trace文件并计算交规违反指标，该指标用于评估遗传算法中每个代际的种群中的个体，并决定筛选结果。交规违反指标的计算位于scenario_runner_able_edition/Law_judgement/law_judgement_extended.py中。

遗传算法过程中运行Carla仿真的参数如下：
python3 scenario_runner.py --sync --reloadWorld --able trace/trace_test.json --agent srunner/autoagents/behavior_agent.py --agentConfig trace/trace_test.json
--able trace/trace_test.json把指定的json场景集作为输入的种群，在Carla中运行并分析交规违反情况后进行选择。
--agent srunner/autoagents/behavior_agent.py用于指定所用的ADS，对于测试不同的ADS需要对应的参数，如测试Apollo需要使用--waitEgo参数并另外启动Apollo的进程。
--agentConfig trace/trace_test.json用于提供初始位置和路径点等信息。

2.3.训练代理模型

2.3.1.配置训练模型所需环境
输入命令
conda create -n gfn python==3.10
创建名为gfn的conda环境，python版本3.10。进入环境输入
pip3 install -r requirements_gfn.txt

输入命令
cd scenario_runner_able_edition/Law_judgement
conda activate gfn
以Law_judgement为工作目录，gfn为conda环境。

2.3.2.训练代理模型
运行GFN_trainsurrogate_ensemble.py开始训练代理模型，代理模型的输入为每个session在遗传算法产生的全部代际的种群，场景训练集位于scenario_runner_able_edition/Law_judgement/traceset_mutated/。
生成的代理模型文件位于scenario_runner_able_edition/Law_judgement/gflownet/generator/proxy/model/，按照不同session分类。

2.4.训练流生成网络模型GFlowNet

输入命令
cd scenario_runner_able_edition/Law_judgement
conda activate gfn
以Law_judgement为工作目录，gfn为conda环境。

运行GFN_traingenerator.py开始训练GFN。分别生成action sequence文件和json格式的场景文件到
scenario_runner_able_edition/Law_judgement/generated_actionseq/与scenario_runner_able_edition/Law_judgement/generated_scenarios/。
scenario_runner_able_edition/Law_judgement/generated_scenarios/中的场景文件即为需要测试的场景文件。

2.5.Active Learning

运行GFN_activelearning.py以启用Active Learning。GFN_activelearning.py同时封装了代理模型和GFlowNet的训练，以及ADS的部署和Carla的仿真。

3.ADS仿真测试

3.1.Apollo
运行apollo_routing_sender/co-sim_mj.py即可完成启动Apollo、Carla、通信bridge、从scenario_runner_able_edition/Law_judgement/generated_scenarios/复制场景文件、运行srunner部署场景、记录场景trace等一系列操作。

3.2.Autoware
运行autoware_routing_sender/co-sim.py即可完成和上述类似的操作。

3.3.Behavior Agent
运行scenario_runner_able_edition/behavior_auto_test.py即可完成使用Behavior Agent的场景测试。

3.4.InterFuser
运行InterFuser/co-sim.py即可完成使用InterFuser的场景测试。由于InterFuser与仿真测试的耦合度较高，因此我们修改了srunner的启动代码，在python脚本中直接运行InterFuser。

4.仿真结果评估程序

violation_auditor.py主要进行关于交通规则违反表达式的计算。
evaluator.py进行各类数据统计和绘图，包括各个step figures、bar figures和代理模型的评估。
test_suit_opt.py进行两种测试集优化方法，以及各类对比。
