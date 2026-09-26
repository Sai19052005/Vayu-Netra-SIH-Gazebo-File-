#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
ubuntu
[[ -f /opt/ros/jazzy/setup.bash ]] || die 'Install Jazzy first: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html (ros-jazzy-desktop and ros-dev-tools). Your stated laptop already has Jazzy.'
sudo apt-get update
apt-cache show ros-jazzy-ros-gzharmonic >/dev/null 2>&1 || die 'ros-jazzy-ros-gzharmonic unavailable in configured repositories. Follow the official PX4 Jazzy/Harmonic integration instructions in docs/troubleshooting.md. Do not substitute Fortress packages.'
sudo apt-get install -y git cmake build-essential ninja-build python3-venv python3-pip python3-yaml python3-pytest python3-colcon-common-extensions python3-opencv ros-jazzy-ros-gzharmonic ros-jazzy-cv-bridge ros-jazzy-rmw-fastrtps-cpp ros-jazzy-visualization-msgs ros-jazzy-rosgraph-msgs libasio-dev libtinyxml2-dev
sudo apt-get install -y astyle ccache cppcheck file gdb lcov libssl-dev libxml2-dev libxml2-utils python3-dev python3-setuptools python3-wheel rsync shellcheck unzip zip bc mesa-utils libgz-sim8-dev libgz-transport13-dev libgz-msgs10-dev
sudo apt-get install -y libunwind-dev cppzmq-dev libeigen3-dev libgstreamer-plugins-base1.0-dev libopencv-dev pkg-config protobuf-compiler
python3 "$ROOT/scripts/bootstrap.py"
# Upstream PX4 setup may use --break-system-packages. Instead use a private Python
# environment for its Python requirements, and its no-sim-tools dependency set only
# if requested explicitly. We never invoke a system-wide pip install here.
python3 -m venv --system-site-packages "$ROOT/.px4-venv"
"$ROOT/.px4-venv/bin/python" -m pip install -r "$ROOT/vendor/PX4-Autopilot/Tools/setup/requirements.txt"
echo 'Sources and build dependencies ready. Run ./build.sh.'
