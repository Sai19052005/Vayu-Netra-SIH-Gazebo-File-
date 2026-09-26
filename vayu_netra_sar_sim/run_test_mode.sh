#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
if [[ "${1:-}" == --ros ]]; then
  ubuntu;rosenv;shift
  exec ros2 launch vayu_netra_sim sar.launch.py mode:=test output_dir:="$ROOT/runs/ros-test-$(date +%Y%m%d-%H%M%S)" "$@"
fi
mkdir -p "$ROOT/runs"
exec python3 -m vayu_netra_sim.software_test --config "$ROOT/src/vayu_netra_sim/config/quick.yaml" --output "$ROOT/runs/software-test-$(date +%Y%m%d-%H%M%S)" "$@"
