import unittest
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


if __name__ == "__main__":
    unittest.main()
