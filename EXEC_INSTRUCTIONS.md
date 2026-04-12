# Lite6 ROS2 Execution Instructions

Operational reference for running the Lite6 with ROS2. For installation see `SETUP_INSTRUCTIONS.md`.

---

## Quick Reference

| Goal | Command |
|---|---|
| Real robot + MoveIt + RViz | `ros2 launch xarm_moveit_config lite6_moveit_realmove.launch.py robot_ip:=192.168.1.176` |
| Gazebo + MoveIt + RViz | `ros2 launch xarm_moveit_config lite6_moveit_gazebo.launch.py` |
| Real robot driver only | `ros2 launch xarm_api lite6_driver.launch.py robot_ip:=192.168.1.176` |

---

## Real Robot

### Launch (all-in-one)

```bash
ros2 launch xarm_moveit_config lite6_moveit_realmove.launch.py robot_ip:=192.168.1.176
```

Starts the driver, move_group, and RViz in one command. **Do NOT run the driver separately** — it will conflict.

### Direct control via service calls

Requires the driver to be running (either via the above or `lite6_driver.launch.py`).

```bash
# 1. Enable joints
ros2 service call /ufactory/motion_enable xarm_msgs/srv/SetInt16ById "{id: 8, data: 1}"

# 2. Set mode=0 (position control), state=0 (ready)
ros2 service call /ufactory/set_mode xarm_msgs/srv/SetInt16 "{data: 0}"
ros2 service call /ufactory/set_state xarm_msgs/srv/SetInt16 "{data: 0}"

# 3. Move to safe home position
ros2 service call /ufactory/set_position xarm_msgs/srv/MoveCartesian \
  "{pose: [250, 0, 300, 3.14, 0, 0], speed: 50, acc: 500, mvtime: 0}"
```

- Namespace is `/ufactory/` (NOT `/xarm/`)
- Always enable joints and set mode+state before sending motion commands
- Speed in mm/s, acceleration in mm/s², pose is [x, y, z, roll, pitch, yaw]

---

## Gazebo Simulation

### Launch (all-in-one)

```bash
ros2 launch xarm_moveit_config lite6_moveit_gazebo.launch.py
```

Launches Gazebo, MoveIt, and RViz together. Do NOT run `lite6_beside_table_gazebo.launch.py` separately — it is already included.

### Scene layout

```
         (open front — operator side)
              y = -0.50
   [-0.60]  [robot -0.2,-0.5]  [0.20]
     left                        right
     fence                       fence
              y = -0.94
         [  back fence  ]
```

- Robot spawned at: `x=-0.2, y=-0.5, z=1.021` (on table surface), rotated 90°
- Table center: `x=-0.1, y=-0.70` (0.50 × 0.36m surface)
- Fence panels: safety yellow, 1.5m tall, ~0.40m from robot base on all 3 sides

### Coordinate frames

MoveIt plans in the URDF `world` frame. The robot's URDF `world` link is spawned at Gazebo position `(-0.2, -0.5, 1.021)`, so:

```
MoveIt = Gazebo - spawn_pos
  x: Gazebo_x + 0.2
  y: Gazebo_y + 0.5
  z: Gazebo_z - 1.021
```

This offset applies when adding MoveIt collision objects that correspond to Gazebo world objects.

### MoveIt planning scene (fence)

The fence is automatically added to MoveIt's planning scene on launch via `spawn_fence_scene.py`. After ~5 seconds you should see:

```
[fence_scene_publisher]: Fence collision objects added to MoveIt planning scene.
```

The fence panels appear in RViz as collision objects. The planner will refuse paths that intersect them.

### Recovery — arm stuck against fence

If the arm executes into the fence (e.g. the fence was not yet in the planning scene when planning occurred):

1. Click **Stop** in the RViz MotionPlanning panel
2. Plan a new path back to a safe open position
3. Execute

If the arm is completely jammed, kill and relaunch everything.

### Stale Gazebo process

If launch fails with `Service /spawn_entity unavailable`:

```bash
pkill -9 gzserver; pkill -9 gzclient; pkill -9 gzmaster
```

Then relaunch.

---

## MoveIt — Plan & Execute

1. In RViz, use the **MotionPlanning** panel
2. Drag the interactive marker (orange ball) to the target pose
3. Click **Plan** — MoveIt computes a collision-free path
4. Click **Execute** — sends the trajectory to the controller
5. If planning fails, the arm does not move — adjust the target and try again

The fence collision objects prevent planning paths that would hit the fence panels.

---

## Simulation Files

| File | Purpose |
|---|---|
| `xarm_gazebo/worlds/table.world` | Gazebo world: table + fence panel models |
| `~/.gazebo/models/table/` | Local table model cache (prevents internet fetch hang on WSL2) |
| `xarm_gazebo/scripts/spawn_fence_scene.py` | Publishes fence as MoveIt collision objects on launch |

---

## Notes

- Controller overrun warnings (`missed its desired rate of 150 Hz`) are expected on WSL2 — no real-time kernel. Harmless.
- Gazebo Classic 11 only — supported on Ubuntu 22.04/Humble, NOT available on Ubuntu 24.04/Jazzy.
- The Lite6 has built-in firmware collision detection (configurable via xArm Studio) as a hardware-level safety layer independent of MoveIt.
