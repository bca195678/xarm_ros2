# Unity ROS-TCP-Connector + ROS2 Humble — Setup Guide
## Windows 11 + WSL2 Environment

---

## Overview

```
WSL2 (Ubuntu 22.04)                    Windows 11
─────────────────────                  ──────────
ROS2 Humble                            Unity Editor
xarm_ros2 nodes          TCP           ROS-TCP-Connector
ros-tcp-endpoint    ◄──────────────►   URDF Importer
publishes /joint_states                3D Lite6 model
                                       mirrors joint angles
```

Unity runs on Windows. ROS runs in WSL2. They talk over TCP via the WSL2 virtual network interface.

---

## Part 1 — WSL2 Side (ROS2)

### Step 1 — Install ros-tcp-endpoint

```bash
cd ~/dev_ws/src
git clone -b main https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git
cd ~/dev_ws
colcon build --packages-select ros_tcp_endpoint
source install/setup.bash
```

### Step 2 — Find your WSL2 IP

Unity on Windows needs to connect to this IP. It changes on every WSL2 restart.

```bash
hostname -I | awk '{print $1}'
```

Save this — you'll enter it in Unity. Example: `172.28.144.1`

**Tip:** Add this alias to your `~/.bashrc` so you can always check it quickly:
```bash
echo "alias wslip='hostname -I | awk \"{print \$1}\"'" >> ~/.bashrc
source ~/.bashrc
```

### Step 3 — Launch the TCP endpoint

```bash
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0
```

`0.0.0.0` means it listens on all interfaces — Unity on Windows can reach it via the WSL2 IP.

You should see:
```
[INFO] Starting server on 0.0.0.0:10000
```

**Leave this running** — it's the bridge between ROS and Unity.

---

## Part 2 — Generate the Lite6 URDF

The Lite6 uses xacro (a macro format), not plain URDF. Unity needs plain URDF. Convert it:

```bash
cd ~/dev_ws
source install/setup.bash

# Generate plain URDF from xacro
ros2 run xacro xacro \
  /home/chester/project/xarm_ros2/xarm_description/urdf/lite6/lite6.urdf.xacro \
  > /tmp/lite6.urdf

echo "Done: /tmp/lite6.urdf"
```

### Copy URDF and meshes to Windows

Unity accesses WSL2 files via `\\wsl$\Ubuntu` in Windows Explorer. No copying needed — just point Unity at the WSL2 path.

WSL2 path from Windows:
- URDF: `\\wsl$\Ubuntu\tmp\lite6.urdf`
- Meshes: `\\wsl$\Ubuntu\home\chester\project\xarm_ros2\xarm_description\meshes\lite6\`

---

## Part 3 — Unity Setup (Windows)

### Step 1 — Install Unity

- Download **Unity Hub** from unity.com
- Install **Unity 2022.3 LTS** (most stable, confirmed compatible with ROS-TCP-Connector)
- Create a new **3D (URP)** project

### Step 2 — Install packages via Package Manager

In Unity: **Window → Package Manager → + → Add package from git URL**

Add these two in order:

```
# 1. ROS-TCP-Connector
https://github.com/Unity-Technologies/ROS-TCP-Connector.git?path=/com.unity.robotics.ros-tcp-connector

# 2. URDF Importer
https://github.com/Unity-Technologies/URDF-Importer.git?path=/com.unity.robotics.urdf-importer
```

### Step 3 — Configure ROS connection

In Unity menu: **Robotics → ROS Settings**

Set:
- **ROS IP Address:** your WSL2 IP from Step 2 above (e.g. `172.28.144.1`)
- **ROS Port:** `10000`
- **Protocol:** ROS2

### Step 4 — Import the Lite6 URDF

1. In Unity **Project** panel, right-click → **Import New Asset**
2. Navigate to `\\wsl$\Ubuntu\tmp\lite6.urdf`
3. Also copy the meshes folder: `\\wsl$\Ubuntu\home\chester\project\xarm_ros2\xarm_description\meshes\lite6\` → drag into Unity Assets

Then right-click `lite6.urdf` in the Project panel → **Import Robot from URDF**

Unity will build the articulated robot hierarchy with all joints.

---

## Part 4 — Digital Twin Script

Create a new C# script in Unity called `Lite6JointSync.cs`:

```csharp
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Sensor;

public class Lite6JointSync : MonoBehaviour
{
    ROSConnection ros;

    // Drag each joint GameObject here in the Inspector
    // Order: joint1, joint2, joint3, joint4, joint5, joint6
    public ArticulationBody[] joints;

    void Start()
    {
        ros = ROSConnection.GetOrCreateInstance();
        ros.Subscribe<JointStateMsg>("/joint_states", OnJointState);
    }

    void OnJointState(JointStateMsg msg)
    {
        for (int i = 0; i < joints.Length && i < msg.position.Length; i++)
        {
            var drive = joints[i].xDrive;
            drive.target = (float)(msg.position[i] * Mathf.Rad2Deg);
            joints[i].xDrive = drive;
        }
    }
}
```

Attach this script to the root robot GameObject. Then drag the 6 joint ArticulationBodies into the `joints` array in the Inspector.

---

## Part 5 — Running It

### Terminal 1 — Start ROS + robot driver
```bash
# In WSL2
source ~/dev_ws/install/setup.bash
ros2 launch xarm_moveit_config lite6_moveit_gazebo.launch.py
```

### Terminal 2 — Start TCP bridge
```bash
# In WSL2
source ~/dev_ws/install/setup.bash
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0
```

### Unity
- Press **Play** in the Unity Editor
- The Lite6 model should start mirroring `/joint_states` in real time

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Unity can't connect | Check WSL2 IP — it changes on restart. Run `wslip` and update ROS Settings |
| Meshes missing (pink/white) | Make sure mesh files were imported into Unity Assets alongside the URDF |
| Joints not moving | Check joint names match between URDF and the `joints` array order in Inspector |
| Port blocked | Run `netsh advfirewall firewall add rule name="ROS" dir=in action=allow protocol=TCP localport=10000` in Windows PowerShell (admin) |
