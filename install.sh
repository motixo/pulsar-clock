#!/usr/bin/env bash
# Install the ready-made release by default; source builds are opt-in.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ ${1:-} == --from-source ]]; then
    shift
    exec bash "$script_dir/build-from-source.sh" "$@"
fi
exec python3 "$script_dir/scripts/install-prebuilt.py" "$@"
