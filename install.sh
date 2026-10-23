#!/usr/bin/env bash
# Rebuild against a COSMIC applets release; only replace the installed clock after success.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
release_ref=""
build_only=false
activate=true
while (($#)); do
    case "$1" in
        --ref) release_ref=${2:?Expected an upstream tag or branch}; shift 2 ;;
        --build-only) build_only=true; shift ;;
        --no-activate) activate=false; shift ;;
        --help|-h)
            printf '%s\n' 'Usage: install.sh [--ref epoch-1.9.0] [--build-only] [--no-activate]' \
                'Without --ref, use the installed Arch cosmic-applets package version.' \
                'Use --no-activate to install without changing panel applets.' \
                'Existing preferences are preserved; failures leave the installed applet intact.'
            exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
    esac
done

if ((EUID == 0)); then
    printf '%s\n' 'Run this installer as your desktop user, without sudo.' >&2
    exit 1
fi

for dependency in git cargo rustc cc pkg-config python3; do
    command -v "$dependency" >/dev/null || { printf 'Missing dependency: %s\n' "$dependency" >&2; exit 1; }
done
if [[ -z $release_ref ]]; then
    if command -v pacman >/dev/null && package=$(pacman -Q cosmic-applets); then
        package_version=${package##* }
        package_version=${package_version#*:}
        release_ref="epoch-${package_version%-*}"
    else
        printf '%s\n' 'Cannot determine the COSMIC version. Specify --ref epoch-VERSION.' >&2
        exit 1
    fi
fi

cache_dir=${XDG_CACHE_HOME:-"$HOME/.cache"}/cosmic-clock-custom
mkdir -p -- "$cache_dir"
source_dir=$(mktemp -d "$cache_dir/source.XXXXXXXX")
printf 'Building from upstream %s in %s\n' "$release_ref" "$source_dir"
git clone --depth 1 --single-branch --branch "$release_ref" -- \
    https://github.com/pop-os/cosmic-applets.git "$source_dir"
cd -- "$source_dir"
if ! git apply --check "$script_dir/clock-preferences.patch"; then
    printf '%s\n' 'This COSMIC version needs a patch update. The installed clock has not been changed.' >&2
    exit 1
fi
git apply "$script_dir/clock-preferences.patch"
export CARGO_TARGET_DIR=${CARGO_TARGET_DIR:-"$cache_dir/target"}
export CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-6}
cargo test -p cosmic-applet-time --features personal-clock --locked --lib
cargo build -p cosmic-applet-time --features personal-clock --locked --release --bin cosmic-applet-time
executable="$CARGO_TARGET_DIR/release/cosmic-applet-time"
if command -v strip >/dev/null; then
    strip --strip-unneeded "$executable"
fi
if "$build_only"; then
    printf 'Built successfully: %s\n' "$executable"
else
    install_options=()
    if ! "$activate"; then
        install_options+=(--no-activate)
    fi
    python3 "$script_dir/scripts/clock-control.py" install "$executable" "${install_options[@]}"
fi
