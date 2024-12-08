# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.win32 import winmanifest

block_cipher = None

# Get CustomTkinter path
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

# Get the directory containing the spec file
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    ['ping_tool.py'],
    pathex=[],
    binaries=[],  
    datas=[
        ('gping_settings.json', '.'),  
        ('README.md', '.'),  
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'csv',
        'json',
        'datetime',
        'threading',
        'subprocess',
        're',
        'socket',
        'ctypes',
        'PIL._tkinter_finder',  
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'pandas', 'matplotlib'],  
    noarchive=False,
    optimize=2,  
)

# Add customtkinter files
try:
    a.datas += Tree(ctk_path, prefix='customtkinter', excludes=['*.pyc'])
except ImportError:
    pass

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='GPing.ico',  
    version='file_version_info.txt',
    uac_admin=True,  
)
