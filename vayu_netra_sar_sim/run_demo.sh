#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
"$ROOT/check_environment.sh"
rosenv
exec python3 "$ROOT/scripts/supervisor.py" --mode quick "$@"
