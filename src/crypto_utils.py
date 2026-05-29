"""
离线文件保险箱 - 加密解密核心模块

使用 AES-256-GCM 加密，PBKDF2HMAC-SHA256 密钥派生。

.cysafe 文件格式（版本 1）:
┌──────────┬──────────┬─────────────────────────────┐
│ 偏移     │ 大小     │ 字段                        │
├──────────┼──────────┼─────────────────────────────┤
│ 0        │ 4 字节   │ Magic Header: "CYSF"        │
│ 4        │ 1 字节   │ Version: 0x01               │
│ 5        │ 2 字节   │ Salt Length (uint16 BE)     │
│ 7        │ 2 字节   │ Nonce Length (uint16 BE)    │
│ 9        │ 2 字节   │ Filename Length (uint16 BE) │
│ 11       │ Ns 字节  │ Salt (PBKDF2)               │
│ 11+Ns    │ Nn 字节  │ Nonce (AES-GCM)             │
│ 11+Ns+Nn │ Nf 字节  │ Original Filename (UTF-8)   │
│ ...      │ M 字节   │ Ciphertext (含 16B auth tag)│
└──────────┴──────────┴─────────────────────────────┘
"""

import os
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

# --- 常量定义 ---

MAGIC_HEADER = b"CYSF"
VERSION = 1
SALT_SIZE = 16          # 128-bit salt
NONCE_SIZE = 12         # 96-bit nonce for GCM
KEY_SIZE = 32           # 256-bit AES key
PBKDF2_ITERATIONS = 600_000  # OWASP 推荐的 PBKDF2-SHA256 迭代次数

# 固定头部 = magic(4) + version(1) + salt_len(2) + nonce_len(2) + filename_len(2) = 11
HEADER_FIXED_SIZE = 11
LEN_FIELD_SIZE = 2      # uint16 大端序存储长度

# AES-GCM 认证标签大小为 16 字节
GCM_TAG_SIZE = 16


def derive_key(password: str, salt: bytes) -> bytes:
    """
    使用 PBKDF2HMAC-SHA256 从密码派生 256-bit AES 密钥。

    Args:
        password: 用户密码
        salt: 随机盐值

    Returns:
        32 字节的 AES-256 密钥
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def _read_exact(f, size: int, context: str) -> bytes:
    """读取精确字节数，读取不足则报错。"""
    data = f.read(size)
    if len(data) < size:
        raise ValueError("密码错误或文件已损坏")
    return data


def encrypt_file(input_path: str, output_path: str, password: str) -> None:
    """
    加密文件。

    使用 AES-256-GCM 加密文件内容，生成 .cysafe 格式的加密文件。

    Args:
        input_path: 原始文件路径
        output_path: 加密输出文件路径
        password: 加密密码
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    # 生成随机 salt 和 nonce
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)

    # 派生密钥
    key = derive_key(password, salt)

    # 读取原始文件内容
    with open(input_path, "rb") as f:
        plaintext = f.read()

    # AES-GCM 加密（密文末尾附带 16 字节认证标签）
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # 原始文件名（不含路径）
    original_filename = os.path.basename(input_path)
    filename_bytes = original_filename.encode("utf-8")

    if len(filename_bytes) > 65535:
        raise ValueError("文件名过长，最大支持 65535 字节")

    # 写入 .cysafe 文件
    with open(output_path, "wb") as f:
        f.write(MAGIC_HEADER)                              # 4B: magic
        f.write(bytes([VERSION]))                           # 1B: version
        f.write(struct.pack(">H", SALT_SIZE))               # 2B: salt_length
        f.write(struct.pack(">H", NONCE_SIZE))              # 2B: nonce_length
        f.write(struct.pack(">H", len(filename_bytes)))     # 2B: filename_length
        f.write(salt)                                       # salt
        f.write(nonce)                                      # nonce
        f.write(filename_bytes)                             # 原始文件名
        f.write(ciphertext)                                 # 密文（含 auth tag）


def decrypt_file(input_path: str, output_dir: str, password: str) -> str:
    """
    解密 .cysafe 文件。

    Args:
        input_path: .cysafe 文件路径
        output_dir: 解密输出目录
        password: 解密密码

    Returns:
        解密后的文件路径
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    with open(input_path, "rb") as f:
        # 1) Magic Header
        magic = _read_exact(f, 4, "magic")
        if magic != MAGIC_HEADER:
            raise ValueError("密码错误或文件已损坏")

        # 2) Version
        version_byte = _read_exact(f, 1, "version")
        version = version_byte[0]
        if version != VERSION:
            raise ValueError("密码错误或文件已损坏")

        # 3) Salt Length
        salt_len_bytes = _read_exact(f, LEN_FIELD_SIZE, "salt_len")
        salt_len = struct.unpack(">H", salt_len_bytes)[0]
        if salt_len < 8 or salt_len > 256:
            raise ValueError("密码错误或文件已损坏")

        # 4) Nonce Length
        nonce_len_bytes = _read_exact(f, LEN_FIELD_SIZE, "nonce_len")
        nonce_len = struct.unpack(">H", nonce_len_bytes)[0]
        if nonce_len < 8 or nonce_len > 64:
            raise ValueError("密码错误或文件已损坏")

        # 5) Filename Length
        filename_len_bytes = _read_exact(f, LEN_FIELD_SIZE, "filename_len")
        filename_len = struct.unpack(">H", filename_len_bytes)[0]
        if filename_len > 65535:
            raise ValueError("密码错误或文件已损坏")

        # 6) Salt
        salt = _read_exact(f, salt_len, "salt")

        # 7) Nonce
        nonce = _read_exact(f, nonce_len, "nonce")

        # 8) Original Filename
        filename_bytes = _read_exact(f, filename_len, "filename")
        try:
            original_filename = filename_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("密码错误或文件已损坏")

        # 9) Ciphertext (含 auth tag)
        ciphertext = f.read()
        if len(ciphertext) < GCM_TAG_SIZE:
            raise ValueError("密码错误或文件已损坏")

    # 派生密钥
    key = derive_key(password, salt)

    # AES-GCM 解密（自动验证认证标签）
    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag:
        raise ValueError("密码错误或文件已损坏")

    # 输出路径，处理同名冲突
    output_path = _resolve_output_path(output_dir, original_filename)

    with open(output_path, "wb") as f:
        f.write(plaintext)

    return output_path


def _resolve_output_path(output_dir: str, filename: str) -> str:
    """解决输出文件路径冲突。"""
    base_path = os.path.join(output_dir, filename)

    if not os.path.exists(base_path):
        return base_path

    name, ext = os.path.splitext(filename)
    counter = 1

    while True:
        new_filename = f"{name}({counter}){ext}"
        new_path = os.path.join(output_dir, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def verify_cysafe_file(filepath: str) -> bool:
    """
    验证文件是否为有效的 .cysafe 格式文件（不验证密码）。
    """
    try:
        if not os.path.isfile(filepath):
            return False

        with open(filepath, "rb") as f:
            # magic
            if f.read(4) != MAGIC_HEADER:
                return False

            # version
            vb = f.read(1)
            if len(vb) < 1 or vb[0] != VERSION:
                return False

            # salt_len
            slb = f.read(LEN_FIELD_SIZE)
            if len(slb) < LEN_FIELD_SIZE:
                return False
            salt_len = struct.unpack(">H", slb)[0]
            if salt_len < 8 or salt_len > 256:
                return False

            # nonce_len
            nlb = f.read(LEN_FIELD_SIZE)
            if len(nlb) < LEN_FIELD_SIZE:
                return False
            nonce_len = struct.unpack(">H", nlb)[0]
            if nonce_len < 8 or nonce_len > 64:
                return False

            # filename_len
            flb = f.read(LEN_FIELD_SIZE)
            if len(flb) < LEN_FIELD_SIZE:
                return False
            filename_len = struct.unpack(">H", flb)[0]
            if filename_len > 65535:
                return False

            # salt
            if len(f.read(salt_len)) < salt_len:
                return False

            # nonce
            if len(f.read(nonce_len)) < nonce_len:
                return False

            # filename
            if len(f.read(filename_len)) < filename_len:
                return False

            # ciphertext (至少 16B auth tag)
            if len(f.read()) < GCM_TAG_SIZE:
                return False

        return True
    except Exception:
        return False
