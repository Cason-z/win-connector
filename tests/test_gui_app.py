import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from win_connector.gui import WinConnectorApp
from win_connector.models import ConnectionCreateRequest, DeviceTemplate, Protocol, SSHConfig
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

    def create_ssh_profile(self):
        profile = self.app.service.create_connection(
            ConnectionCreateRequest(
                name="Edge SSH",
                protocol=Protocol.SSH,
                group="edge",
                tags=[],
                notes="",
                device_template=DeviceTemplate.LINUX,
                protocol_config=SSHConfig(host="10.0.0.5", port=2222, username="admin"),
            )
        )
        self.app.refresh()
        self.app.tree.selection_set(profile.id)
        return profile

    def test_actions_panel_exposes_xpipe_like_workflows(self) -> None:
        required = [
            "open_terminal_button",
            "open_files_button",
            "copy_command_button",
            "start_tunnel_button",
            "service_local_port_var",
            "service_remote_host_var",
            "service_remote_port_var",
        ]

        for attribute in required:
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(self.app, attribute))

    def test_builds_terminal_file_and_tunnel_commands_for_ssh(self) -> None:
        profile = self.create_ssh_profile()

        self.app.service_local_port_var.set("8080")
        self.app.service_remote_host_var.set("127.0.0.1")
        self.app.service_remote_port_var.set("80")

        self.assertEqual(
            self.app._terminal_command(profile),
            ["ssh", "-p", "2222", "admin@10.0.0.5"],
        )
        self.assertEqual(
            self.app._files_command(profile),
            ["sftp", "-P", "2222", "admin@10.0.0.5"],
        )
        self.assertEqual(
            self.app._tunnel_command(profile),
            ["ssh", "-N", "-L", "8080:127.0.0.1:80", "-p", "2222", "admin@10.0.0.5"],
        )

    def test_copy_command_places_terminal_command_on_clipboard(self) -> None:
        self.create_ssh_profile()

        self.app.copy_launch_command()

        self.assertEqual(self.app.root.clipboard_get(), "ssh -p 2222 admin@10.0.0.5")

    def test_quick_add_populates_session_list_for_mobaxterm_flow(self) -> None:
        self.app.quick_name_var.set("Jump Host")
        self.app.quick_host_var.set("10.0.0.20")

        self.app.quick_add_connection()

        self.assertGreater(self.app.session_list.size(), 0)
        self.assertIn("Jump Host", self.app.session_list.get(0))
        self.assertTrue(hasattr(self.app, "session_tree"))
        self.assertTrue(self.app.session_tree.exists("profile::" + self.app.service.list_connections()[0].id))

    def test_quick_add_creates_web_profile_for_stored_web_sessions(self) -> None:
        self.app.quick_protocol_var.set(self.app._display_from_value(self.app.quick_protocol_map, Protocol.WEB.value))
        self.app.quick_template_var.set(self.app._display_from_value(self.app.quick_template_map, DeviceTemplate.WEB_APP.value))
        self.app.quick_name_var.set("Router UI")
        self.app.quick_host_var.set("10.0.0.1")
        self.app.quick_username_var.set("admin")
        self.app.quick_password_var.set("secret")

        self.app.quick_add_connection()

        profile = self.app.service.list_connections()[0]
        self.assertEqual(profile.protocol, Protocol.WEB)
        self.assertEqual(profile.device_template, DeviceTemplate.WEB_APP)
        self.assertEqual(profile.protocol_config.url, "https://10.0.0.1")
        self.assertEqual(profile.protocol_config.username, "admin")
        self.assertEqual(profile.protocol_config.password, "secret")

    def test_open_terminal_tab_embeds_session_in_workspace(self) -> None:
        self.create_ssh_profile()

        with patch("win_connector.gui.start_gui_session_tab") as start_tab:
            self.app.open_terminal_tab()

        self.assertGreaterEqual(len(self.app.terminal_notebook.tabs()), 1)
        start_tab.assert_called_once()


if __name__ == "__main__":
    unittest.main()
