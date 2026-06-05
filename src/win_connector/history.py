from __future__ import annotations

import json
import threading
from pathlib import Path

from pydantic import ValidationError

from win_connector.config import default_task_history_path
from win_connector.models import TaskRecord


class TaskHistoryStore:
    def __init__(self, path: Path | None = None, limit: int = 200) -> None:
        self.path = path or default_task_history_path()
        self.limit = limit
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def load(self) -> list[TaskRecord]:
        with self._lock:
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid task history file: {self.path}") from exc
        records: list[TaskRecord] = []
        for item in payload:
            try:
                records.append(TaskRecord.model_validate(item))
            except ValidationError:
                continue
        return records

    def recent(self, limit: int = 20) -> list[TaskRecord]:
        records = self.load()
        return list(reversed(records[-limit:]))

    def append(self, record: TaskRecord) -> TaskRecord:
        with self._lock:
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid task history file: {self.path}") from exc
            payload.append(record.model_dump(mode="json"))
            if len(payload) > self.limit:
                payload = payload[-self.limit :]
            self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return record
