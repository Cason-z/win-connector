import unittest
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from win_connector import cli


class CLIDefaultGuiTests(unittest.TestCase):
    def test_no_arguments_launches_gui_for_double_click(self) -> None:
        with (
            patch("win_connector.gui.WinConnectorApp") as app_class,
            patch("win_connector.cli.JSONStorage"),
            patch("win_connector.cli.ConnectionService"),
        ):
            app = app_class.return_value

            exit_code = cli.main([])

        self.assertEqual(exit_code, 0)
        app_class.assert_called_once()
        app.run.assert_called_once_with()

    def test_add_web_profile_stores_url_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Path(tmpdir) / "connections.json"

            with redirect_stdout(StringIO()):
                exit_code = cli.main(
                    [
                        "--storage",
                        str(storage),
                        "add",
                        "--name",
                        "Router UI",
                        "--protocol",
                        "web",
                        "--url",
                        "http://10.0.0.1",
                        "--username",
                        "admin",
                        "--password",
                        "secret",
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            data = storage.read_text(encoding="utf-8")
            self.assertIn('"protocol": "web"', data)
            self.assertIn('"url": "http://10.0.0.1"', data)
            self.assertIn('"username": "admin"', data)


if __name__ == "__main__":
    unittest.main()
