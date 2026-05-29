"""
离线文件保险箱 - 哈希校验模块

支持 MD5、SHA-1、SHA-256 三种哈希算法。
"""

import os
import hashlib
from typing import Dict


# 大文件分块读取大小（64KB）
CHUNK_SIZE = 64 * 1024


def compute_hashes(filepath: str) -> Dict[str, str]:
    """
    计算文件的 MD5、SHA-1、SHA-256 哈希值。

    使用分块读取方式，支持大文件处理。

    Args:
        filepath: 文件路径

    Returns:
        字典，键为算法名称，值为十六进制哈希字符串。
        例如: {"MD5": "d41d8cd9...", "SHA-1": "da39a3ee...", "SHA-256": "e3b0c44..."}

    Raises:
        FileNotFoundError: 文件不存在
        IOError: 读取文件出错
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")

    if not os.path.isfile(filepath):
        raise ValueError(f"路径不是文件: {filepath}")

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)

    return {
        "MD5": md5.hexdigest(),
        "SHA-1": sha1.hexdigest(),
        "SHA-256": sha256.hexdigest(),
    }
