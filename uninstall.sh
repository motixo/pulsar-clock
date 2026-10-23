#!/usr/bin/env bash
# Restore the original clock and remove the per-user installation.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$script_dir/scripts/clock-control.py" uninstall "$@"
