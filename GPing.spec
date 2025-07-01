# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get CustomTkinter path
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

# Get Python DLL directory
python_dll_path = os.path.join(sys.base_prefix, 'DLLs')

a = Analysis(
    ['ping_tool.py'],
    pathex=[python_dll_path],  # Add Python DLL path
    binaries=[
        ('tcping.exe', '.'),
        (os.path.join(sys.base_prefix, 'python311.dll'), '.'),  # Include Python DLL
    ],
    datas=[
        ('gping_settings.json', '.'),
        ('README.md', '.'),
        ('GPing.ico', '.'),
    ] + collect_data_files('customtkinter'),
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'PIL._tkinter_finder',
        '_tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.colorchooser',
        'tkinter.commondialog',
        'tkinter.font',
    ] + collect_submodules('customtkinter'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False
)

# Add all DLL files from Python's DLLs directory
for dll_file in os.listdir(python_dll_path):
    if dll_file.lower().endswith('.dll'):
        dll_path = os.path.join(python_dll_path, dll_file)
        a.binaries.append((dll_file, dll_path, 'BINARY'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GPing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='GPing.ico',
    uac_admin=True
)