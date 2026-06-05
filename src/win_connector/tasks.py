from __future__ import annotations

from pathlib import Path

from win_connector.executors import execute_task, test_connection
from win_connector.history import TaskHistoryStore
from win_connector.models import (
    ConnectionProfile,
    DeviceTemplate,
    TaskExecuteRequest,
    TaskExecutionResult,
    TaskRecord,
    TaskTestResult,
)
from win_connector.presets import presets_for_template


class TaskService:
    def __init__(self, history_path: Path | None = None) -> None:
        self.history = TaskHistoryStore(history_path)

    def execute(self, profile: ConnectionProfile, request: TaskExecuteRequest) -> TaskExecutionResult:
        result = execute_task(
            profile=profile,
            command=request.command,
            timeout=request.timeout,
            mode=request.mode,
            preset_id=request.preset_id,
        )
        self.history.append(TaskRecord.from_execution(profile, result))
        return result

    def test(self, profile: ConnectionProfile, timeout: float = 5.0) -> TaskTestResult:
        result = test_connection(profile, timeout=timeout)
        self.history.append(TaskRecord.from_test(profile, result))
        return result

    def recent_history(self, limit: int = 20) -> list[TaskRecord]:
        return self.history.recent(limit=limit)

    def presets(self, template: DeviceTemplate) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for preset in presets_for_template(template):
            records.append(
                {
                    "id": preset.id,
                    "title": preset.title,
                    "title_zh": preset.title_zh,
                    "command": preset.command,
                    "templates": [item.value for item in preset.templates],
                }
            )
        return records
