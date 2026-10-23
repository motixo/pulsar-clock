#!/usr/bin/env python3
"""Exercise installer/rollback without changing the desktop or user files."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("clock_control", Path(__file__).resolve().parents[1] / "scripts/clock-control.py")
clock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clock)


class ClockControlTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix="clock-control-test-")
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        clock.CONFIG = root / "config"
        clock.STATE = root / "state"
        clock.DATA = root / "data"
        clock.CACHE = root / "cache/cosmic-clock-custom"
        clock.BINARY = root / "bin/cosmic-clock-custom"
        clock.DESKTOP = clock.DATA / "applications" / f"{clock.APP_ID}.desktop"
        clock.atomic_write(clock.CONFIG / "com.system76.CosmicPanel/v1/entries", '[\n "Panel",\n]')
        self.center = clock.CONFIG / "com.system76.CosmicPanel.Panel/v1/plugins_center"
        self.wings = self.center.with_name("plugins_wings")
        clock.atomic_write(self.center, f'Some(["{clock.STOCK_ID}", "old.applet",])')
        clock.atomic_write(self.wings, 'Some((["another.applet"], []))')

    def test_restore_preserves_later_edits_and_other_applets(self):
        self.assertEqual(clock.switch_clock(clock.STOCK_ID, clock.APP_ID), 1)
        clock.atomic_write(self.center, self.center.read_text().replace("old.applet", "new.applet"))
        self.assertEqual(clock.switch_clock(clock.APP_ID, clock.STOCK_ID), 1)
        self.assertIn('"new.applet"', self.center.read_text())
        self.assertEqual(self.wings.read_text(), 'Some((["another.applet"], []))')
        self.assertEqual(clock.switch_clock(clock.APP_ID, clock.STOCK_ID), 0)
        self.assertEqual(len(list((clock.STATE / "backups").iterdir())), 2)

    def test_first_install_copies_stock_settings_and_is_independent(self):
        binary = Path(shutil.which("true"))
        clock.atomic_write(clock.CONFIG / clock.STOCK_ID / "v1/show_seconds", "true")
        clock.install(binary)
        self.assertIn(f'"{clock.APP_ID}"', self.center.read_text())
        self.assertEqual((clock.CONFIG / clock.APP_ID / "v1/show_seconds").read_text(), "true")
        self.assertEqual((clock.CONFIG / clock.APP_ID / "v1/bold_text").read_text(), "true")
        self.assertEqual((clock.CONFIG / clock.APP_ID / "v1/text_color").read_text(), "None")
        self.assertEqual((clock.CONFIG / clock.STOCK_ID / "v1/show_seconds").read_text(), "true")
        self.assertTrue(clock.BINARY.is_file())

    def test_reinstall_keeps_running_process_and_preferences(self):
        # A real temporary process catches accidental applet termination on reinstall.
        binary = Path(shutil.which("sleep"))
        clock.atomic_write(self.center, f'Some(["{clock.APP_ID}",])')
        clock.atomic_write(clock.BINARY, binary.read_bytes(), 0o755)
        settings = clock.CONFIG / clock.APP_ID / "v1"
        clock.atomic_write(settings / "bold_text", "false")
        clock.atomic_write(settings / "date_time_separator", 'Some(" • ")')
        clock.atomic_write(settings / "text_color", 'Some("#AABBCC")')
        process = subprocess.Popen([str(clock.BINARY), "60"])
        try:
            clock.install(binary)
            with self.assertRaises(subprocess.TimeoutExpired):
                process.wait(timeout=0.1)
            self.assertIsNone(process.poll(), "Reinstall terminated the running applet")
            self.assertEqual((settings / "bold_text").read_text(), "false")
            self.assertEqual((settings / "date_time_separator").read_text(), 'Some(" • ")')
            self.assertEqual((settings / "text_color").read_text(), 'Some("#AABBCC")')
            self.assertIn(process.pid, clock.running_pids())
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)


    def test_install_without_activation_preserves_panel(self):
        original = self.center.read_text()
        clock.install(Path(shutil.which("true")), activate=False)
        self.assertEqual(self.center.read_text(), original)
        self.assertTrue(clock.BINARY.is_file())
        self.assertTrue(clock.DESKTOP.is_file())

    def test_uninstall_restores_stock_and_keeps_preferences_and_unrelated_files(self):
        clock.atomic_write(clock.CONFIG / clock.STOCK_ID / "v1/military_time", "true")
        clock.install(Path(shutil.which("true")))
        other_binary = clock.BINARY.with_name("unrelated-command")
        other_desktop = clock.DESKTOP.with_name("other.desktop")
        clock.atomic_write(other_binary, "keep")
        other_desktop_content = '[Desktop Entry]\nType=Application\nName=Unrelated\nExec=true\n'
        clock.atomic_write(other_desktop, other_desktop_content)
        clock.atomic_write(self.center, self.center.read_text().replace("old.applet", "new.applet"))
        clock.uninstall()
        self.assertIn(f'"{clock.STOCK_ID}"', self.center.read_text())
        self.assertIn('"new.applet"', self.center.read_text())
        self.assertFalse(clock.BINARY.exists())
        self.assertFalse(clock.DESKTOP.exists())
        self.assertTrue((clock.CONFIG / clock.APP_ID / "v1/military_time").is_file())
        self.assertEqual((clock.CONFIG / clock.STOCK_ID / "v1/military_time").read_text(), "true")
        self.assertEqual(other_binary.read_text(), "keep")
        self.assertEqual(other_desktop.read_text(), other_desktop_content)
        self.assertTrue((clock.STATE / "backups").is_dir())
        clock.uninstall()  # Repeated removal must be safe.

    def test_purge_removes_only_custom_preferences_and_cache(self):
        clock.install(Path(shutil.which("true")))
        clock.atomic_write(clock.CACHE / "downloaded-source", "source")
        other_config = clock.CONFIG / "unrelated.app/v1/preference"
        clock.atomic_write(other_config, "keep")
        clock.uninstall(purge=True)
        self.assertFalse((clock.CONFIG / clock.APP_ID).exists())
        self.assertFalse(clock.CACHE.exists())
        self.assertTrue((clock.STATE / "backups").is_dir())
        self.assertEqual(other_config.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
