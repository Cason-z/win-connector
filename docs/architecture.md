# Win Connector Architecture

## Goals

Win Connector is a local network operations connection hub for SSH, Telnet, Serial, and RDP. It serves both human operators and large-model-driven automation through a shared connection model, task execution APIs, history storage, and a Windows-friendly GUI.

## Layers

### 1. Domain Model

- `ConnectionProfile` is the unified connection object.
- `protocol_config` is a discriminated union of `SSHConfig`, `TelnetConfig`, `SerialConfig`, and `RDPConfig`.
- `DeviceTemplate` captures common device presets such as `linux`, `cisco_ios`, `huawei`, and `serial_console`.

This split keeps shared metadata (`group`, `tags`, `notes`, `device_template`) separate from protocol-specific fields.

### 2. Persistence

- `JSONStorage` reads and writes a local JSON file.
- Default Windows path: `%APPDATA%\WinConnector\connections.json`
- Non-Windows fallback: `~/.win_connector/connections.json`

The storage layer validates records on read and skips malformed profiles with a warning.

### 3. Service Layer

- `ConnectionService` owns CRUD logic.
- `TaskService` owns command execution, task history, connection testing, and preset lookup.
- It isolates CLI/GUI/API from storage details.
- This is the right place for future indexing, encryption, import/export, and sync logic.

### 4. Task Execution Layer

- `executors.py` provides protocol-specific single-task execution and test routines.
- `history.py` persists recent task records to local JSON.
- `presets.py` maps device templates to recommended inspection commands.
- `tasks.py` coordinates execution, testing, and history recording.

Execution behavior:

- SSH: executes a single remote command through `paramiko`
- Telnet: sends one command and captures best-effort output until idle/timeout
- Serial: sends text and reads response until timeout
- RDP: returns a structured unsupported response for command execution

### 5. Protocol Adapter / Launcher

- `ConnectionLauncher` routes a `ConnectionProfile` to the correct connector.
- SSH uses `paramiko`.
- Telnet uses `telnetlib`.
- Serial uses `pyserial`.
- RDP uses external launch via `mstsc /v:host`.

For GUI usage, SSH/Telnet/Serial open in a simple embedded session window. For CLI usage, SSH/Telnet/Serial run in a basic interactive console loop.

### 6. Interfaces

- CLI: `win-connector list/add/show/delete/connect/execute/test/tasks/serve-api/gui`
- GUI: `tkinter/ttk`
- HTTP API: FastAPI bound to `127.0.0.1` by default, with task execution and history routes

All interfaces operate on the same service layer and JSON storage.

## Extension Points

- Add new protocol models and session handlers, then register them in `ConnectionLauncher`.
- Add richer device templates in `templates.py`.
- Replace JSON persistence with SQLite later without changing API/GUI contracts.
- Add secure secret storage by moving credentials out of `ConnectionProfile` while keeping the same profile IDs.
- Replace best-effort Telnet parsing with prompt-aware vendor adapters if deeper automation is needed.

## Known MVP Limits

- Credentials are stored in plain JSON.
- Telnet task execution uses the stdlib implementation and only supports simple prompt-driven single commands.
- Embedded terminal windows are basic and not full VT emulators.
- RDP credential automation is intentionally omitted, and RDP task execution is reported as unsupported by design.
