# Ubuntu24.04 / Jazzy / Harmonic troubleshooting

Start with `./check_environment.sh`, then read the first failing process log in the
newest `runs/` folder. The dashboard is not proof that PX4 is healthy.

| Symptom | Diagnosis and concrete next action |
|---|---|
| Jazzy missing | Install `ros-jazzy-desktop` and `ros-dev-tools` using the official Jazzy Noble instructions below, source its setup, rerun setup. Do not source another ROS distro. |
| `ros-jazzy-ros-gzharmonic` cannot be located | Run `sudo apt update` and `apt-cache policy ros-jazzy-ros-gzharmonic`. Verify Noble ROS2 repositories and Gazebo stable repository. Use the exact package named in official PX4 ROS2 guidance. Do not substitute another Gazebo major version. |
| Harmonic native development packages missing | Add the official Gazebo Noble repository as below, then rerun setup. Verify `gz sim --versions` lists8.x. |
| PX4 build fails | Verify the locked commit and submodules: `git -C vendor/PX4-Autopilot submodule status --recursive`. Rerun setup; use `JOBS=1 ./build.sh` for memory pressure. Read the first compiler/CMake error, not the final make wrapper error. |
| Python build module missing | Activate `.px4-venv/bin/activate` and reinstall the pinned checkout's `Tools/setup/requirements.txt`; do not use system pip or another Python major. |
| Agent build fails | Confirm Agent2.4.3, native dependencies and available disk. Source dependencies are isolated in vendor; do not mix an arbitrary Agent3 binary into the2.x client setup. Inspect `vendor/agent-build`. |
| Wrong px4_msgs | `python3 scripts/verify_contract.py` identifies mismatch. Work from a new extraction/setup or deliberately restore the documented pin yourself. Scripts do not reset your work automatically. |
| ROS package/executable missing | Run `./build.sh`, then `source install/setup.bash`; inspect `ros2 pkg executables vayu_netra_sim`. A successful Python import alone is not package installation. |
| Python import / cv_bridge ABI error | Use Ubuntu Python3.12 for ROS. Keep YOLO in the provided optional environment with NumPy1.x. The perception process gets its site-packages path through the supervisor. Do not activate a Windows/Conda environment for colcon. |
| `ros_gz_bridge` missing | `sudo apt install ros-jazzy-ros-gzharmonic`; verify `ros2 pkg prefix ros_gz_bridge`. |
| World/model not found | Launch through run_demo.sh, which sets the custom and pinned upstream model resource paths. Check `vendor/PX4-Autopilot/Tools/simulation/gz/models/x500/model.sdf`. No Fuel download should occur during the mission. |
| Gazebo starts but camera black/missing | Inspect RGBD model/plugin errors in gazebo.log; verify Ogre2/EGL support and `/vayu/camera/image`. Symbolic scene objects are not guaranteed YOLO detections. |
| Gazebo window absent | Check DISPLAY/WAYLAND_DISPLAY. `gz sim -g` must run in a graphical session. Headless operation requires `VAYU_HEADLESS=1 ./run_demo.sh --headless`. |
| Low FPS / OpenGL errors | Inspect `glxinfo -B`; prefer hardware rendering. Close other GPU workloads and use the portable software fallback if3D rendering is unreliable. Headless still needs a rendering context. Do not display invented FPS. |
| `/fmu/out/...` missing | Check agent.log and px4.log, UDP8888 occupancy and ROS_DOMAIN_ID42. Use versioned endpoints: status/local_position/battery each have `_v1`. Other subscribed endpoints in architecture.md are unversioned. |
| XRCE connection fails | Ensure the launched Agent2.4.3 owns UDP8888 and PX4 starts its UDP client. Do not run a second Agent. Check domain and localhost configuration in both terminals. |
| Offboard won't engage | Confirm continuing20Hz heartbeat/setpoint publications, fresh valid local/global reference feedback, unpaused clock, then read command ACK and PX4 preflight messages. The code intentionally waits rather than falsely declaring takeoff. |
| Won't arm | Inspect PX4 reasons; fix missing estimator/sensors or configuration. Do not force arm or remove safety checks just for the dashboard. Default launcher uses SITL-only RC settings. |
| Armed but won't move | Check `/vayu/mission`, `/vayu/control`, `/fmu/in/trajectory_setpoint`; verify OFFBOARD feedback and NED negative-Z setpoints. Do not invert coordinates ad hoc. |
| Clock problems | `ros2 topic echo /clock --once`. Source is `/world/disaster_zone/clock`. All application nodes use sim time; the launcher disables PX4 time synchronization for this shared-clock arrangement. |
| Nodes don't communicate | In every terminal: source Jazzy and install overlay; export ROS_DOMAIN_ID=42 ROS_LOCALHOST_ONLY=1 RMW_IMPLEMENTATION=rmw_fastrtps_cpp. Restart the ROS CLI daemon after changing domain if needed. |
| Mission aborts mid-search | Inspect event reason. Kill/stale pipeline, mode loss, estimator reset or feedback expiry deliberately causes abort/landing fallback. Do not relabel ABORTED as success. |
| Reinspection times out | A second observation must arrive after reaching target radius. Check camera timestamps/view, detector output and pose matching. The code resumes without manufacturing evidence. |
| No detections in YOLO mode | First verify image pixels and model file. Primitive humanoids may be out of domain. Use the explicitly labelled deterministic demo for closed-loop presentation; use real labelled photos/video for model evaluation. |
| YOLO package missing | Run `./setup_yolo.sh` before the mission. Start through the wrapper with `--perception yolo --model "$PWD/weights/yolov8n.pt"`. |
| Dashboard cannot connect | Check dashboard process in ros.log and port8080. URL is `http://127.0.0.1:8080`, on the same laptop. Server deliberately does not bind all network interfaces. |
| Permission denied | `chmod +x ./*.sh scripts/*.sh`. If filesystem is mounted noexec, extract under your Ubuntu home directory. |
| Stale supervisor / busy port | Stop the prior run with Ctrl+C or `./clean.sh`. Inspect port owner with `ss -lntup`; do not kill unrelated processes. Clean never deletes logs. |
| Report missing | Verify mapping node and writable output path. Reports begin after startup and are periodically written. Abrupt power/process kill can prevent a final flush; inspect last snapshot. |

## Official repository setup references

ROS2 installation: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

PX4 integration package: https://docs.px4.io/main/en/ros2/user_guide

Gazebo Harmonic: https://gazebosim.org/docs/harmonic/install_ubuntu/

If the Gazebo stable repository is absent, the official Noble-compatible pattern is:

```bash
sudo apt install curl lsb-release gnupg
sudo curl -fsSL https://packages.osrfoundation.org/gazebo.gpg -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list
sudo apt update
sudo apt install gz-harmonic ros-jazzy-ros-gzharmonic
```

Repository configuration is an installation step, never a mission-time dependency.
If the exact ROS integration package remains unavailable, record `apt-cache policy`
and repository output and resolve the package source before proceeding. No automatic
fallback to a mismatched bridge is implemented.
