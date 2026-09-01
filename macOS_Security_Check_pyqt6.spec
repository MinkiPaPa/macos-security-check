# -*- mode: python ; coding: utf-8 -*-
import os

# 프로젝트 루트 디렉토리 경로
project_root = os.path.abspath(SPECPATH)

a = Analysis(
    ['main_gui_app.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'assets'), 'assets'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'reportlab.platypus',
        'PIL',
        'PIL.Image',
        'requests',
        'urllib3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='macOS Security Check',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='macOS Security Check',
)

app = BUNDLE(
    coll,
    name='macOS Security Check.app',
    icon=os.path.join(project_root, 'assets', 'app_icon.icns'),
    bundle_identifier='com.ncskorea.macos-security-check',
)
