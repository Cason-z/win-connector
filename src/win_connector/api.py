from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from win_connector.models import (
    ConnectResult,
    ConnectionCreateRequest,
    ConnectionProfile,
    ConnectionTestRequest,
    HealthResponse,
    TaskExecuteRequest,
    TaskExecutionResult,
    TaskRecord,
    TaskTestResult,
)
from win_connector.launcher import ConnectionLauncher
from win_connector.service import ConnectionService
from win_connector.storage import JSONStorage
from win_connector.tasks import TaskService
from win_connector.config import task_history_path_for


def create_app(storage_path: Path | None = None) -> FastAPI:
    storage = JSONStorage(storage_path)
    service = ConnectionService(storage)
    launcher = ConnectionLauncher()
    task_service = TaskService(task_history_path_for(storage.path))
    app = FastAPI(title="Win Connector API", version="0.2.0")

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", storage_path=str(storage.path))

    @app.get("/connections", response_model=list[ConnectionProfile])
    def list_connections() -> list[ConnectionProfile]:
        return service.list_connections()

    @app.post("/connections", response_model=ConnectionProfile)
    def create_connection(request: ConnectionCreateRequest) -> ConnectionProfile:
        return service.create_connection(request)

    @app.get("/connections/{connection_id}", response_model=ConnectionProfile)
    def get_connection(connection_id: str) -> ConnectionProfile:
        try:
            return service.get_connection(connection_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/connections/{connection_id}/connect", response_model=ConnectResult)
    def connect(connection_id: str) -> ConnectResult:
        try:
            profile = service.get_connection(connection_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            return launcher.connect(profile)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/connections/{connection_id}/test", response_model=TaskTestResult)
    def test_connection(connection_id: str, request: ConnectionTestRequest | None = None) -> TaskTestResult:
        try:
            profile = service.get_connection(connection_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            return task_service.test(profile, timeout=(request.timeout if request else 5.0))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/tasks/execute", response_model=TaskExecutionResult)
    def execute_task(request: TaskExecuteRequest) -> TaskExecutionResult:
        try:
            profile = service.get_connection(request.connection_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            return task_service.execute(profile, request)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/tasks/history", response_model=list[TaskRecord])
    def tasks_history(limit: int = 20) -> list[TaskRecord]:
        return task_service.recent_history(limit=limit)

    @app.get("/connections/{connection_id}/presets")
    def connection_presets(connection_id: str) -> list[dict[str, object]]:
        try:
            profile = service.get_connection(connection_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return task_service.presets(profile.device_template)

    return app
