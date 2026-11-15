"""Verify the generated macOS service command without touching launchd."""

import contextlib
import io
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class MacServiceTest(unittest.TestCase):
    def test_plist_launches_framework_executable_without_apple_shim(self):
        script = (Path(__file__).resolve().parents[1] / "scripts/install_service.sh").read_text()
        source = script.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "framework/Resources/Python.app/Contents/MacOS/Python"
            executable.parent.mkdir(parents=True)
            executable.touch()
            for framework_exists in (True, False):
                with self.subTest(framework_exists=framework_exists):
                    if not framework_exists:
                        executable.unlink()
                    plist = root / "service.plist"
                    args = ["-", str(plist), str(root), "8765", "0", "/usr/bin:/bin", "", "8443"]
                    output = io.StringIO()
                    with mock.patch.object(sys, "argv", args), mock.patch.object(
                        sys, "prefix", str(root / "framework")
                    ), mock.patch.object(sys, "executable", "/selected/python3"), contextlib.redirect_stdout(output):
                        exec(compile(source, "install_service.sh", "exec"), {})
                    data = plistlib.loads(plist.read_bytes())
                    expected = str(executable) if framework_exists else "/selected/python3"
                    self.assertEqual(data["ProgramArguments"], [expected, "-u", str(root / "run.py")])
                    self.assertEqual(data["EnvironmentVariables"]["REPORTS_FAKE_PROVIDER"], "0")
                    self.assertEqual(data["EnvironmentVariables"]["PORT"], "8765")
                    self.assertIn(expected, output.getvalue())
                    if framework_exists:
                        self.assertIn(str(executable.parents[2]), output.getvalue())
