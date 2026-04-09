# Lite6 + ROS2 — Ideas & Possibilities

A collection of ideas for what can be built with the Lite6 robot arm and ROS2.

---

## What Works Right Now (No Extra Hardware)

- **Motion planning with MoveIt** — plan collision-free paths, avoid obstacles, control joints or end-effector pose
- **Direct robot control** — move to Cartesian positions via service calls
- **MoveIt Servo** — real-time joystick/keyboard control of the arm
- **Gripper control** — standard, vacuum, and bio gripper supported
- **Trajectory execution** — plan and execute from Python/C++ code via `xarm_planner`

---

## Vision — With Intel RealSense D435i Camera

The repo already has a complete pick and place pipeline in `xarm_vision/d435i_xarm_setup/`.

### How object detection works (`find_object_2d`)
- Provide a reference photo of the object (e.g. `objects/1.png`)
- The package extracts keypoints (distinctive corners, edges, texture) from the reference image
- Each frame from the camera is scanned for matching keypoints
- When enough keypoints match, the object is considered found
- The D435i depth image converts the 2D pixel position to a 3D coordinate
- That 3D position is published as a TF frame (`object_1`) which the grasp code listens for
- Works best on objects with rich texture (labels, patterns, text) — plain colored objects are harder

### Full pick and place sequence (already coded)
1. Open gripper / turn off vacuum
2. Move to start pose above the table
3. Wait for camera to detect the object (up to 15 seconds)
4. Move 40mm above the detected object
5. Descend to the object
6. Activate vacuum gripper (Lite6) or close finger gripper
7. Lift up
8. Return to start pose

Two versions available:
- `findobj_grasp_moveit_planner.cpp` — uses MoveIt (collision-aware)
- `findobj_grasp_xarm_api.cpp` — uses direct API (simpler)

### Detection alternatives
| Method | Speed | GPU needed | Robustness |
|---|---|---|---|
| `find_object_2d` (feature matching) | 10-30 fps | No | Medium — needs textured objects |
| YOLOv8-nano | ~15 fps | No | Good |
| YOLOv8 full | 30-60 fps | Yes | Very good |
| VLM (GPT-4o, LLaVA, MoE) | 0.5-2 fps | Optional | Excellent — understands language |

---

## Using LLMs / AI with ROS

### VLM for object detection
- A Vision Language Model (VLM) can identify objects from camera images using natural language
- No reference images needed — "pick up the red cup" just works
- **Problem:** too slow for real-time tracking (500ms–2s per inference)
- **Solution:** use VLM for high-level understanding, fast classical vision for real-time tracking

### LLM as task planner (recommended approach)
- LLM acts as the "brain" that breaks down high-level instructions into steps
- Fast vision handles real-time detection
- Example:
  ```
  User: "Clean up the table"
  LLM: 1. Find the cup → 2. Move to shelf → 3. Find the bottle → ...
  ```
- Similar to Google RT-2, SayCan, Microsoft RoboFlamingo

### OpenCV
- Not currently used in this repo
- Could be added as a custom ROS node for color detection, edge detection, custom tracking
- Node subscribes to camera feed, publishes detected object position
- Existing grasp code picks up the position from there

---

## ROS + Unity3D

Unity has an official **ROS-TCP-Connector** package. Works well with Windows + WSL since Unity runs on Windows and ROS runs in WSL — connected via TCP over localhost.

### What you can build
- **Digital twin** — mirror real arm movements live in Unity in real time
- **Simulation before execution** — test movements in Unity before running on real arm
- **VR control** — control the arm with a VR headset (Meta Quest etc.), arm mirrors hand movements
- **AR overlay** — show safety zones, planned trajectories overlaid on real world
- **AI training data** — generate synthetic images of objects in Unity, train detection models, deploy on real robot

---

## ROS + Other Platforms

### Visualization & Digital Twin
| Platform | Notes |
|---|---|
| **Unity3D** | Best balance of ease and features, official ROS bridge |
| **Unreal Engine** | More photorealistic, heavier setup, popular in automotive |
| **NVIDIA Isaac Sim** | Best for AI training data, GPU-accelerated, native ROS2 support |
| **Blender** | Open source, good for rendering/recording demonstrations |

### Web & Remote Control
- **rosbridge + WebSocket** — control the robot from any web browser
- Build a dashboard in React/Vue showing live joint states, camera feed, send commands
- No ROS installation needed on the client — just a browser
- Easiest way to build a remote control interface

### Mobile
- **Flutter / React Native** — mobile app connecting to ROS via WebSocket
- Control arm from phone, show live camera feed and joint states

### AI & Machine Learning
- **PyTorch / TensorFlow** — train models on robot data, deploy object detection or grasp prediction
- **Isaac Sim** — photorealistic simulation for generating AI training data

### Industrial Hardware
- **Arduino / Raspberry Pi** — connect custom sensors (force sensors, conveyors, light curtains)
- **PLC** — bridge ROS with industrial PLCs (Siemens, Allen-Bradley) to integrate into a production line

---

## Recommended Next Steps by Difficulty

| Step | Difficulty | What you get |
|---|---|---|
| Web dashboard (rosbridge) | Easy | Browser-based control and monitoring |
| MoveIt Servo (keyboard/joystick) | Easy | Real-time arm control |
| ROS + Unity digital twin | Medium | Live 3D visualization, VR control |
| Pick and place with D435i | Medium | Full vision-guided grasping |
| ROS + PyTorch object detection | Medium | AI-powered grasping with YOLOv8 |
| LLM task planner | Medium | Natural language robot control |
| NVIDIA Isaac Sim | Hard | Advanced simulation and AI training |

---

## ROS vs UFACTORY Studio

| | UFACTORY Studio | ROS |
|---|---|---|
| Setup | None | Significant |
| Ease of use | Easy GUI |  Code-based |
| Connects to other systems | No | Yes |
| Computer vision | No | Yes |
| AI integration | No | Yes |
| Multi-robot | No | Yes |
| Best for | Quick tasks, simple automation | Complex systems, research, custom applications |

**Practical approach:** Use Studio for quick testing and simple tasks. Use ROS when you need to connect the arm to cameras, AI, web interfaces, or other hardware.

---

## OpenVLA

OpenVLA (Open Vision-Language-Action) is a 7B parameter model from Stanford/Berkeley. Unlike the LLM+vision pipeline approach, it is a single end-to-end model that takes a camera image + language instruction and outputs robot actions directly.

### Traditional pipeline vs OpenVLA

```
Traditional:
camera → YOLOv8 → LLM planner → MoveIt → arm

OpenVLA:
camera + "pick up the cup" → OpenVLA → arm
```

### Key facts
- Open source — weights on HuggingFace, free to use
- Trained on 970k real robot demonstrations (Open X-Embodiment dataset)
- Input: camera image + text instruction
- Output: end-effector delta poses or joint angles
- Fine-tunable on custom robots with LoRA (efficient, hours not days)
- Not trained specifically on Lite6 — fine-tuning needed for best results

### Hardware fit

| Hardware | Feasibility |
|---|---|
| A100 server | ✓ ideal — inference + fine-tuning |
| A30 server | ✓ good — 24GB VRAM handles inference + fine-tuning |
| Jetson Xavier | ✗ too slow for real-time (7B model) |

### Comparison to LLM pipeline

| | LLM pipeline | OpenVLA |
|---|---|---|
| Components | Many (detection + planner + MoveIt) | One model |
| Setup complexity | High | Medium |
| Generalization | Good | Very good |
| Custom objects | Retrain YOLOv8 | Fine-tune OpenVLA |
| Speed | Fast (small components) | Slower (7B model per step) |
| Hardware | Xavier handles it | Needs A30/A100 for real-time |
| Data needed | Less | Needs demonstrations |

### Integration work needed
OpenVLA outputs actions in its own format. A ROS2 bridge node needs to be built that:
1. Subscribes to `/camera/color/image_raw`
2. Sends image + instruction to OpenVLA (running on A30/A100)
3. Converts output action to ROS2 commands (`/ufactory/set_position` or MoveIt)

This bridge does not exist yet for xarm_ros2 — needs to be built.

### Fine-tuning path for Lite6
1. **Collect demonstrations** — teleoperate the Lite6 doing tasks, record camera + joint states
2. **Format data** — convert to OpenVLA's expected format (RLDS/LeRobot format)
3. **Fine-tune with LoRA** — run on A100/A30
4. **Deploy** — inference on A30/A100 server, actions sent to arm via ROS2 bridge

### Realistic implementation path
1. Get D435i camera + set up Xavier
2. Build ROS2 ↔ OpenVLA bridge node (runs on A30/A100)
3. Test with pretrained weights first (no fine-tuning needed to start)
4. Collect Lite6 demonstrations and fine-tune for better accuracy

---

## Hardware Available

### Jetson Xavier (model TBD — need to check)
- Fresh device, not yet set up
- Will serve as the robot brain — runs ROS2 nodes, camera processing, YOLOv8 inference
- Supports keyboard + mouse + HDMI monitor for direct interaction
- Day-to-day use: headless via SSH

**Key specs to check:**
- Which model: NX (8/16GB) or AGX (16/32GB)
- RAM amount
- Whether an NVMe SSD is already installed (eMMC alone is too small — 32GB fills up fast with JetPack + ROS2 + models)
- If no NVMe: buy a 256GB+ M.2 NVMe SSD (~$30-50) before setting up

**What it can run:**
| Component | Feasibility |
|---|---|
| ROS2 + robot driver | ✓ easy |
| YOLOv8-nano | ✓ fast |
| YOLOv8 full | ✓ good |
| LLM 7B (task planner) | ✓ slow (~2-3 tok/s) |
| VLM 7B (LLaVA etc.) | ✓ slow |
| LLM + VLM together | depends on RAM |

### A100 Server
- Run full YOLOv8 or fine-tune on custom objects
- Run large LLMs locally (LLaMA 3, Mistral 70B etc.) as task planner
- Run VLMs locally (LLaVA, InternVL) for open-vocabulary detection
- NVIDIA Isaac Sim for synthetic training data generation

### A30 Server
- 24GB VRAM
- Similar to A100 for most tasks
- Suitable for YOLOv8, medium LLMs (up to ~70B quantized), VLMs

---

## Target AI Pipeline (when D435i arrives)

```
D435i camera
      │
      ▼
Jetson Xavier
  - ROS2 node
  - YOLOv8 inference (fast, on-device)
  - publishes object 3D position
      │
      ▼
A100/A30 server (optional)
  - LLM task planner ("clean the table" → step-by-step plan)
  - or VLM for complex scenes
      │
      ▼
Lite6 arm
  - MoveIt executes motion
```

---

## Jetson Xavier Setup Plan

### Step 1 — Flash JetPack (one time only)

JetPack is NVIDIA's OS bundle for Jetson: Ubuntu + CUDA + cuDNN + TensorRT + all drivers.
Recommended version: **JetPack 5.x** (Ubuntu 20.04, most stable ecosystem).

Requires SDK Manager (GUI app) running on a machine with physical USB-C access to the Xavier.

**Option A — Use A100/A30 server (simplest)**
- If servers run native Ubuntu and Xavier can be physically connected via USB-C
- Install SDK Manager on the server, flash from there

**Option B — usbipd into WSL2 on Windows PC**
- Install `usbipd-win` on Windows (has `.msi` installer)
- Put Xavier in recovery mode, connect USB-C to PC
- In PowerShell (admin):
  ```powershell
  usbipd list
  usbipd bind --busid <ID>
  usbipd attach --wsl --busid <ID>
  ```
- In WSL: verify with `lsusb` (should show "NVIDIA Corp.")
- WSLg (Windows 11) supports GUI apps natively so SDK Manager runs in WSL directly
- More steps but avoids needing a separate machine

### Step 2 — After flashing
1. Connect keyboard + mouse + monitor directly to Xavier
2. Complete Ubuntu initial setup
3. Install ROS2 Humble (same steps as PC)
4. Add NVMe SSD if not already present
5. Switch to SSH for all further development

### Step 3 — Connect to PC over network
- Xavier and PC on same network (ethernet recommended for ROS2)
- SSH from WSL: `ssh chester@<xavier-ip>`
- ROS2 nodes run on Xavier, RViz/Gazebo visualization on PC
