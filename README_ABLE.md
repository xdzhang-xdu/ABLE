# 1. Prerequisites

## 1.1 Installation of CARLA

### 1.1.1 Environment Configuration

Extract the CARLA archive (version 0.9.13) to `/home/xxx`.

Configure the environment variables in `~/.bashrc` as follows:

```bash
export CARLA_ROOT=/home/xxx/CARLA_0.9.13
export PYTHONPATH=$PYTHONPATH:${CARLA_ROOT}/PythonAPI/carla/dist/carla-0.9.13-py3.7-linux-x86_64.egg:${CARLA_ROOT}/PythonAPI:${CARLA_ROOT}/PythonAPI/carla:${CARLA_ROOT}/PythonAPI/carla/agents:${CARLA_ROOT}/PythonAPI/carla/agents/navigation:${CARLA_ROOT}/PythonAPI/examples
```

After saving the configuration, execute:

```bash
source ~/.bashrc
```

### 1.1.2 Modification of the CARLA Python API

Open the file
`CARLA_0.9.13/PythonAPI/carla/agents/navigation/behavior_agent.py`
and locate the following code segment (approximately at line 291):

```python
elif self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
```

Modify it as follows:

```python
elif self._incoming_waypoint and self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
```

This modification addresses a null-reference issue in the behavior agent.

Next, copy `local_planner.py` and `controller.py` from
`scenario_runner_able_edition/patch_for_carla/`
to:

```
CARLA_0.9.13/PythonAPI/carla/agents/navigation/
```

Please back up the original files before replacement.

The modified `local_planner.py` prevents non-player characters (NPCs) from circling near waypoints due to incorrect arrival detection during scenario replay.
The modified `controller.py` resolves a braking and steering malfunction that occurs when waypoints are located on both sides of the vehicle, which may otherwise prevent vehicle movement.

---

## 1.2 Installation of ADS and Bridge Components

Before replacing any files, ensure that all original files are backed up.

### 1.2.1 Installation of Apollo

Install Apollo and the corresponding bridge following the instructions at:
[https://github.com/MaisJamal/carla_apollo_bridge](https://github.com/MaisJamal/carla_apollo_bridge)

Successful installation is confirmed when:

* A pygame window is launched by the bridge,
* A map is displayed in Dreamview,
* The localization module correctly matches road structures.

Afterwards, the planning, control, perception, and prediction modules can be activated in Dreamview, and a destination can be manually specified to verify vehicle operation in CARLA.

During compilation, replace `speed_limit_dicider.cc` and `trajectory_stitcher.cc` in `apollo_routing_sender/` with the corresponding files in Apollo. Additionally, replace `control_conf.pb.txt` in the control module configuration to improve driving smoothness and accuracy.

After compilation, copy `carla_town05` and `carla_town06` from `apollo_routing_sender/` to the Apollo map directory to enable correct map recognition and localization.

When imap ([https://github.com/daohu527/imap](https://github.com/daohu527/imap)) is installed, execute `xodr2bin_7.0.sh` and `xodr2bin_8.0.sh` to convert CARLA maps from XODR format to Apollo-compatible BIN format.

---

### 1.2.2 Installation of Autoware

Install Autoware and the corresponding bridge according to:
[https://github.com/hatem-darweesh/op_bridge/tree/ros2-humble](https://github.com/hatem-darweesh/op_bridge/tree/ros2-humble)

This framework adopts Autoware Universe with ROS2 Humble.

During compilation, copy all files from `autoware_routing_sender/src_minimum/` into the corresponding Autoware source directories, following the original directory structure, to improve the initialization speed and accuracy of the localization module.

Additionally, replace the YAML and C++ files in `autoware_routing_sender/` with the files of the same name in Autoware to resolve issues that prevent vehicle operation.

---

### 1.2.3 Installation of InterFuser

Install InterFuser following the instructions at:
[https://github.com/opendilab/InterFuser](https://github.com/opendilab/InterFuser)

Since InterFuser is tightly coupled with the scenario control scripts, the working directory must be switched to the `InterFuser/` directory during operation.

---

# 2. Training GFlowNet and Generating Scenario Files

## 2.1 Execution of OSC Scripts and Scenario Collection

### 2.1.1 Launching CARLA

Start CARLA using:

```bash
./CARLA_0.9.13/CarlaUE4.sh
```

CARLA does not require activation of a conda environment. However, all subsequent steps must be performed within the appropriate conda environments.

---

### 2.1.2 Configuration of the Scenario Execution Environment

Create a conda environment named `srunner` with Python 3.7:

```bash
conda create -n srunner python==3.7
```

Activate the environment and install dependencies:

```bash
pip3 install -r requirements_srunner.txt
pip3 install websocket
pip3 install websocket-client
```

These packages enable communication between Python simulation scripts and Apollo via WebSocket. For Autoware, destinations are configured using ROS2 commands, and no additional Python packages are required.

Further details are provided in `scenario_runner_able_edition/READ_ME.md`.

Set the working directory and activate the environment:

```bash
cd scenario_runner_able_edition
conda activate srunner
```

---

### 2.1.3 Execution of OSC Scenario Scripts

First, execute `manual_control.py` to control the ego vehicle.

Run an OSC scenario using:

```bash
python3 scenario_runner.py --sync --reloadWorld --osc able_osc_scenarios/avunit_s1.osc
```

Custom scenarios may be developed in accordance with the OpenSCENARIO 2.0 specification.

To execute XML-based scenarios, use:

```bash
python3 scenario_runner.py --scenario FollowLeadingVehicle_1 --reloadWorld
```

After execution, scenario files are generated in the `scenario_runner_able_edition/trace` directory. These JSON-formatted files contain NPC trajectories and detailed driving records of the ego vehicle.

---

## 2.2 Construction of the Scenario Training Dataset

### 2.2.1 Configuration of the Traffic Rule Evaluation Environment

Create a conda environment named `law`:

```bash
conda create -n law python==3.7
```

Install dependencies:

```bash
pip3 install -r requirements_law.txt
```

If compatibility issues arise, comment out conflicting packages and rerun the installation.

Additional details are available in `scenario_runner_able_edition/Law_judgement/readme.md`.

Set the working directory and activate the environment:

```bash
cd scenario_runner_able_edition/Law_judgement
conda activate law
```

---

### 2.2.2 Generation of the Initial Population

Execute:

```bash
python3 TestCaseRandom.py
```

This script randomizes scenario files in `trace` and outputs the results to `traceset_randomized/`.

---

### 2.2.3 Execution of the Genetic Algorithm

Run:

```bash
python3 GeneticAlgorithm.py
```

Each scenario in `traceset_randomized/` is treated as an initial population. The genetic algorithm evolves these populations and outputs the results to `traceset_mutated/`. Each output file contains populations from all generations and constitutes the final training dataset.

During optimization, CARLA simulations are executed with ADSs to collect trace files and compute traffic rule violation metrics. These metrics, implemented in `law_judgement_extended.py`, are used to evaluate and select individuals.

The simulation is executed as follows:

```bash
python3 scenario_runner.py --sync --reloadWorld --able trace/trace_test.json \
--agent srunner/autoagents/behavior_agent.py \
--agentConfig trace/trace_test.json
```

The `--able` parameter specifies the scenario population.
The `--agent` parameter defines the ADS under evaluation.
The `--agentConfig` parameter provides initial positions and waypoints.

---

## 2.3 Training of Surrogate Models

### 2.3.1 Environment Configuration

Create a conda environment named `gfn`:

```bash
conda create -n gfn python==3.10
```

Install dependencies:

```bash
pip3 install -r requirements_gfn.txt
```

Activate the environment:

```bash
cd scenario_runner_able_edition/Law_judgement
conda activate gfn
```

---

### 2.3.2 Surrogate Model Training

Execute:

```bash
python3 GFN_trainsurrogate_ensemble.py
```

The surrogate models are trained using all generations of populations generated by the genetic algorithm. The training data are located in `traceset_mutated/`.

The trained models are stored in:

```
gflownet/generator/proxy/model/
```

and are organized by session.

---

## 2.4 Training of the GFlowNet Generator

Activate the `gfn` environment and set the working directory as described above.

Run:

```bash
python3 GFN_traingenerator.py
```

This process generates action sequence files and JSON-formatted scenario files in:

```
generated_actionseq/
generated_scenarios/
```

The generated scenarios constitute the test dataset.

---

## 2.5 Active Learning

Execute:

```bash
python3 GFN_activelearning.py
```

This script integrates surrogate model training, GFlowNet training, ADS deployment, and CARLA simulation within an active learning framework.

---

# 3. ADS Simulation Testing

## 3.1 Apollo

Execute:

```bash
python3 apollo_routing_sender/co-sim_mj.py
```

This script automates the initialization of Apollo, CARLA, and the communication bridge, copies generated scenarios, deploys scenarios using ScenarioRunner, and records execution traces.

---

## 3.2 Autoware

Execute:

```bash
python3 autoware_routing_sender/co-sim.py
```

This script performs operations analogous to those for Apollo.

---

## 3.3 Behavior Agent

Execute:

```bash
python3 scenario_runner_able_edition/behavior_auto_test.py
```

This command evaluates scenarios using the CARLA Behavior Agent.

---

## 3.4 InterFuser

Execute:

```bash
python3 InterFuser/co-sim.py
```

This script enables scenario testing with InterFuser. Due to its tight integration with the simulation framework, the ScenarioRunner startup procedure has been modified to directly invoke InterFuser within Python scripts.

---

# 4. Simulation Result Evaluation

The evaluation framework consists of the following components:

* `violation_auditor.py`: Computes traffic rule violation expressions.
* `evaluator.py`: Performs statistical analysis and visualization, including step-wise figures, bar charts, and surrogate model evaluation.
* `test_suit_opt.py`: Implements two test set optimization methods and conducts comparative analyses.
