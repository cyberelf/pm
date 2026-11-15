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
    def test_plist_reports_the_entry_point_that_needs_authorization(self):
        script = (Path(__file__).resolve().parents[1] / "scripts/install_service.sh").read_text()
        source = script.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plist = root / "service.plist"
            args = ["-", str(plist), str(root), "8765", "0", "/usr/bin:/bin", "", "8443"]
            output = io.StringIO()
            with mock.patch.object(sys, "argv", args), mock.patch.object(
                sys, "executable", "/framework/python3"
            ), contextlib.redirect_stdout(output):
                exec(compile(source, "install_service.sh", "exec"), {})
            data = plistlib.loads(plist.read_bytes())
            self.assertEqual(data["ProgramArguments"], ["/usr/bin/python3", "-u", str(root / "run.py")])
            self.assertEqual(data["EnvironmentVariables"]["REPORTS_SERVICE_PYTHON"], "/usr/bin/python3")
            self.assertEqual(data["EnvironmentVariables"]["REPORTS_FAKE_PROVIDER"], "0")
            self.assertEqual(data["EnvironmentVariables"]["PORT"], "8765")
            self.assertIn("Full Disk Access to: /usr/bin/python3", output.getvalue())
