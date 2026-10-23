#!/usr/bin/env python3
"""Install or restore the separate, user-owned COSMIC clock applet."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone

APP_ID = "io.github.motixo.CosmicClock"
STOCK_ID = "com.system76.CosmicAppletTime"
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "cosmic"
DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
STATE = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "cosmic-clock-custom"
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "cosmic-clock-custom"
BINARY = Path.home() / ".local/bin/cosmic-clock-custom"
DESKTOP = DATA / "applications" / f"{APP_ID}.desktop"
DEFAULTS = {
    "show_seconds": "false",
    "military_time": "false",
    "first_day_of_week": "6",
    "show_date_in_top_panel": "true",
    "show_weekday": "false",
    "format_strftime": '""',
    "bold_text": "true",
    "date_time_separator": 'Some(" • ")',
    "text_color": "None",
}


def atomic_write(path, content, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(content if isinstance(content, bytes) else content.encode())
            target.flush()
            os.fsync(target.fileno())
            os.fchmod(target.fileno(), mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def panel_files():
    entries = CONFIG / "com.system76.CosmicPanel/v1/entries"
    if not entries.exists():
        return []
    names = [json.loads(match) for match in re.findall(r'"(?:[^"\\]|\\.)*"', entries.read_text())]
    return [
        file
        for name in names
        for file in (CONFIG / f"com.system76.CosmicPanel.{name}" / "v1").glob("plugins_*")
        if file.is_file()
    ]


def switch_clock(original, replacement):
    changes = []
    for path in panel_files():
        before = path.read_text()
        after = before.replace(f'"{original}"', f'"{replacement}"')
        if before != after:
            changes.append((path, before, after))
    if changes:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = STATE / "backups" / stamp
        backup.mkdir(parents=True)
        for path, before, after in changes:
            snapshot = backup / path.parent.parent.name / path.name
            atomic_write(snapshot, before)
            atomic_write(path, after)
        print(f"Changed {len(changes)} panel setting(s); backup: {backup}")
    return len(changes)


def desktop_text():
    # Escape the absolute executable path according to the Desktop Entry Exec rules.
    escaped = str(BINARY).replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$").replace("%", "%%")
    return f'''[Desktop Entry]
Name=Custom Clock
Name[fa]=ساعت سفارشی
Comment=Date, time and calendar with clock preferences
Type=Application
Exec="{escaped}"
Terminal=false
Categories=COSMIC;
Icon=com.system76.CosmicAppletTime-symbolic
NoDisplay=true
X-CosmicApplet=true
X-CosmicShrinkable=true
X-HostWaylandDisplay=true
X-CosmicHoverPopup=Auto
'''


def install(binary, activate=True):
    binary = binary.resolve(strict=True)
    if binary.read_bytes()[:4] != b"\x7fELF":
        raise SystemExit("Expected a compiled Linux ELF executable.")
    settings = CONFIG / APP_ID / "v1"
    stock = CONFIG / STOCK_ID / "v1"
    # Copy the stock preferences on the first installation, then preserve all custom choices.
    for key, default in DEFAULTS.items():
        target = settings / key
        if not target.exists():
            original = stock / key
            value = original.read_text() if key not in {"bold_text", "date_time_separator", "text_color"} and original.exists() else default
            atomic_write(target, value)
    if BINARY.exists():
        STATE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BINARY, STATE / "previous-binary")
    atomic_write(BINARY, binary.read_bytes(), 0o755)
    atomic_write(DESKTOP, desktop_text())
    if shutil.which("desktop-file-validate"):
        subprocess.run(["desktop-file-validate", str(DESKTOP)], check=True)
    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(DESKTOP.parent)], check=True)
    activated = switch_clock(STOCK_ID, APP_ID) if activate else 0
    print(f"Installed {BINARY}")
    selected = any(f'"{APP_ID}"' in path.read_text() for path in panel_files())
    if selected:
        print("Click the clock, then Clock preferences…")
    else:
        print("Add Custom Clock through COSMIC panel settings when you want to use it.")
    if selected and not activated:
        # COSMIC can remove an applet after a clean exit instead of respawning it.
        # Keep the running instance alive; the new executable is used on the next login.
        print("The running applet is preserved. A rebuilt executable takes effect on the next login or panel reload.")


def uninstall(purge=False):
    # Restore panel references before deleting any executable or desktop entry.
    switch_clock(APP_ID, STOCK_ID)
    BINARY.unlink(missing_ok=True)
    DESKTOP.unlink(missing_ok=True)
    (STATE / "previous-binary").unlink(missing_ok=True)
    if DESKTOP.parent.exists() and shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(DESKTOP.parent)], check=True)
    if purge:
        deadline = time.monotonic() + 5
        while running_pids() and time.monotonic() < deadline:
            time.sleep(0.1)
        if running_pids():
            raise SystemExit("The clock is still running. Preferences were kept; log out and rerun uninstall.sh --purge.")
        for directory in (CONFIG / APP_ID, CACHE):
            if directory.exists():
                shutil.rmtree(directory)
    print("Custom Clock removed; the stock clock is selected wherever it was replaced.")
    print("Panel backups are retained in " + str(STATE / "backups"))
    if not purge:
        print("Custom preferences and build cache are retained. Use --purge to remove them too.")


def running_pids():
    found = []
    for entry in Path("/proc").iterdir():
        if entry.name.isdecimal():
            try:
                executable = os.readlink(entry / "exe").removesuffix(" (deleted)")
                if executable == str(BINARY):
                    found.append(int(entry.name))
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                pass
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    install_parser = sub.add_parser("install")
    install_parser.add_argument("binary", type=Path)
    install_parser.add_argument("--no-activate", action="store_true", help="Keep the panel's current applets selected")
    uninstall_parser = sub.add_parser("uninstall")
    uninstall_parser.add_argument("--purge", action="store_true", help="Also remove custom preferences and build cache")
    sub.add_parser("activate")
    sub.add_parser("restore")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.action != "status" and os.geteuid() == 0:
        parser.error("Run this command as your desktop user, without sudo.")
    if args.action == "install":
        install(args.binary, activate=not args.no_activate)
    elif args.action == "uninstall":
        uninstall(purge=args.purge)
    elif args.action == "activate":
        if not BINARY.is_file() or not DESKTOP.is_file():
            raise SystemExit("Install the custom clock before activating it.")
        switch_clock(STOCK_ID, APP_ID)
    elif args.action == "restore":
        switch_clock(APP_ID, STOCK_ID)
        print("Restored the stock clock. Custom preferences and binary are retained.")
    else:
        print(f"Binary: {BINARY} ({'installed' if BINARY.exists() else 'absent'})")
        print(f"Running processes: {running_pids() or 'none'}")
        for file in panel_files():
            content = file.read_text()
            for identifier in (APP_ID, STOCK_ID):
                if f'"{identifier}"' in content:
                    print(f"{file.parent.parent.name}/{file.name}: {identifier}")


if __name__ == "__main__":
    main()
