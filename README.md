# Win Connector

Win Connector is a local session workspace for Windows-oriented operators, agents, and skills. The Windows GUI now follows a MobaXterm/XPipe-style workflow: a persistent session library on the left, embedded terminal tabs in the center, and profile details plus launch actions on the right.

## Positioning

- Local connection hub for `SSH`, `Telnet`, `Serial (COM)`, `RDP`, and stored `Web` sessions
- Usable by humans through a bilingual (`????` / `English`) sci-fi GUI
- Usable by large models, agents, and skills through structured local HTTP APIs and JSON-first CLI commands
- Designed for device inspection flows: connection profiles, device templates, command presets, and recent task history

## Features

- Save and manage connection profiles in local JSON
- Device templates: `linux`, `cisco_ios`, `h3c`, `huawei`, `juniper`, `firewall_generic`, `serial_console`, `web_app`
- Launch interactive connections:
  - `SSH` / `Telnet` / `Serial`: embedded GUI session or CLI inline session
  - `RDP`: launch Windows `mstsc`
  - `Web`: open saved URLs in the system browser with local username/password storage
- Execute automation tasks:
  - `SSH` / `Telnet`: execute a single command and return structured output
  - `Serial`: send text and read response with timeout
  - `RDP`: return structured unsupported result for remote command execution
  - `Web`: return structured unsupported result for shell command execution
- Save recent task history locally
- Test connections through CLI/API/GUI
- Built-in command presets for common device templates
- Local FastAPI service for skill or agent invocation

## Project Structure

```text
src/win_connector/
  api.py
  cli.py
  executors.py
  gui.py
  history.py
  models.py
  presets.py
  service.py
  sessions.py
  tasks.py
README.md
requirements.txt
docs/architecture.md
examples/sample_connections.json
scripts/build_windows.ps1
scripts/build_windows.sh
win_connector.spec
```

## Requirements

- Python 3.11+
- Windows 10/11 recommended for GUI and RDP launch
- `paramiko`, `pyserial`, `fastapi`, `uvicorn`, `pydantic`
- `PyInstaller` for packaging

## Install

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If running from source without packaging:

```powershell
$env:PYTHONPATH = "$PWD\src"
```

## Storage Paths

Default Windows data files:

```text
%APPDATA%\WinConnector\connections.json
%APPDATA%\WinConnector\task_history.json
%APPDATA%\WinConnector\win_connector.log
```

Non-Windows fallback:

```text
~/.win_connector/connections.json
~/.win_connector/task_history.json
~/.win_connector/win_connector.log
```

## GUI

Run the GUI:

```powershell
python -m win_connector gui
```

Pick language explicitly:

```powershell
python -m win_connector gui --lang zh-CN
python -m win_connector gui --lang en-US
```

GUI capabilities:

- left-side session library grouped by environment/customer/device role
- quick connect row for name, protocol, host or URL, port, username, password, and group
- double-click a session in the left library to open it
- embedded terminal tabs for `SSH`, `Telnet`, and `Serial`
- native launch for `RDP` and `Web`
- right-side launchpad for terminal, SFTP files, launch command copy, SSH tunnel, edit, delete, and refresh
- task panel for command presets, custom commands, connection testing, structured output, and recent task history

After adding a profile, it appears immediately in the left Session Library. Select it and press `Terminal`, or double-click it. The storage path is shown in the bottom status bar.

## CLI

List connections:

```powershell
python -m win_connector list --json
```

Create an SSH profile:

```powershell
python -m win_connector add `
  --name "Linux 01" `
  --protocol ssh `
  --host 10.0.0.10 `
  --username admin `
  --group lab/linux `
  --tags linux,prod
```

Create a Web profile:

```powershell
python -m win_connector add `
  --name "Router UI" `
  --protocol web `
  --url http://10.0.0.1 `
  --username admin `
  --password secret `
  --group network/web
```

Create a template-driven Cisco profile:

```powershell
python -m win_connector add `
  --name "Core Switch" `
  --template cisco_ios `
  --host 10.0.0.20 `
  --username admin `
  --group network/core `
  --tags switch,cisco
```

Create a serial console profile:

```powershell
python -m win_connector add `
  --name "Console COM3" `
  --protocol serial `
  --port-name COM3 `
  --baudrate 9600 `
  --group oob
```

Show or delete:

```powershell
python -m win_connector show <connection-id> --json
python -m win_connector delete <connection-id> --json
```

Interactive connect:

```powershell
python -m win_connector connect <connection-id> --json
```

Execute a task:

```powershell
python -m win_connector execute <connection-id> --command "show version" --json
python -m win_connector execute <connection-id> --preset cisco_show_version --json
```

Test a connection:

```powershell
python -m win_connector test <connection-id> --json
```

Query recent tasks:

```powershell
python -m win_connector tasks --limit 10 --json
```

CLI returns structured JSON for automation-oriented commands.

## HTTP API

Start the local API:

```powershell
python -m win_connector serve-api --host 127.0.0.1 --port 8000
```

Available endpoints:

- `GET /health`
- `GET /connections`
- `POST /connections`
- `GET /connections/{id}`
- `POST /connections/{id}/connect`
- `POST /connections/{id}/test`
- `GET /connections/{id}/presets`
- `POST /tasks/execute`
- `GET /tasks/history`

### Task Response Shape

`POST /tasks/execute` returns JSON like:

```json
{
  "status": "success",
  "protocol": "ssh",
  "connection_id": "9f2c...",
  "command": "show version",
  "mode": "single",
  "preset_id": "cisco_show_version",
  "stdout": "...",
  "stderr": "",
  "exit_code": 0,
  "duration_ms": 184,
  "started_at": "2026-06-05T12:00:00+00:00",
  "message": "ssh_exec_completed"
}
```

### Agent / Skill Usage

Typical large-model automation flow:

1. `GET /connections`
2. Select target by `id`, `group`, `protocol`, `tags`, or `device_template`
3. Optionally `GET /connections/{id}/presets`
4. `POST /connections/{id}/test`
5. `POST /tasks/execute`
6. `GET /tasks/history?limit=10`

This makes Win Connector suitable as a local skill backend or agent-side tool adapter.

### curl Examples

Health:

```bash
curl http://127.0.0.1:8000/health
```

List connections:

```bash
curl http://127.0.0.1:8000/connections
```

Create a connection:

```bash
curl -X POST http://127.0.0.1:8000/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Agent Linux",
    "protocol": "ssh",
    "group": "agents",
    "tags": ["linux", "agent"],
    "notes": "Created by API",
    "device_template": "linux",
    "protocol_config": {
      "protocol": "ssh",
      "host": "10.0.0.50",
      "port": 22,
      "username": "admin",
      "password": ""
    }
  }'
```

Test a connection:

```bash
curl -X POST http://127.0.0.1:8000/connections/<connection-id>/test \
  -H "Content-Type: application/json" \
  -d '{"timeout": 5}'
```

Get recommended presets for a device template:

```bash
curl http://127.0.0.1:8000/connections/<connection-id>/presets
```

Execute a command:

```bash
curl -X POST http://127.0.0.1:8000/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "<connection-id>",
    "command": "show ip int brief",
    "timeout": 8,
    "mode": "single"
  }'
```

Execute by preset:

```bash
curl -X POST http://127.0.0.1:8000/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "<connection-id>",
    "preset_id": "cisco_show_version",
    "timeout": 8,
    "mode": "single"
  }'
```

Read recent task history:

```bash
curl "http://127.0.0.1:8000/tasks/history?limit=10"
```

## Example Configuration

Sample profiles are in [examples/sample_connections.json](/workspace/win-connector/examples/sample_connections.json).

On Windows:

```powershell
Copy-Item .\examples\sample_connections.json $env:APPDATA\WinConnector\connections.json
```

## Windows Packaging

This repository now includes a PyInstaller spec, local helper scripts, and GitHub Actions workflows for building a Windows x86_64 GUI package.

### Local Windows One-Click Build

On Windows x86_64:

```powershell
.\scripts\build_windows.ps1
```

This script:

- creates or reuses `.venv`
- installs `requirements.txt`
- installs `pyinstaller`
- builds from `win_connector.spec`

Expected output:

```text
dist\WinConnector\
```

### Shell Build Variant

On Git Bash / WSL / Linux for script preparation:

```bash
./scripts/build_windows.sh
```

Note: the current Linux environment can validate the build script and spec, but cannot reliably produce a runnable Windows `.exe` without a Windows build host and Windows-compatible packaging environment.

### Manual PyInstaller Build

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm win_connector.spec
```

## GitHub Actions

### 1. Windows 自动构建

仓库已包含：

- `.github/workflows/windows-build.yml`

触发条件：
- push 到 `main`
- 对 `main` 发起 PR
- 手动 `workflow_dispatch`

这个工作流会：
- 在 `windows-latest` 上使用 Python 3.11 x64
- 安装依赖与 PyInstaller
- 执行 `compileall`
- 验证 CLI 帮助命令
- 运行 `scripts/build_windows.ps1`
- 上传 `WinConnector-windows-x86_64.zip` 构建产物

### 2. Release 自动发布

仓库已包含：

- `.github/workflows/release.yml`

触发条件：
- push tag：`v*`
- 手动 `workflow_dispatch`

这个工作流会：
- 在 Windows runner 上构建 GUI 包
- 自动打包为 zip
- 创建 GitHub Release
- 上传 zip 作为 release asset

### 3. 推荐发布流程

#### 自动构建验证
直接 push 到 `main`，然后在 GitHub Actions 查看 `windows-build`。

#### 正式发版
本地执行：

```bash
git tag v0.1.0
git push origin v0.1.0
```

推送 tag 后，`release.yml` 会自动：
- 构建 Windows x86_64 版本
- 创建 release
- 上传产物

## CI / 验证建议

当前最基础的 CI 校验已经覆盖：
- Python 源码可编译
- CLI 关键入口可启动
- Windows 打包链可执行

后续可以继续增强：
- 增加 API smoke tests
- 增加任务执行单元测试
- 增加 GUI 结构性测试（非桌面依赖部分）

## Architecture

See [docs/architecture.md](/workspace/win-connector/docs/architecture.md).

## Current Limits

- credentials are stored in plain local JSON
- Telnet single-command execution is best-effort and prompt-driven, not a full terminal emulator
- embedded session windows are intentionally basic
- RDP task execution returns structured unsupported status instead of attempting remote shell execution
