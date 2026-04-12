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

### Setup process

**Stage 1 — Environment (on A100/A30 server)**
```bash
conda create -n openvla python=3.10
conda activate openvla
pip install torch torchvision
pip install transformers accelerate
pip install openvla
```

**Stage 2 — Download model weights (~15GB from HuggingFace)**
```bash
huggingface-cli download openvla/openvla-7b
```

**Stage 3 — Run inference server**
- Exposes an API endpoint on the server
- Accepts: camera image (JPEG/PNG) + text instruction
- Returns: action (joint deltas or end-effector pose)

**Stage 4 — Build ROS2 bridge node**
```
/camera/color/image_raw  ──►  bridge node  ──►  OpenVLA server
                                   │
                                   ▼
                          /ufactory/set_position
```
This node does not exist yet for xarm_ros2 — needs to be built.

### Network topology

Lite6 and D435i connect to the PC. The A100/A30 server is on a different subnet.

```
  Subnet A (desk)                  Subnet B (server room)
  ───────────────                  ──────────────────────

  ┌─────────────────┐              ┌─────────────────┐
  │   D435i Camera  │              │  A100/A30       │
  │   (USB 3.0)     │              │  Server         │
  └────────┬────────┘              │  OpenVLA 7B     │
           │                       └────────┬────────┘
           ▼                                │
  ┌─────────────────┐   REST API            │
  │   Windows PC    │ ◄─────────────────────┘
  │   WSL2          │  (cross-subnet,
  │                 │   HTTP works if routing exists)
  │  ROS2 nodes     │
  │  camera driver  │
  │  bridge node    │
  └────────┬────────┘
           │ Ethernet (xArm protocol)
           ▼
  ┌─────────────────┐
  │   Lite6 Arm     │
  └─────────────────┘
```

Cross-subnet API call works as long as:
- PC can ping the server (`ping <server-ip>`)
- Server firewall allows incoming connections on the API port

If firewall blocks direct access, use an SSH tunnel:
```bash
# Forward server port 8000 to localhost on PC
ssh -L 8000:localhost:8000 user@<server-ip>
```
Then bridge node calls `http://localhost:8000` instead of the server IP directly.

### Jetson Xavier — is it needed for OpenVLA?

No, not strictly. For OpenVLA the PC can take the Jetson's role:
- Camera plugs into PC via USB
- ROS2 bridge runs on PC (WSL2)
- PC calls OpenVLA on the server

Jetson becomes useful when:
- System needs to run standalone without a PC
- Everything self-contained next to the robot
- Adding more on-device processing (e.g. YOLOv8 running locally on Xavier)

**Stage 5 — Fine-tuning (optional, after camera arrives)**
1. Collect demonstrations — teleoperate Lite6, record camera + joint states
2. Format into LeRobot/RLDS format
3. Run LoRA fine-tuning on A100/A30
4. Swap pretrained weights for fine-tuned weights

**What you can do right now (without camera):**
- Set up server environment (Stage 1)
- Download weights (Stage 2)
- Test with static images to verify model responds correctly

**What needs the camera:**
- Live inference (Stage 3 + 4)
- Collecting demonstrations for fine-tuning (Stage 5)

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

---

## OpenVLA — Deeper Notes

### How the model actually works

OpenVLA is built on Prismatic VLM fine-tuned for action prediction. Actions are tokenized as text tokens.

```
Input:
  - Image: 224×224 RGB (single frame, not video)
  - Text: "In: What action should the robot take to {instruction}?"

Output:
  - 7 numbers decoded from text tokens
  - Format: [Δx, Δy, Δz, Δroll, Δpitch, Δyaw, gripper_open]
  - These are end-effector deltas, not joint angles
```

For Lite6 (6-DOF), the 7th dimension (gripper) maps naturally to the vacuum gripper on/off.

### Control frequency reality check

| Hardware | Inference time | Control Hz |
|---|---|---|
| A100 (80GB) | ~80ms | ~12 Hz |
| A30 (24GB) | ~120–150ms | ~6–8 Hz |

Most manipulation tasks need 5–10 Hz minimum. A30 is borderline — usable for slow pick-and-place.
Network hop (PC → server → PC) adds ~5–20ms on same LAN. Tolerable.

### OpenVLA-OFT (newer, preferred over base model)

OpenVLA-OFT (Optimized Fine-Tuning) improves on the original:
- **Parallel decoding** instead of autoregressive token generation → ~6× faster inference
- **Action chunking** (predicts multiple steps ahead, like ACT/Diffusion Policy)
- Continuous action head instead of tokenized actions → smoother motion
- Better fine-tuning efficiency with LoRA

Use this over base OpenVLA if starting fresh.
HuggingFace: `openvla/openvla-oft-pretrained-bridge`

### ROS2 bridge node design

```
xarm_openvla_bridge/
├── bridge_node.py          # main ROS2 node — 8 Hz control loop
├── openvla_client.py       # HTTP client to inference server on A30
├── action_executor.py      # converts EEF deltas → /ufactory/set_position
└── config/
    └── bridge_params.yaml  # server URL, control rate, safety limits
```

Safety layer required — raw deltas from pretrained model (not fine-tuned on Lite6) can be large:
- Per-axis delta clamp (e.g. max 20mm per step)
- Workspace bounding box check before execution
- Emergency stop topic subscriber

### Fine-tuning data — what to record per timestep

- `/camera/color/image_raw` — compressed JPEG
- `/ufactory/robot_states` — current joint positions + EEF pose
- Timestamp + episode ID

LeRobot format (HuggingFace standard): Parquet files for actions/observations, video files for images, `meta/info.json`.
Use `lerobot` Python package for dataset creation. Need a ROS2 bag → LeRobot converter.

**How many demos needed:** 50–200 demos per task with LoRA. Start with one simple repeatable task.

### Smaller/faster alternatives to OpenVLA

| Model | Size | Notes |
|---|---|---|
| OpenVLA-OFT | 7B | Faster inference, better fine-tuning |
| Octo | ~90M | Transformer, runs on Jetson Xavier |
| ACT | ~80M | Action chunking, works well with 50 demos |
| Diffusion Policy | ~100M | State-of-the-art for dexterous tasks |
| SmolVLA | 450M | Flow-matching (π0 architecture), comparable to OpenVLA |

**Octo** is useful if latency matters more than accuracy — runs on Jetson, trained on Open X-Embodiment, some research groups have ROS2 bridges already.

---

## Octo

Octo is a transformer-based generalist robot policy from UC Berkeley, trained on 800k trajectories from the Open X-Embodiment dataset. Published at RSS 2024. Much smaller and faster than OpenVLA, and Jetson-compatible.

GitHub: `https://github.com/octo-models/octo`  
HuggingFace: `rail-berkeley/octo-base-1.5`, `rail-berkeley/octo-small-1.5`

### Model sizes

| Variant | Parameters | Best for |
|---|---|---|
| Octo-Small-1.5 | 27M | Jetson Xavier, fastest inference |
| Octo-Base-1.5 | 93M | A30/A100, better accuracy |

### Input / output

```
Input:
  - RGB image (primary camera + optional wrist camera)
  - Proprioception (current joint positions)
  - Language instruction OR goal image

Output:
  - 4 actions per inference call (action chunking)
  - Each action: [Δx, Δy, Δz, Δroll, Δpitch, Δyaw, gripper] — EEF deltas
```

For Lite6: 6D EEF deltas map to `/ufactory/set_position`, gripper maps to `/ufactory/set_vacuum_gripper`.

### Control frequency

| Hardware | Hz |
|---|---|
| A100 | ~15–20 Hz |
| A30 | ~10–13 Hz |
| Jetson Xavier (Octo-Small) | ~1–5 Hz |

A30 is comfortably real-time. Octo-Small on Jetson is borderline but feasible for slow pick-and-place.

### Install (JAX-based)

```bash
conda create -n octo python=3.10
conda activate octo
git clone https://github.com/octo-models/octo.git
cd octo
pip install -e .
pip install "jax[cuda12_local]==0.4.30"
```

### Inference

```python
from octo.model.octo_model import OctoModel
import jax

model = OctoModel.load_pretrained("hf://rail-berkeley/octo-base-1.5")
task = model.create_tasks(texts=["pick up the cup"])

observation = {
    "image_primary": rgb_image,   # numpy (H, W, 3)
    "proprio": joint_state,        # current joint positions
}

actions = model.sample_actions(observation, task, rng=jax.random.PRNGKey(0))
# returns shape (4, 7) — 4 steps ahead, execute all 4 before resampling
```

### Fine-tuning for Lite6

- 50–200 demos per task (same requirement as OpenVLA but fine-tunes faster)
- Hours on A100/A30 (vs. 10–15h for OpenVLA)
- Same ROS2 bag recording pipeline as OpenVLA demos

```bash
python scripts/finetune.py \
  --config.pretrained_path=hf://rail-berkeley/octo-base-1.5 \
  --config.dataset_path=/path/to/your/demos \
  --config.task_type=language_conditioned \
  --config.finetuning_mode=head_mlp_only
```

Fine-tuning modes: `head_only` (fastest, freeze backbone), `head_mlp_only` (recommended), `full` (best results, 100+ demos).

### ROS2 bridge node design

No official bridge exists — same situation as OpenVLA. Structure is nearly identical:

```
xarm_octo_bridge/
├── bridge_node.py          # main ROS2 node — 10 Hz control loop
├── octo_client.py          # HTTP client to inference server on A30
├── action_executor.py      # converts EEF deltas → /ufactory/set_position
└── config/
    └── bridge_params.yaml  # server URL, control rate, safety limits
```

```
/camera/color/image_raw  ──►  octo_bridge_node  ──►  Octo server (A30)
/joint_states            ──►       │
                                   ▼
                          /ufactory/set_position
                          /ufactory/set_vacuum_gripper
```

### Octo vs OpenVLA

| | Octo | OpenVLA |
|---|---|---|
| Size | 27–93M | 7B |
| Speed | 10–20 Hz | 6–8 Hz |
| Fine-tune time | Hours | ~10–15h |
| Demos needed | 50–200 | 50–500 |
| Runs on Jetson | Yes (Small) | No |
| Zero-shot quality | Good | Better |
| Action output | Continuous (diffusion) | Tokenized |

**Recommendation:** Start with Octo for faster iteration and Jetson compatibility. Switch to OpenVLA or π0.5 if zero-shot generalization becomes the bottleneck.

### Implementation path

1. Set up Octo environment on A30 (Stage 1 above)
2. Test inference with static images — no camera or arm needed
3. Build ROS2 bridge node (reuse OpenVLA bridge design, swap model client)
4. Camera arrives: wire up live inference loop
5. Collect 50–200 Lite6 demos → fine-tune on A30

---

## VLA Landscape Beyond OpenVLA

### π0 / π0.5 — Physical Intelligence (best capability, self-hosted)

Open-source weights on GitHub (`Physical-Intelligence/openpi`). No cloud API — but runs on the A30.

Why it's better than OpenVLA:
- **Flow-matching architecture** instead of token prediction → smoother, continuous actions
- **50 Hz control rate** vs OpenVLA's ~8 Hz
- Trained on 8 different robot embodiments
- π0.5 (April 2025) adds open-world generalization

```bash
# Setup on A30
conda create -n pi0 python=3.10
conda activate pi0
git clone https://github.com/Physical-Intelligence/openpi
pip install -e openpi
huggingface-cli download physical-intelligence/pi0
```

Fine-tuning path: same as OpenVLA — collect demos, convert to LeRobot format, run LoRA on A30.

**Enterprise API:** Physical Intelligence is building a commercial API. Contact `pi.website` for enterprise/research access if self-hosting is not ideal.

### Gemini Robotics-ER — Google DeepMind (cloud API, production)

Built on Gemini 2.0, announced March 2025. The only production cloud VLA API currently available.

- Available via **Google AI Studio** and **Vertex AI**
- Handles dexterous tasks: origami folding, packing bags
- Tested on ALOHA and bi-arm Franka — not yet documented for Lite6/xArm
- Fine-tuning available with ~50–100 demos
- Output: motor commands and trajectory/grasp predictions

**Input/output format:** RGB image + natural language → motor commands. Mapping to Lite6's `/ufactory/set_position` requires a translation layer (same as OpenVLA bridge).

To get access: apply at `ai.google.dev` / Vertex AI, or contact Google Cloud sales for robotics partnership.

### Full VLA comparison

| Model | Cloud API | Size | Control Hz | Best for |
|---|---|---|---|---|
| Gemini Robotics-ER | ✓ Vertex AI | Large | TBD | Cloud-first, no GPU owned |
| π0.5 | ✗ self-hosted | 7B+ | 50 Hz | Best capability, have A30 |
| OpenVLA-OFT | ✗ self-hosted | 7B | ~8 Hz | Good starting point |
| SmolVLA | ✗ self-hosted | 450M | fast | Jetson-compatible |
| Octo | ✗ self-hosted | 90M | fast | Lightweight, Jetson |

---

## Gemini 2.5 Pro as Task Planner (Cloud API — Available Today)

This is the fastest path to get working before D435i arrives. Uses Gemini as the "brain" for high-level planning while local components handle real-time execution.

### Architecture

```
Cloud (one API call per high-level instruction):
  Gemini 2.5 Pro
  Input:  current camera frame + "clean up the table"
  Output: structured JSON plan → ["find cup", "grasp cup", "move to shelf", ...]

Local (real-time, on Jetson/PC):
  YOLOv8  → object detection + 3D position
  MoveIt  → motion execution
  Bridge  → converts plan steps to /ufactory/set_position calls
```

Gemini fires once per high-level instruction, not every control cycle. The arm moves at full speed locally. This avoids the 1–2s latency problem of cloud models.

### What Gemini 2.5 Pro adds over a simpler planner

- Understands spatial relationships from image ("the red cup near the edge")
- Can count objects, read labels on items
- Reasons about task ordering and dependencies
- Handles novel instructions without retraining
- Can ask for clarification if instruction is ambiguous

### ROS2 bridge node — planned design

```
/camera/color/image_raw  ──►  gemini_planner_node
/detected_objects         ──►  (JSON: {"cup": [x,y,z], ...} from YOLOv8)
/gemini_planner/task      ──►  task instruction (std_msgs/String)

gemini_planner_node:
  1. On new task: capture frame + call Gemini API
  2. Parse JSON plan returned by Gemini
  3. For each step: look up object position, call /ufactory/set_position
  4. Vacuum gripper: /ufactory/set_vacuum_gripper

Gemini prompt output schema:
  {
    "steps": [
      {"action": "pick",    "object": "cup",   "reason": "..."},
      {"action": "place",   "target": "shelf",  "reason": "..."}
    ],
    "requires_clarification": false
  }

Valid actions: pick | place | move_to | open_gripper | close_gripper | scan
```

### Key xarm_ros2 service facts (verified from source)

```
# Cartesian move (mm + radians)
/ufactory/set_position   →  xarm_msgs/srv/MoveCartesian
  req.pose = [x, y, z, roll, pitch, yaw]  # mm, radians
  req.speed = 160.0   # mm/s
  req.acc   = 1000.0
  req.wait  = True

# Vacuum gripper (Lite6 default)
/ufactory/set_vacuum_gripper  →  xarm_msgs/srv/VacuumGripperCtrl
  req.on   = True/False
  req.wait = True

# Robot init sequence (required before moves)
/ufactory/set_mode   →  xarm_msgs/srv/SetInt16  (data=0 for position mode)
/ufactory/set_state  →  xarm_msgs/srv/SetInt16  (data=0 for ready)

# TCP offset for Lite6 vacuum gripper
gripper_tcp_offset = [0, 0, 61.1, 0, 0, 0]  # mm

# Lite6 typical start pose
start_pose = [250, 0, 200, 3.14159, 0, 0]  # x=250mm, facing down
# Hover above object: z + 40mm
# Grasp position:     z - 10mm
```

### Cost estimate

| Service | Usage | Cost |
|---|---|---|
| Gemini 2.5 Pro | ~1 call per task | ~$0.01–0.03/call |
| Gemini Flash (faster, cheaper) | ~1 call per task | ~$0.001/call |
| Gemini Robotics-ER | per inference | TBD (preview) |

At one task per minute during development: well under $5/day.

### Recommended paid stack

| Layer | Service | Notes |
|---|---|---|
| High-level reasoning | Gemini 2.5 Pro API | Available today |
| Direct action (cloud VLA) | Gemini Robotics-ER | Apply for early access |
| Fallback local policy | π0.5 on A30 | Best capability, self-hosted |
| Object detection | YOLOv8 on Jetson | Fast, on-device |

### Implementation sequence

1. **Now (no camera):** Sign up for Google AI Studio, test Gemini 2.5 Pro with a photo of the workbench — ask it to plan a pick-and-place task
2. **Apply for access:** Gemini Robotics-ER via Vertex AI; contact Physical Intelligence about π0 enterprise API
3. **Camera arrives:** Wire up YOLOv8 → object positions topic; build Gemini planner bridge node
4. **Benchmark:** Gemini 2.5 Pro planner + YOLOv8 vs Gemini Robotics-ER direct action
5. **Fine-tune:** Collect Lite6 demos → LoRA fine-tune π0.5 on A30 for dexterous tasks
