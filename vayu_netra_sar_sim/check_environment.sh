#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
ubuntu; rosenv
python3 "$ROOT/scripts/check_environment.py"
