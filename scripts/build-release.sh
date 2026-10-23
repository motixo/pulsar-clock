#!/usr/bin/env bash
# Build a distributable binary using an Ubuntu 22.04 runtime baseline.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
output_dir=${1:?Usage: scripts/build-release.sh OUTPUT_DIRECTORY}
mkdir -p -- "$output_dir"
output_dir=$(cd -- "$output_dir" && pwd)
version=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$root/release.json")
upstream_ref=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["upstream_ref"])' "$root/release.json")
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
git clone --depth 1 --single-branch --branch "$upstream_ref" https://github.com/pop-os/cosmic-applets.git "$work/source"
git -C "$work/source" apply --check "$root/clock-preferences.patch"
git -C "$work/source" apply "$root/clock-preferences.patch"
mkdir -p "$work/cargo" "$work/target"
docker build -t cosmic-clock-release-builder -f "$root/packaging/Dockerfile" "$root/packaging"
docker run --rm --user "$(id -u):$(id -g)" \
    -e COSMIC_CLOCK_VERSION="$version" -e CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" \
    -v "$work/source:/source:ro" -v "$work/cargo:/build/cargo" -v "$work/target:/build/target" \
    cosmic-clock-release-builder sh -c \
    'cargo test -p cosmic-applet-time --features personal-clock --locked --lib && cargo build -p cosmic-applet-time --features personal-clock --locked --release --bin cosmic-applet-time && strip --strip-unneeded /build/target/release/cosmic-applet-time && /build/target/release/cosmic-applet-time --version'
python3 "$root/scripts/package-release.py" --binary "$work/target/release/cosmic-applet-time" --source "$work/source" --output "$output_dir"
