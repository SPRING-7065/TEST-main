"""
PyInstaller 打包配置文件
使用方法：pyinstaller build.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# ── 收集依赖数据文件 ──────────────────────────────────────
# PySide6 数据文件
pyside6_datas = collect_data_files('PySide6')

# DrissionPage 数据文件
drissionpage_datas = collect_data_files('DrissionPage')

# 项目自身的资源文件
project_datas = [
    ('assets', 'assets'),          # 图标等资源
]

all_datas = (
    pyside6_datas
    + drissionpage_datas
    + project_datas
)

# ── 隐式导入（防止被PyInstaller漏掉）────────────────────
hidden_imports = [
    # PySide6
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',

    # DrissionPage
    'DrissionPage',
    'DrissionPage._pages.chromium_page',
    'DrissionPage._pages.chromium_tab',
    'DrissionPage._configs.chromium_options',

    # keyring 后端：PyInstaller 静态分析无法发现，必须显式列出
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'keyring.backends.macOS',
    'keyring.backends.SecretService',
    'keyring.backends.fail',
    'keyring.backends.null',
    'jaraco.classes',
    'jaraco.context',
    'jaraco.functools',

    # 标准库
    'json',
    'uuid',
    'threading',
    'datetime',
    'dataclasses',
    'enum',
    'copy',
    'shutil',
    're',
    'os',
    'sys',
    'time',

    # 项目模块
    'models',
    'models.task',
    'models.step',
    'storage',
    'storage.task_store',
    'core',
    'core.engine',
    'core.scheduler',
    'core.variable_parser',
    'core.file_manager',
    'core.logger',
    'gui',
    'gui.main_window',
    'gui.task_list_widget',
    'gui.task_editor_dialog',
    'gui.visual_picker_window',
    'gui.help_widget',
]

# ── 分析 ────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=all_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'tkinter',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── 打包 ────────────────────────────────────────────────
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,       # 使用文件夹模式（非单文件），启动更快
    name='WebAutoDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                    # 使用UPX压缩（需要安装UPX）
    console=False,               # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',      # 程序图标
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WebAutoDownloader',     # 输出文件夹名
)