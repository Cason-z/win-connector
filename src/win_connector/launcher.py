from __future__ import annotations

import logging

from win_connector.models import ConnectResult, ConnectionProfile, Protocol
from win_connector.sessions import connect_serial_console, connect_ssh_console, connect_telnet_console, open_rdp_external, start_gui_session_window

logger = logging.getLogger(__name__)


class ConnectionLauncher:
    def connect(self, profile: ConnectionProfile, mode: str = "auto", root=None) -> ConnectResult:
        logger.info("Launching connection %s (%s)", profile.id, profile.protocol.value)
        if root is not None:
            return start_gui_session_window(profile, root)
        if profile.protocol == Protocol.RDP:
            return open_rdp_external(profile)
        if profile.protocol == Protocol.SSH:
            return connect_ssh_console(profile)
        if profile.protocol == Protocol.TELNET:
            return connect_telnet_console(profile)
        if profile.protocol == Protocol.SERIAL:
            return connect_serial_console(profile)
        raise RuntimeError(f"Unsupported protocol: {profile.protocol}")
