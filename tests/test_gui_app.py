import tempfile
import unittest
from pathlib import Path

import sys
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from win_connector.gui import WinConnectorApp
from win_connector.service import ConnectionService
from win_connector.storage import JSONStorage


@unittest.skipUnless(bool(getattr(tk, "Tk", None)), "tkinter is unavailable")
class WinConnectorAppQuickAddTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        storage_path = Path(self.tmpdir.name) / "connections.json"
        service = ConnectionService(JSONStorage(storage_path))
        try:
            self.app = WinConnectorApp(service, language="en-US")
        except tk.TclError as exc:
            self.tmpdir.cleanup()
            self.skipTest(f"tkinter display is unavailable: {exc}")
        self.app.root.withdraw()

    def tearDown(self) -> None:
        self.app.root.destroy()
        self.tmpdir.cleanup()

    def test_quick_add_form_exposes_connection_credentials(self) -> None:
        required = [
            "quick_name_var",
            "quick_host_var",
            "quick_port_var",
            "quick_username_var",
            "quick_password_var",
            "quick_group_var",
            "quick_add_button",
            "quick_password_entry",
        ]

        for attribute in required:
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(self.app, attribute))

        self.assertEqual(self.app.quick_password_entry.cget("show"), "*")

    def test_quick_add_creates_ssh_profile(self) -> None:
        self.app.quick_name_var.set("Core Switch")
        self.app.quick_host_var.set("10.0.0.10")
        self.app.quick_port_var.set("2222")
        self.app.quick_username_var.set("admin")
        self.app.quick_password_var.set("pw")
        self.app.quick_group_var.set("network/core")

        self.app.quick_add_connection()

        profiles = self.app.service.list_connections()
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]
        self.assertEqual(profile.name, "Core Switch")
        self.assertEqual(profile.group, "network/core")
        self.assertEqual(profile.protocol_config.host, "10.0.0.10")
        self.assertEqual(profile.protocol_config.port, 2222)
        self.assertEqual(profile.protocol_config.username, "admin")
        self.assertEqual(profile.protocol_config.password, "pw")

    def test_add_group_keeps_group_available_before_profiles_exist(self) -> None:
        self.app.new_group_var.set("lab/core")

        self.app.add_group()

        self.assertEqual(self.app.quick_group_var.get(), "lab/core")
        self.assertIn("lab/core", self.app.group_combo.cget("values"))


if __name__ == "__main__":
    unittest.main()
