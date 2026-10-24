#!/bin/sh
# Fetch the current installer; release.json pins the checksummed binary release.
set -eu
PULSAR_TEMP=$(mktemp -d -t pulsar-clock.XXXXXXXX)
trap 'rm -rf "$PULSAR_TEMP"' EXIT HUP INT TERM
curl -fL --retry 3 --connect-timeout 15 --speed-limit 10240 --speed-time 30 https://github.com/motixo/pulsar-clock/archive/refs/heads/main.tar.gz -o "$PULSAR_TEMP/installer.tar.gz"
tar -xzf "$PULSAR_TEMP/installer.tar.gz" -C "$PULSAR_TEMP"
if [ "${1:-}" = "--uninstall" ]; then
    shift
    "$PULSAR_TEMP/pulsar-clock-main/uninstall.sh" "$@"
else
    "$PULSAR_TEMP/pulsar-clock-main/install.sh" "$@"
fi
