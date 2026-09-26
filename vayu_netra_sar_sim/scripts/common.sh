#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export ROOT
die() { echo "ERROR: $*" >&2; exit 1; }
ubuntu() { [[ "$(uname -s)" == Linux ]] || die 'Run on Ubuntu24.04 x86_64. This shell is not Linux.'; source /etc/os-release; [[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] || die "Expected Ubuntu24.04, found $ID $VERSION_ID"; [[ "$(uname -m)" == x86_64 ]] || die 'Expected x86_64 laptop'; }
rosenv() { [[ -f /opt/ros/jazzy/setup.bash ]] || die 'ROS2 Jazzy missing. Install using https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html then rerun setup.sh'; set +u; source /opt/ros/jazzy/setup.bash; [[ ! -f "$ROOT/install/setup.bash" ]] || source "$ROOT/install/setup.bash"; set -u; export ROS_DOMAIN_ID=42; export ROS_LOCALHOST_ONLY=1; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; }
export PYTHONPATH="$ROOT/src/vayu_netra_sim${PYTHONPATH:+:$PYTHONPATH}"
