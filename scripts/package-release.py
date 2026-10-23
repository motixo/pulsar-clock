#!/usr/bin/env python3
"""Package a built clock, installer, and its corresponding source."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile


def add_bytes(archive, name, content, executable=False):
    info = tarfile.TarInfo(name)
    info.size = len(content)
    info.mode = 0o755 if executable else 0o644
    archive.addfile(info, io.BytesIO(content))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    release = json.loads((root / "release.json").read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    bundle = {**release, "binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest()}
    files = [
        "install.sh", "uninstall.sh", "build-from-source.sh", "release.json",
        "README.md", "LICENSE", "NOTICE", "clock-preferences.patch", "assets/screenshot.png",
        "scripts/clock-control.py", "scripts/install-prebuilt.py",
    ]
    binary_archive = args.output / "pulsar-clock-linux-x86_64.tar.gz"
    with tarfile.open(binary_archive, "w:gz") as archive:
        for name in files:
            add_bytes(archive, f"pulsar-clock/{name}", (root / name).read_bytes(), name.endswith(".sh"))
        add_bytes(archive, "pulsar-clock/bin/pulsar-clock", args.binary.read_bytes(), True)
        add_bytes(archive, "pulsar-clock/bundle.json", json.dumps(bundle, indent=2).encode() + b"\n")
    source_archive = args.output / f"pulsar-clock-v{release['version']}-source.tar.gz"
    prefix = f"pulsar-clock-v{release['version']}-source"
    with tarfile.open(source_archive, "w:gz") as archive:
        for path in sorted(args.source.rglob("*")):
            relative = path.relative_to(args.source)
            if path.is_file() and not {".git", "target"}.intersection(relative.parts):
                add_bytes(archive, f"{prefix}/{relative.as_posix()}", path.read_bytes(), bool(path.stat().st_mode & 0o111))
        for name in files + ["packaging/Dockerfile", "scripts/build-release.sh", "scripts/package-release.py"]:
            add_bytes(archive, f"{prefix}/release-tools/{name}", (root / name).read_bytes(), name.endswith(".sh"))
    checksums = "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in (binary_archive, source_archive))
    (args.output / "SHA256SUMS").write_text(checksums)
    print(checksums, end="")


if __name__ == "__main__":
    main()
