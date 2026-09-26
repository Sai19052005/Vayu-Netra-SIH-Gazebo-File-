# VĀYU-NETRA — Autonomous SAR Simulation

Team AEROINDIA · Ubuntu24.04 / ROS2 Jazzy / Gazebo Harmonic / PX4 SITL

**Delivery status: software-tested source package; Ubuntu/ROS/Gazebo flight acceptance remains open.**
The authoring host is Windows without WSL, ROS or Gazebo. We did not build the ROS
workspace or fly PX4 here. Do not present this ZIP as a flight-validated simulator.
The exact limitations and actual test records are in [validation.md](docs/validation.md).

## 1. Overview

A modular, offline SAR demonstrator with a PX4 X500 physics model, custom disaster
world, feedback-driven search, clearly labelled simulated perception, an optional
real YOLOv8n adapter, configurable P0–P4 prioritization, targeted reinspection,
local mapping, a browser dashboard and JSON/HTML/GeoJSON reports.

The earlier HTML guide was reviewed, not patched. Its coordinate-driven detector,
fixed inference time, fabricated temperatures, permissive startup sequencing and
incomplete dashboard are replaced. See [architecture.md](docs/architecture.md).

## 2. What it demonstrates

- Six humanoid scene targets and six hazards: fire, smoke, flood, debris, structure and power line.
- Search → observe → prioritize → reinspection → new observation → update → resume.
- Takeoff, search, controlled return at survey altitude, native PX4 landing and disarm verification.
- RGBD rendering and ROS image interfaces; separate deterministic thermal-evidence fixture.
- Local dashboard without map services, external fonts, cloud APIs or internet during a mission.
- Separation of scenario-oracle results from actual neural inference.

## 3. Supported environment and exact source versions

| Component | Target / pin |
|---|---|
| OS / architecture | Ubuntu24.04 LTS, x86_64 |
| ROS / Python | ROS2 Jazzy; Ubuntu system Python3.12 |
| Gazebo | Harmonic, gz-sim8 |
| ROS–Gazebo integration | `ros-jazzy-ros-gzharmonic`; ROS package `ros_gz_bridge` |
| PX4 | v1.17.0, `d6f12ad1c4f70ad3230afd7d86e971421e02fef4` |
| px4_msgs | release/1.17 snapshot, `86d8239e962f6939e05c3737784f60c02fa884db` |
| Micro XRCE-DDS Agent | v2.4.3, `73622810d984349b80bbac0ef55fc0b694d62222` |
| Gazebo model submodule | `b6127f4ec20de867e215fb5f78ae88b80f371909` |
| Optional YOLO environment | Ultralytics8.3.203, CPU Torch2.6.0/Torchvision0.21.0, NumPy1.26.4 |

These are source pins, not a claim that this combination was runtime-tested here.
`verify_contract.py` compares the actual wire definitions, not merely branch names.
ROS/Gazebo apt patch versions are recorded after setup, not frozen to an apt snapshot.
Therefore reproducibility is source-level with recorded installed dependencies,
not an identical binary image. See `dependencies.lock.json`.

## 4. Prerequisites

Use the stated Ubuntu24.04 laptop with Jazzy installed and functional desktop
OpenGL/EGL. Internet and sudo are needed for installation only. Reserve disk space
for private PX4, model and Agent source/build trees; use `JOBS=2` to limit compile RAM.
Close other agents on UDP8888 and applications on TCP8080.

The scripts use a private `vendor/PX4-Autopilot` checkout. They preserve your
existing installed PX4 checkout. No flight-controller USB/serial connection is used.
Do not connect this SITL-only launcher to a real aircraft.

## 5. Installation

On Ubuntu, extract with an archive tool that preserves Unix modes, or use:

```bash
unzip vayu_netra_sar_sim_ubuntu24_jazzy_harmonic.zip
cd vayu_netra_sar_sim
./setup.sh
```

If the archive was extracted on Windows, restore executable permissions once:
`chmod +x ./*.sh scripts/*.sh`.

Setup installs the Harmonic-specific ROS integration and build dependencies, checks
out exact source revisions and creates an isolated PX4 Python environment. It does
not install Python libraries into the system interpreter. If Jazzy or its package
repositories are absent, it stops with a specific fix; see troubleshooting.

## 6. Environment check

```bash
./check_environment.sh
```

Before the first build, missing generated binaries/packages are expected; run the
build next. After build, every required check must pass. Checks include OS, Python,
ROS, Gazebo major version, apt integration package, colcon, package discovery,
source/message pins, executable paths and display availability. Results are saved
in `validation/environment.json`; failed requirements return a nonzero exit code.

## 7. Build

```bash
./build.sh
```

This builds the Agent locally, PX4 SITL and the two ROS packages; runs software tests;
verifies installed entry points; then runs environment validation. No system Agent
installation is required. Build logs from colcon remain under `log/`.

## 8. Quick demo

```bash
./run_demo.sh
```

Starts the Agent, waits for the actual Gazebo world service, attaches PX4 to the
world's `vayu_netra_0`, then launches ROS nodes. Flight waits for valid feedback,
camera flow and application readiness. Startup uses readiness gates rather than a
fixed assumption that a15-second sleep was enough.

Open **http://127.0.0.1:8080**. Quick mode is designed for approximately2–4minutes
of mission simulation time; actual laptop real-time factor and startup vary.
The pure kinematic fixture completed it in128.2 simulated seconds. That is not a
PX4/Gazebo timing benchmark.

## 9. Full mission

```bash
./run_full_mission.sh
```

Expands the search bounds and tightens line spacing. Both missions use the same
world and all six survivors. Configuration lives in installed/source `config/quick.yaml`
and `config/full.yaml`; change source config and rerun build to refresh installation.
Files are YAML using the JSON subset, supported by both YAML and Python fallback loaders.

## 10. Software test and presentation fallback

Fast deterministic test, no ROS/Gazebo required:

```bash
./run_test_mode.sh
```

Visible backup using the same mission engine and local dashboard:

```bash
./run_test_mode.sh --realtime --serve
```

ROS-node graph test without Gazebo/PX4:

```bash
./run_test_mode.sh --ros
```

The ROS fixture publishes a clock, kinematic flight feedback and blank image frames.
It is explicitly synthetic, not camera inference or flight dynamics. The portable
test runs the core classes directly; use `--ros` when ROS-node testing is required.
No battery values are invented in either software fixture.

## 11. Dashboard and visualization

The local dashboard shows state, altitude, speed, simulated PX4 battery if available,
unique incident counts, priority, observation counts, path, planned grid, footprint
coverage estimate and mission events. It is read-only and bound to loopback.

For camera pixels, use Gazebo's sensor viewer or a ROS image viewer on
`/vayu/camera/image`. The web dashboard currently shows the map, not a live video pane.
RViz markers are on `/vayu/map_markers`; an RViz config is included under `rviz/sar.rviz`.

## 12. Expected output

Every flight launch creates a new `runs/YYYYMMDD-HHMMSS/` folder containing:

- `agent.log`, `gazebo.log`, `px4.log`, `ros.log` and optional GUI log.
- `mission_report.json`, `mission_report.html`, `incidents.geojson`.
- A fresh PX4 run directory and logs, separate from other runs.

Reports are refreshed during operation and marked interrupted on orderly shutdown
before completion. They include runtime path length, sim timestamps, coverage basis,
latest incident observations/counts, priority changes and reinspection events.
GeoJSON includes only objects with a local position, never unlocalized pixel boxes.
Track count is not a guaranteed count of unique physical people in real YOLO mode.

## 13. Troubleshooting

See [troubleshooting.md](docs/troubleshooting.md). Inspect the first failing process
log instead of repeatedly relaunching. Wrong commits, missing topics, invalid
position estimates or arming failures must be corrected before claiming acceptance.

## 14. Common errors

Wrong ROS distribution, missing `ros-jazzy-ros-gzharmonic`, a moving px4_msgs branch,
missing `_v1` PX4 topic suffixes, missing world resources, a paused clock and occupied
ports are checked or described with fixes. Headless rendering still needs a usable
graphics driver: `VAYU_HEADLESS=1 ./run_demo.sh --headless`.

## 15. SIH procedure and target acceptance

Follow [demo_script.md](docs/demo_script.md) and [sih_demo_checklist.md](docs/sih_demo_checklist.md).
Start this observer in a second sourced terminal immediately after launching:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 RMW_IMPLEMENTATION=rmw_fastrtps_cpp
./validate_target.sh
```

This requires actual received RGB/depth, flight, observation and map messages,
node discovery, reinspection and completed landing. It writes
`validation/target_acceptance.json` and fails if these conditions are missing.
The full acceptance applies to the deterministic Gazebo demo. Real YOLO may find
zero persons in the primitive world; that is an honest domain-gap result.

Stop with Ctrl+C in the launch terminal, or `./clean.sh`. Cleanup signals only the
registered supervisor after checking process identity. It never uses `pkill`,
deletes reports, or deletes your existing PX4 installation.

## 16. What is simulated

Gazebo world, UAV physics, IMU/GNSS, RGB/depth rendering, PX4 battery, deterministic
target detections, synthetic thermal evidence and scene-context priority inputs.
The primitive fire/smoke/water visuals are symbols, not combustion, smoke transport
or fluid simulations. The default detector is a scenario oracle gated by camera
frames and view geometry; it does not model occlusion or recognize image pixels.

Real YOLO mode:

```bash
./setup_yolo.sh
./run_demo.sh --perception yolo --model "$PWD/weights/yolov8n.pt"
```

The optional setup downloads weights before the mission. Runtime requires a local
file and never silently falls back to scripted detections. A separate virtual
environment is injected only into the perception process. Pretrained YOLO person
detection does not implement the six hazard classes. Unknown urgency is
`UNASSESSED`, not artificially converted to P0–P4. Read model licensing terms before
redistribution; weights are not included in this ZIP.

## 17. What is actually validated

On the authoring PC:27 pytest tests passed,2 ROS-dependent checks skipped; all Bash
scripts parsed; all nine PX4 wire definitions matched the pinned sources; both
pure-Python mission modes completed and exercised three reinspections. The YOLO
adapter performed one real-photo smoke inference with an array transport adapter.
These checks do not establish ROS build, ROS-node startup, Gazebo integration,
autonomous flight stability, accuracy, endurance or laptop performance.

Your September22brief reports Jetson Nano/RGB/YOLO and a basic UAV/Cube platform.
Those are recorded as team-reported progress. This package does not independently
verify those hardware tests and does not claim RB5, thermal or deployed SAR validation.

## 18. Future physical integration

Replace the camera source and detector adapter behind the same observation envelope.
Calibrate RGB/depth extrinsics and timestamps, implement uncertainty-aware tracking,
collect labelled SAR data and independently validate hazards. Thermal fields accept
real observations later but never infer body temperature from this fixture. RB5 /
QRB5165 remains a future target. Physical flight needs a separate safety/configuration
review; the launch scripts intentionally use simulation-only settings.

Official sources: [PX4 ROS2](https://docs.px4.io/main/en/ros2/user_guide),
[XRCE-DDS](https://docs.px4.io/main/en/middleware/uxrce_dds),
[Gazebo simulation](https://docs.px4.io/v1.17/en/sim_gazebo_gz/),
[Jazzy installation](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html).
