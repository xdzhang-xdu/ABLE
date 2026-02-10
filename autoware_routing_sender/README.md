## Autoware Troubleshooting Guide

### 1. Errors When Importing CARLA

When importing CARLA, it is essential to use Python outside of a Conda environment. The import may fail if executed within Conda. Therefore, the Conda environment must be deactivated before running the relevant scripts:

```bash
conda deactivate
```

---

### 2. Required Python Packages for Running Open Planner

The following Python packages are required to run Open Planner:

* `py_trees`
* `networkx`
* `tabulate`
* `transforms3d`

These packages should be installed in the active Python environment before execution.

---

### 3. Excessive Initialization Time Before Driving Readiness

Autoware may require an excessively long time to become ready for driving after startup. This issue arises because the Open Planner bridge transmits only sensor data such as GNSS, while Autoware relies on the NDT (Normal Distributions Transform) module to scan the map and estimate the ego vehicle’s position autonomously.

Using CARLA Town05 as an example:

* Node initialization and map loading require approximately 30 seconds.
* Point cloud map loading requires approximately 60 seconds.
* Ego vehicle localization by the NDT module requires approximately 3 minutes and 30 seconds.

The localization process is particularly time-consuming and may also introduce angular misalignment between the point cloud map and the road map.

To bypass the NDT-based localization process, the ego vehicle’s position and orientation can be specified externally. This requires modifying the `launch.xml` files, YAML configuration files, and C++ source files under `autoware/src`, followed by recompilation. With these changes, the vehicle’s pose is assigned immediately after the point cloud map is loaded.

Reference:
[https://github.com/autowarefoundation/autoware.universe/pull/6692](https://github.com/autowarefoundation/autoware.universe/pull/6692)

All modified files and directory structures are stored in `src_minimum`. The `src_extend` directory additionally extends the startup options in `planning_simulator.launch.xml` to facilitate rapid testing.

---

### 4. No Planned Path After Setting a Destination

If no planned trajectory is generated after setting a destination, the operation mode should be switched from `STOP` to `LOCAL` before assigning the destination. Under this mode, the system should successfully generate a planned route.

---

### 5. Unable to Switch Operation Mode to AUTO

If the operation mode cannot be switched to `AUTO`, replace the files `operation_mode_transition_manager.param.yaml` and `operation_mode.cpp` with the corresponding versions under `autoware/src`, and then recompile the system. This modification enables forced mode transitions and allows the vehicle to begin driving.
