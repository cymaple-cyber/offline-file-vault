#!/usr/bin/env python3
"""
离线文件保险箱 - 应用程序入口

使用方法：
    python main.py
    或
    bash run.sh
"""

import sys
import os

# ── macOS: 自动检测并切换到可用的 Python 环境 ──
MINICONDA_PYTHON = "/opt/miniconda3/bin/python3"

if sys.platform == "darwin":
    # 如果当前 Python 来自 Desktop 下的 .venv（已知有 PySide6 兼容问题），
    # 且 miniconda Python 可用，则自动切换
    if (
        "Desktop/.venv" in sys.executable
        and os.path.isfile(MINICONDA_PYTHON)
        and sys.executable != MINICONDA_PYTHON
    ):
        os.execv(MINICONDA_PYTHON, [MINICONDA_PYTHON] + sys.argv)

    # 配置 Qt 运行环境
    try:
        import PySide6
    except ImportError:
        print("错误：未找到 PySide6，请先安装依赖：")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    pyside6_root = os.path.dirname(PySide6.__file__)
    qt_plugins = os.path.join(pyside6_root, "Qt", "plugins")
    qt_platforms = os.path.join(qt_plugins, "platforms")
    qt_lib = os.path.join(pyside6_root, "Qt", "lib")
    cocoa_plugin = os.path.join(qt_platforms, "libqcocoa.dylib")

    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_platforms
    os.environ["QT_PLUGIN_PATH"] = qt_plugins
    os.environ["DYLD_LIBRARY_PATH"] = qt_lib

    # 预检 cocoa 插件
    if not os.path.isfile(cocoa_plugin):
        print(f"错误：未找到 cocoa 插件 ({cocoa_plugin})")
        print("请重新安装 PySide6：pip install --force-reinstall PySide6")
        sys.exit(1)

    import ctypes
    try:
        ctypes.CDLL(cocoa_plugin, ctypes.RTLD_GLOBAL)
    except OSError as e:
        print(f"错误：无法加载 cocoa 插件 ({cocoa_plugin})")
        print(f"原因: {e}")
        print("请重新安装 PySide6：pip install --force-reinstall PySide6")
        sys.exit(1)

    print(f"[离线文件保险箱] Python: {sys.executable}")

# ── 启动应用 ──
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.app import main

if __name__ == "__main__":
    main()
