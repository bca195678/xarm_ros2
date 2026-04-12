# Lite6 ROS2 Setup Instructions

This file is intended to be read by Claude Code running inside WSL (Ubuntu-22.04).

## Environment

- Robot: UFACTORY Lite6
- Robot IP: 192.168.1.176
- Host OS: Windows 11 with WSL2 (Ubuntu-22.04)
- ROS2 distro: Humble (matches Ubuntu 22.04)
- This repo accessible in WSL at: `/home/chester/project/xarm_ros2`
- Branch: `humble`

---

## Step 1 — Set locale

```bash
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
```

---

## Step 2 — Add ROS2 apt repository

Check first: `ls /etc/apt/sources.list.d/ros2.list`

If missing:
```bash
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list
sudo apt update
```

---

## Step 3 — Install ROS2 Humble + MoveIt + ros2_control + Gazebo

Check first: `which ros2`

If missing:
```bash
sudo apt install -y ros-humble-desktop ros-humble-moveit ros-dev-tools
sudo apt install -y ros-humble-ros2-control ros-humble-ros2-controllers
sudo apt install -y ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control
```

---

## Step 4 — Initialize submodules

The `xarm_sdk/cxx` submodule must be initialized before building:

```bash
cd /home/chester/project/xarm_ros2
git submodule sync
git submodule update --init --remote
```

---

## Step 5 — Create workspace and install dependencies

```bash
mkdir -p ~/dev_ws/src
ln -sf /home/chester/project/xarm_ros2 ~/dev_ws/src/xarm_ros2

cd ~/dev_ws
source /opt/ros/humble/setup.bash

sudo rosdep init 2>/dev/null || true
sudo rosdep fix-permissions
rosdep update

rosdep install --from-paths src --ignore-src --rosdistro humble --simulate
```

The `--simulate` flag shows what will be installed. The actual install requires sudo, so run it manually:

```bash
sudo apt-get install -y \
  ros-humble-joint-state-publisher \
  ros-humble-moveit-servo \
  ros-humble-image-view \
  ros-humble-tf-transformations \
  ros-humble-find-object-2d
```

> Note: `sudo rosdep update` should be avoided — run `sudo rosdep fix-permissions` first, then `rosdep update` (no sudo).

---

## Step 6 — Build the workspace

```bash
cd ~/dev_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

Expected output: `Summary: 13 packages finished`

Deprecation warnings in `xarm_controller` and `xarm_planner` are harmless.

---

## Step 7 — Source in ~/.bashrc

```bash
grep -q "ros/humble/setup.bash" ~/.bashrc || echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
grep -q "dev_ws/install/setup.bash" ~/.bashrc || echo "source ~/dev_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## Step 8 — Verify

```bash
source ~/dev_ws/install/setup.bash
ros2 pkg list | grep xarm
```

Expected packages: `xarm_api`, `xarm_controller`, `xarm_description`, `xarm_gazebo`, `xarm_moveit_config`, `xarm_moveit_servo`, `xarm_msgs`, `xarm_planner`, `xarm_sdk`, `d435i_xarm_setup`

---

## Known Fixes Applied to This Repo

These bugs exist in the `humble` branch and have already been patched. If you re-clone, you will need to reapply them.

### Fix 1 — Remove obsolete header include

`hardware_interface/visibility_control.h` was removed in newer ros2_control releases and is missing on both Humble and Jazzy. Remove the include from:

- `xarm_controller/include/xarm_controller/hardware/uf_robot_system_hardware.h` (line 25)
- `xarm_controller/include/xarm_controller/hardware/bak_uf_robot_fake_system_hardware.h` (line 23)

Delete this line from both files:
```cpp
#include "hardware_interface/visibility_control.h"
```

### Fix 2 — Enable OMPL planning plugin

The code that registers the OMPL planner was commented out in `uf_ros_lib`. Without this, MoveIt shows "NO PLANNING LIBRARY LOADED" and cannot plan any motion.

**File:** `uf_ros_lib/uf_ros_lib/moveit_configs_builder.py`

Find the block starting with `# # Special rule to add ompl planner_configs` (around line 711) and uncomment it:

```python
if 'ompl' in self.__moveit_configs.planning_pipelines:
    ompl_config = self.__moveit_configs.planning_pipelines['ompl']
    if os.environ.get('ROS_DISTRO', '') > 'iron':
        ompl_config.update({
            'planning_plugins': ['ompl_interface/OMPLPlanner'],
            'request_adapters': [
                'default_planning_request_adapters/ResolveConstraintFrames',
                'default_planning_request_adapters/ValidateWorkspaceBounds',
                'default_planning_request_adapters/CheckStartStateBounds',
                'default_planning_request_adapters/CheckStartStateCollision',
            ],
            'response_adapters': [
                'default_planning_response_adapters/AddTimeOptimalParameterization',
                'default_planning_response_adapters/ValidateSolution',
                'default_planning_response_adapters/DisplayMotionPath',
            ],
        })
    else:
        ompl_config.update({
            'planning_plugin': 'ompl_interface/OMPLPlanner',
            'request_adapters': """default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints""",
            'start_state_max_bounds_error': 0.1,
        })
```

Also apply the same uncomment in `uf_ros_lib/uf_ros_lib/substitutions/planning_pipelines.py` around line 126.

### Fix 3 — Gazebo spawn entity QoS mismatch

`spawn_entity.py` subscribes to `/robot_description` with `volatile` QoS durability, but `robot_state_publisher` publishes it with `transient_local` (latched). ROS2 treats these as incompatible, so the spawn node never receives the message and the robot silently fails to appear in Gazebo — only the table is visible.

**File:** `xarm_gazebo/launch/_robot_beside_table_gazebo.launch.py` (line ~271, in the `else` / Gazebo Classic branch)

Write the URDF to a temp file and pass it via `-file` instead of subscribing to the topic:

```python
# Before
arguments=[
    '-topic', 'robot_description',
    ...
]

# After
urdf_file = tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False)
urdf_file.write(robot_description['robot_description'])
urdf_file.close()
arguments=[
    '-file', urdf_file.name,
    ...
]
```

This passes the URDF content directly via a temp file instead of subscribing to the topic, bypassing the QoS issue entirely.

---

## How to Run

### Launch MoveIt + RViz (real robot)

```bash
ros2 launch xarm_moveit_config lite6_moveit_realmove.launch.py robot_ip:=192.168.1.176
```

This single command starts the driver, move_group, and RViz. Do NOT run the driver separately in another terminal — it will conflict.

### Launch Gazebo simulation (with MoveIt + RViz)

```bash
ros2 launch xarm_moveit_config lite6_moveit_gazebo.launch.py
```

This single command launches Gazebo, MoveIt, and RViz together. Do NOT run `lite6_beside_table_gazebo.launch.py` separately — it is already included.

Gazebo Classic 11 is supported on Ubuntu 22.04/Humble.

> **WSL2 note:** On first run, Gazebo will hang with a black window trying to download `model://table` from the internet. Pre-cache it locally to fix this:
> ```bash
> mkdir -p ~/.gazebo/models/table/materials/scripts
> ```
> Then populate `~/.gazebo/models/table/model.config`, `model.sdf`, and `materials/scripts/table.material` with the standard Gazebo table model. Once cached, Gazebo loads immediately.

### Control via service calls (without MoveIt)

If you just want to send motion commands directly:

**Terminal 1:**
```bash
ros2 launch xarm_api lite6_driver.launch.py robot_ip:=192.168.1.176
```

**Terminal 2:**
```bash
# Enable joints
ros2 service call /ufactory/motion_enable xarm_msgs/srv/SetInt16ById "{id: 8, data: 1}"

# Set mode=0 (position control), state=0 (ready)
ros2 service call /ufactory/set_mode xarm_msgs/srv/SetInt16 "{data: 0}"
ros2 service call /ufactory/set_state xarm_msgs/srv/SetInt16 "{data: 0}"

# Move to safe home position (x=250mm, y=0mm, z=300mm, pointing down)
ros2 service call /ufactory/set_position xarm_msgs/srv/MoveCartesian \
  "{pose: [250, 0, 300, 3.14, 0, 0], speed: 50, acc: 500, mvtime: 0}"
```

---

## Notes

- The Lite6 uses the `/ufactory/` namespace (NOT `/xarm/`)
- Always enable joints and set mode+state before sending motion commands
- Speed is in mm/s, acceleration in mm/s², pose is [x, y, z, roll, pitch, yaw]
- Controller overrun warnings (`missed its desired rate of 150 Hz`) are expected on WSL2 — WSL2 has no real-time kernel. They are harmless.
- Gazebo Classic 11 is supported on Ubuntu 22.04 (Humble). It is NOT available on Ubuntu 24.04 (Jazzy).
