1、搭建环境

解压Carla压缩包（版本0.9.13）到/home/xxx
配置环境变量到~/.bashrc：
export CARLA_ROOT=/home/xxx/CARLA_0.9.13
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.13-py3.7-linux-x86_64.egg:${CARLA_ROOT}/PythonAPI:${CARLA_ROOT}/PythonAPI/carla:${CARLA_ROOT}/PythonAPI/carla/agents:${CARLA_ROOT}/PythonAPI/carla/agents/navigation:${CARLA_ROOT}/PythonAPI/examples
保存后运行
source ~/.bashrc

打开CARLA_0.9.13/PythonAPI/carla/agents/navigation/behavior_agent.py，查找代码
elif self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
（应该在第291行），修改为
elif self._incoming_waypoint and self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
这样是为了处理behavior agent的空引用bug。

把scenario_runner_able_edition/patch_for_carla中的local_planner.py和controller.py复制到
CARLA_0.9.13/PythonAPI/carla/agents/navigation/（请自行备份原文件）代替原有的local_planner.py和controller.py，
前者是为了重放场景时避免npc已靠近waypoint但不被认为已抵达而造成npc原地打转的行为，
后者是为了使车辆在遇到路径点处于两侧，behavior agent刹车转向导致车辆无法运动的bug。

输入命令
conda create -n srunner python==3.7
创建名为srunner的conda环境，python版本3.7,进入环境输入
pip3 install -r requirements_srunner.txt
然后再额外运行
pip3 install websocket
pip3 install websocket-client

输入命令
conda create -n law python==3.7
创建名为law的conda环境，python版本3.7,进入环境输入
pip3 install -r requirements_law.txt

出现包兼容性问题把出错的注释掉再重新运行一遍pip命令即可

2、运行初始的场景，生成json场景文件

首先另外打开一个终端，输入命令
cd CARLA_0.9.13
进入CARLA的主文件夹，运行
./CarlaUE4.sh
启动Carla。现在应该看到默认的地图为town10，切换地图后过快使用world或map相关的变量可能会导致段错误、找不到车辆对象等问题，重复后续命令即可，无需重启Carla。
当Carla崩溃时才需要重新启动。Carla崩溃的问题听说是传感器actor反复创建删除后释放不完全的显存泄漏问题，是Carla官方自己的问题，目前个人暂无已知的避免方法，只能经常重启。
运行Carla不需要其他conda环境，但其余步骤均需要进入conda环境完成。

输入命令
cd scenario_runner_able_edition
conda activate srunner
进入srunner环境

输入命令
python3 scenario_runner.py --sync --reloadWorld --osc able_osc_scenarios/avunit_s1.osc
在已有的Carla中运行osc场景文件，场景文件位于able_osc_scenarios和srunner/examples中。
osc场景对车辆生成的配置放在把scenario_runner_able_edition/srunner/scenariomanager/carla_data_provider.py中，可以自行修改。

要运行其他场景，使用命令
python3 scenario_runner.py --scenario FollowLeadingVehicle_1 --reloadWorld
即可运行srunner/examples中xml文件定义的场景，在此之前运行scenario_runner_able_edition下的manual_control.py来控制ego主车。

场景运行结束后会在trace文件夹下生成带有场景名称和顺序编号的json场景文件。
这些json文件包括了npc车辆的一些路径点，以及附在最后的ego车辆更加详细的驾驶过程记录。

3、随机变异json场景文件的数值

输入命令
cd scenario_runner_able_edition/Law_judgement
conda activate law
进入law环境（如果还在srunner环境用conda deactivate退出）

输入命令
python3 TestCaseRandom.py
在当前目录的trace文件夹下，把上一级文件夹的trace中的每一个json文件，都随机修改数值，生成15个场景，加上原有的1个，16个场景放在一个json文件中，输出到traceset_randomized文件夹。

4、遗传算法变异场景

输入命令
cd scenario_runner_able_edition/Law_judgement
conda activate law
进入law环境（已在此环境可忽略）

输入命令
python3 GeneticAlgorithm.py
即可自动完成变异过程，把traceset_randomized的每个文件中的32个场景，经过n代遗传算法，输出到traceset_mutated/。
遗传算法的指标为交规违反指数，位于scenario_runner_able_edition/Law_judgement/law_judgement_extended.py中。

命令解释：
python3 scenario_runner.py --sync --reloadWorld --able trace/trace_test.json --agent srunner/autoagents/behavior_agent.py --agentConfig trace/trace_test.json
--able trace/trace_test.json把指定的json场景集作为输入的种群，在Carla中运行并分析交规违反情况后进行选择。
--agent srunner/autoagents/behavior_agent.py用于指定所用的ADS，
--agentConfig trace/trace_test.json用于提供初始位置和路径点等信息。

5、训练代理模型

输入命令
conda create -n gfn python==3.10
创建名为gfn的conda环境，python版本3.10,
输入命令
cd scenario_runner_able_edition/Law_judgement
conda activate gfn
进入gfn环境，输入
pip3 install -r requirements_gfn.txt

输入命令
python3 GFN_trainproxy.py
开始训练代理模型，每个代理模型的输入为每个场景session在遗传算法产生的所有场景种群，
输入的数据集位于scenario_runner_able_edition/Law_judgement/traceset_mutated/。

生成的代理模型文件位于
scenario_runner_able_edition/Law_judgement/gflownet/generator/proxy/model/
按照不同session分类。

6、训练流生成网络模型GFN

输入命令
cd scenario_runner_able_edition/Law_judgement
conda activate gfn
进入gfn环境（已在此环境可忽略）

输入命令
python3 GFN_traingenerator.py
开始训练GFN。分别生成action sequence文件和json场景文件到
scenario_runner_able_edition/Law_judgement/generated_actionseq/与
scenario_runner_able_edition/Law_judgement/generated_scenarios/,
即为可以测试的场景文件。
