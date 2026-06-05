# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path.cwd()
SRC = ROOT / "src"

block_cipher = None

a = Analysis(
    [str(SRC / "win_connector" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "win_connector.api",
        "win_connector.cli",
        "win_connector.executors",
        "win_connector.gui",
        "win_connector.history",
        "win_connector.i18n",
        "win_connector.launcher",
        "win_connector.models",
        "win_connector.presets",
        "win_connector.service",
        "win_connector.sessions",
        "win_connector.storage",
        "win_connector.tasks",
        "win_connector.templates",
        "win_connector.theme",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="WinConnector",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
