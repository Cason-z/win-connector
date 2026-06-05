from __future__ import annotations

import logging
from pathlib import Path

from win_connector.config import default_log_path


def setup_logging(log_path: Path | None = None) -> None:
    path = log_path or default_log_path()
    if logging.getLogger().handlers:
        return
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.insert(0, logging.FileHandler(path, encoding="utf-8"))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
    )
