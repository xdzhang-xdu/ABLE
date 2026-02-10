## Apollo Troubleshooting Guide

### 1. Correction and Generation of CARLA Town Maps in XODR Format

First, maps generated using the iMAP tool exhibit an approximate offset of 166,021 units along the x-axis. Therefore, the value of `x_0` in the header of the XODR file must be manually adjusted. This process may require repeated fine-tuning in Dreamview.

Second, the script `xodr2bin.sh` is used to automatically generate the three types of map files required by Apollo. This process depends on the iMAP tool and must be executed within Apollo’s Docker environment.

---

### 2. Traffic Lights Not Displayed in Dreamview or Not Detected by Apollo

To resolve issues where traffic lights are not displayed in Dreamview or cannot be detected by Apollo, the `signal` entries and the corresponding `overlap` entries must be added to the `base_map.txt` file. Afterward, the `sim_map` and `routing_map` files should be regenerated.

The `signal` entry represents the traffic light entity. Its identifier must exactly match the traffic light ID contained in the messages published by the bridge to the Cyber node at `apollo/perception/traffic_light`.

The `overlap` entry defines the road segments affected by the traffic light. The start and end ranges of the affected road segments (specified by the `s` parameter) must be adjusted accordingly. These overlap relationships must be added to both the corresponding road segments and traffic lights.

---

### 3. Performance and Control Issues

#### 3.1 Startup Stuttering in Apollo

This issue is characterized by continuous flickering and distortion of the planned blue trajectory, accompanied by repeated acceleration and braking while the vehicle remains stationary (as indicated by the dashboard in the upper-right corner of Dreamview). Under these conditions, the vehicle cannot start normally. However, once an initial velocity is manually assigned, the vehicle can continue moving.

The root cause is frequent replanning of the driving trajectory. This can be observed in the planning logs, particularly in the file `trajectory_stitcher.cc`. By commenting out the timestamp-related replanning logic and recompiling Apollo, stable trajectory planning can be restored. The planned path becomes stable and no longer flickers, enabling normal vehicle startup.

It is hypothesized that this issue arises from inconsistencies in timestamp calculations between the bridge and Apollo, which trigger repeated replanning.

---

#### 3.2 Trajectory Deviation During Turning

During turning maneuvers, Apollo may fail to maintain the vehicle near the center of the lane, frequently encroaching on adjacent lanes. This behavior is partly caused by erroneous acceleration data and excessively high cornering speeds.

To address this issue, incorrect code in the bridge’s IMU module must be corrected. Specifically, the assignments of the x- and y-axis acceleration values were reversed and should be swapped. In addition, the maximum acceleration limit along the x-axis should be removed.
