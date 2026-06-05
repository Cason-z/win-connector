from __future__ import annotations

from datetime import datetime, timezone

from win_connector.models import ConnectionCreateRequest, ConnectionProfile, ConnectionUpdateRequest
from win_connector.storage import JSONStorage


class ConnectionService:
    def __init__(self, storage: JSONStorage) -> None:
        self.storage = storage

    def list_connections(self) -> list[ConnectionProfile]:
        return self.storage.load()

    def get_connection(self, connection_id: str) -> ConnectionProfile:
        for profile in self.storage.load():
            if profile.id == connection_id:
                return profile
        raise KeyError(f"Connection not found: {connection_id}")

    def create_connection(self, request: ConnectionCreateRequest) -> ConnectionProfile:
        profiles = self.storage.load()
        profile = ConnectionProfile(**request.model_dump())
        profiles.append(profile)
        self.storage.save(profiles)
        return profile

    def update_connection(self, connection_id: str, request: ConnectionUpdateRequest) -> ConnectionProfile:
        profiles = self.storage.load()
        for index, profile in enumerate(profiles):
            if profile.id != connection_id:
                continue
            update_data = request.model_dump(exclude_none=True)
            next_protocol = update_data.get("protocol", profile.protocol)
            if "protocol_config" in update_data and update_data["protocol_config"].protocol != next_protocol:
                raise ValueError("Updated protocol_config must match updated protocol")
            merged = profile.model_copy(
                update={
                    **update_data,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            profiles[index] = merged
            self.storage.save(profiles)
            return merged
        raise KeyError(f"Connection not found: {connection_id}")

    def delete_connection(self, connection_id: str) -> None:
        profiles = self.storage.load()
        filtered = [profile for profile in profiles if profile.id != connection_id]
        if len(filtered) == len(profiles):
            raise KeyError(f"Connection not found: {connection_id}")
        self.storage.save(filtered)
