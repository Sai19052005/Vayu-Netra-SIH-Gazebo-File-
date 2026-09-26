#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
ubuntu; rosenv
[[ -d "$ROOT/vendor/PX4-Autopilot/.git" ]] || die 'Run ./setup.sh first'
python3 "$ROOT/scripts/verify_contract.py"
JOBS="${JOBS:-2}"
cmake -S "$ROOT/vendor/Micro-XRCE-DDS-Agent" -B "$ROOT/vendor/agent-build" -DCMAKE_INSTALL_PREFIX="$ROOT/vendor/agent-install" -DUAGENT_BUILD_EXAMPLES=OFF
cmake --build "$ROOT/vendor/agent-build" -j "$JOBS"
cmake --install "$ROOT/vendor/agent-build"
(
  source "$ROOT/.px4-venv/bin/activate"
  cd "$ROOT/vendor/PX4-Autopilot"
  make px4_sitl_default -j "$JOBS"
)
cd "$ROOT"
colcon build --symlink-install --packages-select px4_msgs vayu_netra_sim --executor sequential
python3 -m pytest "$ROOT/src/vayu_netra_sim/tests" -q
rosenv
ros2 pkg prefix vayu_netra_sim
ros2 pkg executables vayu_netra_sim
"$ROOT/check_environment.sh"
