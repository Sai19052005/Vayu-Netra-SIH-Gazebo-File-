#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
ubuntu;rosenv
exec python3 "$ROOT/scripts/acceptance.py" --output "$ROOT/validation/target_acceptance.json" "$@"
