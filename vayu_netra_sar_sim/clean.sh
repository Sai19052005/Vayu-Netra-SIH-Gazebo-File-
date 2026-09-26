#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
# No broad pkill/killall and no deletion of source, reports or user's PX4 checkout.
exec python3 "$ROOT/scripts/cleanup.py" "$@"
