import unittest
from pathlib import Path
from unittest.mock import patch

import sys
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from win_connector.gui import ConnectionEditor
from win_connector.i18n import I18N
from win_connector.models import Protocol


@unittest.skipUnless(bool(getattr(tk, "Tk", None)), "tkinter is unavailable")
class ConnectionEditorCredentialTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"tkinter display is unavailable: {exc}")
        self.root.withdraw()

    def tearDown(self) -> None:
        self.root.destroy()

    def make_editor(self) -> ConnectionEditor:
        editor = ConnectionEditor(self.root, I18N("en-US"))
        editor.window.withdraw()
        return editor

    def test_ssh_and_telnet_render_masked_password_controls(self) -> None:
        editor = self.make_editor()

        for protocol in (Protocol.SSH, Protocol.TELNET):
            with self.subTest(protocol=protocol.value):
                editor.vars["protocol"].set(protocol.value)
                editor._render_protocol_fields()

                self.assertIsNotNone(editor.password_entry)
                self.assertIsNotNone(editor.password_toggle)
                self.assertEqual(editor.password_entry.cget("show"), "*")

    def test_serial_and_rdp_hide_password_controls(self) -> None:
        editor = self.make_editor()

        for protocol in (Protocol.SERIAL, Protocol.RDP):
            with self.subTest(protocol=protocol.value):
                editor.vars["protocol"].set(protocol.value)
                editor._render_protocol_fields()

                self.assertIsNone(editor.password_entry)
                self.assertIsNone(editor.password_toggle)

    def test_toggle_password_visibility(self) -> None:
        editor = self.make_editor()
        editor.vars["protocol"].set(Protocol.SSH.value)
        editor._render_protocol_fields()

        self.assertEqual(editor.password_entry.cget("show"), "*")
        editor.show_password_var.set(True)
        editor._sync_password_visibility()
        self.assertEqual(editor.password_entry.cget("show"), "")


if __name__ == "__main__":
    unittest.main()
