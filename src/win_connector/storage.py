from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from win_connector.config import default_storage_path
from win_connector.models import ConnectionProfile

logger = logging.getLogger(__name__)


class JSONStorage:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_storage_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save([])

    def load(self) -> list[ConnectionProfile]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON storage file: {self.path}") from exc
        profiles: list[ConnectionProfile] = []
        for item in data:
            try:
                profiles.append(ConnectionProfile.model_validate(item))
            except ValidationError as exc:
                logger.warning("Skip invalid profile in %s: %s", self.path, exc)
        return profiles

    def save(self, profiles: list[ConnectionProfile]) -> None:
        payload = [profile.model_dump(mode="json") for profile in profiles]
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
