from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "Win Connector"


def default_data_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "WinConnector"
    return Path.home() / ".win_connector"


def default_storage_path() -> Path:
    return default_data_dir() / "connections.json"


def default_log_path() -> Path:
    return default_data_dir() / "win_connector.log"


def default_task_history_path() -> Path:
    return default_data_dir() / "task_history.json"


def task_history_path_for(storage_path: Path) -> Path:
    return storage_path.with_name("task_history.json")
