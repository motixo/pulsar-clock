import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prebuilt", root / "scripts/install-prebuilt.py")
prebuilt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prebuilt)


class PrebuiltTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="clock-prebuilt-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.release = json.loads((root / "release.json").read_text())
        self.binary = self.root / "bin/pulsar-clock"
        self.binary.parent.mkdir()
        self.binary.write_bytes(b"\x7fELFtest-binary")
        self.bundle = {**self.release, "binary_sha256": hashlib.sha256(self.binary.read_bytes()).hexdigest()}
        (self.root / "release.json").write_text(json.dumps(self.release))
        (self.root / "bundle.json").write_text(json.dumps(self.bundle))

    def archive(self, symlink=False):
        path = self.root / prebuilt.ASSET
        with tarfile.open(path, "w:gz") as archive:
            for name, content in [
                ("pulsar-clock/bundle.json", json.dumps(self.bundle).encode()),
                ("pulsar-clock/bin/pulsar-clock", self.binary.read_bytes()),
                ("../../unwanted", b"do not extract"),
            ]:
                info = tarfile.TarInfo(name)
                info.size = len(content)
                if symlink and name.endswith("pulsar-clock"):
                    info.type = tarfile.SYMTYPE
                    info.linkname = "/etc/passwd"
                archive.addfile(info, io.BytesIO(content))
        return path

    def test_valid_and_invalid_download_checksums(self):
        archive = self.archive()
        checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
        prebuilt.verify_checksum(archive, f"{checksum}  {archive.name}\n")
        with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
            prebuilt.verify_checksum(archive, f"{'0' * 64}  {archive.name}\n")
        for text in ["", f"{checksum}  another-file.tar.gz", f"not-a-hash  {archive.name}"]:
            with self.assertRaises(RuntimeError):
                prebuilt.verify_checksum(archive, text)

    def test_unpack_reads_only_expected_regular_files(self):
        destination = self.root / "unpacked"
        destination.mkdir()
        binary, bundle = prebuilt.unpack_binary(self.archive(), destination)
        self.assertEqual(binary.read_bytes(), self.binary.read_bytes())
        self.assertEqual(bundle, self.bundle)
        self.assertFalse((self.root / "unwanted").exists())
        self.assertEqual(list(destination.iterdir()), [binary])

    def test_symlink_cannot_be_used_as_binary(self):
        with self.assertRaisesRegex(RuntimeError, "Invalid release archive member"):
            prebuilt.unpack_binary(self.archive(symlink=True), self.root)

    def test_tampered_binary_and_wrong_release_are_rejected(self):
        prebuilt.check_bundle(self.binary, self.bundle, self.release)
        with self.assertRaisesRegex(RuntimeError, "unexpected version"):
            prebuilt.check_bundle(self.binary, {**self.bundle, "version": "wrong"}, self.release)
        self.binary.write_bytes(b"corrupt")
        with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
            prebuilt.check_bundle(self.binary, self.bundle, self.release)

    def test_platform_and_glibc_requirements(self):
        with patch.object(prebuilt.platform, "system", return_value="Linux"), patch.object(prebuilt.platform, "machine", return_value="x86_64"):
            with patch.object(prebuilt.os, "confstr", return_value="glibc 2.35"):
                prebuilt.check_platform(self.release)
            with patch.object(prebuilt.os, "confstr", return_value="glibc 2.31"):
                with self.assertRaisesRegex(RuntimeError, "glibc 2.35 or newer"):
                    prebuilt.check_platform(self.release)
        with patch.object(prebuilt.platform, "system", return_value="Linux"), patch.object(prebuilt.platform, "machine", return_value="aarch64"):
            with self.assertRaisesRegex(RuntimeError, "x86_64"):
                prebuilt.check_platform(self.release)

    def test_runtime_is_checked_before_install(self):
        expected = f"Pulsar Clock {self.release['version']} (COSMIC {self.release['upstream_ref'].removeprefix('epoch-')})\n"
        with patch.object(prebuilt.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, expected, "")):
            prebuilt.check_runtime(self.binary, self.release)
        with patch.object(prebuilt.subprocess, "run", return_value=subprocess.CompletedProcess([], 127, "", "library missing")):
            with self.assertRaisesRegex(RuntimeError, "library missing"):
                prebuilt.check_runtime(self.binary, self.release)

    def test_bundle_install_preserves_no_activate_and_uses_no_download(self):
        manager = Mock()
        with patch.object(prebuilt, "load_manager", return_value=manager), patch.object(prebuilt, "check_platform"), patch.object(prebuilt, "check_runtime"), patch.object(prebuilt, "fetch_binary") as fetch:
            prebuilt.install_release(self.root, no_activate=True)
        fetch.assert_not_called()
        manager.install.assert_called_once_with(self.binary, activate=False)

    def test_invalid_bundle_does_not_change_installation(self):
        self.binary.write_bytes(b"corrupt")
        manager = Mock()
        with patch.object(prebuilt, "load_manager", return_value=manager), patch.object(prebuilt, "check_platform"):
            with self.assertRaises(RuntimeError):
                prebuilt.install_release(self.root)
        manager.install.assert_not_called()


if __name__ == "__main__":
    unittest.main()
