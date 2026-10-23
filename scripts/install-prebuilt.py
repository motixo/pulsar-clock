#!/usr/bin/env python3
"""Install a verified COSMIC Clock release without a Rust toolchain."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

ASSET = "cosmic-clock-linux-x86_64.tar.gz"
PREFIX = "cosmic-clock"


def download(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": "cosmic-clock-installer"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def verify_checksum(path, checksum_text):
    for line in checksum_text.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1].lstrip("*") == path.name:
            expected = fields[0].lower()
            if not re.fullmatch(r"[0-9a-f]{64}", expected):
                break
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise RuntimeError("Release checksum mismatch; nothing was installed.")
            return
    raise RuntimeError("The release checksum file does not identify this download.")


def read_member(archive, name, limit):
    member = archive.getmember(name)
    if not member.isfile() or member.size > limit:
        raise RuntimeError(f"Invalid release archive member: {name}")
    with archive.extractfile(member) as stream:
        return stream.read()


def unpack_binary(archive_path, destination):
    # Read only these two regular files; never extract paths supplied by a tarball.
    with tarfile.open(archive_path, "r:gz") as archive:
        bundle = json.loads(read_member(archive, f"{PREFIX}/bundle.json", 16384))
        content = read_member(archive, f"{PREFIX}/bin/cosmic-clock-custom", 128 * 1024 * 1024)
    binary = destination / "cosmic-clock-custom"
    binary.write_bytes(content)
    binary.chmod(0o755)
    return binary, bundle


def check_bundle(binary, bundle, release):
    for key in ("version", "upstream_ref", "architecture", "minimum_glibc"):
        if bundle.get(key) != release[key]:
            raise RuntimeError(f"The binary bundle has an unexpected {key}.")
    expected = bundle.get("binary_sha256")
    if not expected or hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise RuntimeError("Binary checksum mismatch; nothing was installed.")
    if binary.read_bytes()[:4] != b"\x7fELF":
        raise RuntimeError("The release does not contain a Linux ELF executable.")


def version_tuple(value):
    return tuple(int(part) for part in value.split("."))


def check_platform(release):
    if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        raise RuntimeError("This release supports Linux x86_64. Use install.sh --from-source on another architecture.")
    try:
        libc = os.confstr("CS_GNU_LIBC_VERSION") or ""
    except (ValueError, OSError):
        libc = ""
    if not libc.startswith("glibc "):
        raise RuntimeError("This binary needs glibc. Use install.sh --from-source on another libc.")
    installed = libc.split()[1]
    if version_tuple(installed) < version_tuple(release["minimum_glibc"]):
        raise RuntimeError(f"This release needs glibc {release['minimum_glibc']} or newer; found {installed}.")


def check_runtime(binary, release):
    result = subprocess.run([str(binary), "--version"], text=True, capture_output=True)
    expected = f"COSMIC Clock {release['version']} (COSMIC {release['upstream_ref'].removeprefix('epoch-')})"
    if result.returncode or result.stdout.strip() != expected:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit status {result.returncode}"
        raise RuntimeError(f"The downloaded clock cannot run on this system: {detail}")


def fetch_binary(release, destination):
    base_url = f"https://github.com/{release['repository']}/releases/download/v{release['version']}"
    checksum_path = destination / "SHA256SUMS"
    archive_path = destination / ASSET
    print(f"Downloading COSMIC Clock {release['version']} for Linux x86_64…", flush=True)
    download(f"{base_url}/SHA256SUMS", checksum_path)
    download(f"{base_url}/{ASSET}", archive_path)
    verify_checksum(archive_path, checksum_path.read_text())
    return unpack_binary(archive_path, destination)


def load_manager(root):
    spec = importlib.util.spec_from_file_location("clock_control", root / "scripts/clock-control.py")
    manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager)
    return manager


def install_release(root, no_activate=False):
    release = json.loads((root / "release.json").read_text())
    check_platform(release)
    manager = load_manager(root)
    with tempfile.TemporaryDirectory(prefix="cosmic-clock-install-") as temporary:
        local_binary = root / "bin/cosmic-clock-custom"
        if local_binary.is_file():
            binary = local_binary
            bundle = json.loads((root / "bundle.json").read_text())
        else:
            binary, bundle = fetch_binary(release, Path(temporary))
        check_bundle(binary, bundle, release)
        check_runtime(binary, release)
        manager.install(binary, activate=not no_activate)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Build it yourself instead: ./install.sh --from-source [--ref epoch-1.9.0]",
    )
    parser.add_argument("--no-activate", action="store_true", help="Keep current panel applets selected")
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error("Run this installer as your desktop user, without sudo.")
    try:
        install_release(Path(__file__).resolve().parents[1], args.no_activate)
    except (OSError, RuntimeError, ValueError, KeyError, tarfile.TarError) as error:
        parser.exit(1, f"Install failed: {error}\n")


if __name__ == "__main__":
    main()
