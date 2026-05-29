#!/bin/bash
# 离线文件保险箱 启动脚本 (macOS)
# 自动选择可用的 Python 环境

cd "$(dirname "$0")"

# 优先使用 miniconda Python（已验证稳定）
if [ -x /opt/miniconda3/bin/python3 ]; then
    /opt/miniconda3/bin/python3 main.py
    exit $?
fi

# 回退：尝试 .venv
if [ -d "../.venv" ] && [ -x "../.venv/bin/python3" ]; then
    ../.venv/bin/python3 main.py
    exit $?
fi

# 最后：系统默认 python3
python3 main.py
