# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置
将 HarmonyOS Device Tool 打包为 macOS .app，可内置 hdc 工具
"""

import os
import sys

block_cipher = None

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# 检查是否有内置 hdc 及依赖库
hdc_dir = os.path.join(PROJECT_ROOT, 'hdc')
hdc_binaries = []
hdc_datas = []

# macOS hdc
if os.path.exists(os.path.join(hdc_dir, 'hdc')):
    hdc_binaries.append((os.path.join(hdc_dir, 'hdc'), 'hdc'))
    if os.path.exists(os.path.join(hdc_dir, 'libusb_shared.dylib')):
        hdc_binaries.append((os.path.join(hdc_dir, 'libusb_shared.dylib'), '.'))

# Windows hdc
hdc_windows_dir = os.path.join(hdc_dir, 'windows')
if os.path.exists(os.path.join(hdc_windows_dir, 'hdc.exe')):
    hdc_binaries.append((os.path.join(hdc_windows_dir, 'hdc.exe'), 'hdc'))
    if os.path.exists(os.path.join(hdc_windows_dir, 'libusb_shared.dll')):
        hdc_binaries.append((os.path.join(hdc_windows_dir, 'libusb_shared.dll'), '.'))

a = Analysis(
    ['hap_installer.py'],
    pathex=[PROJECT_ROOT],
    binaries=hdc_binaries,
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'tkinter',
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.windows.widgets',
        'darkdetect',
        'packaging',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HarmonyOS Device Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HarmonyOS Device Tool',
)

app = BUNDLE(
    coll,
    name='HarmonyOS Device Tool.app',
    icon=os.path.join(PROJECT_ROOT, 'assets', 'icon.icns') if os.path.exists(os.path.join(PROJECT_ROOT, 'assets', 'icon.icns')) else None,
    bundle_identifier='com.harmonyos.devtool',
    version='1.0.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDisplayName': 'HarmonyOS Device Tool',
        'CFBundleName': 'HarmonyOS Device Tool',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.13.0',
    },
)