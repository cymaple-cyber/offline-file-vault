"""
离线文件保险箱 - 密码生成器模块

使用 Python secrets 模块生成安全随机密码。
"""

import secrets
import string


# 密码长度选项
LENGTH_OPTIONS = [16, 24, 32, 48]


def generate_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
) -> str:
    """
    生成安全随机密码。

    使用 secrets.choice 保证密码学安全。

    Args:
        length: 密码长度
        include_uppercase: 是否包含大写字母
        include_lowercase: 是否包含小写字母
        include_digits: 是否包含数字
        include_symbols: 是否包含符号

    Returns:
        生成的随机密码字符串

    Raises:
        ValueError: 未选择任何字符类型，或长度无效
    """
    if length < 4:
        raise ValueError("密码长度至少为 4")

    # 构建字符集
    char_pool = ""
    required_chars = []  # 确保每类字符至少出现一次

    if include_uppercase:
        char_pool += string.ascii_uppercase
        required_chars.append(secrets.choice(string.ascii_uppercase))
    if include_lowercase:
        char_pool += string.ascii_lowercase
        required_chars.append(secrets.choice(string.ascii_lowercase))
    if include_digits:
        char_pool += string.digits
        required_chars.append(secrets.choice(string.digits))
    if include_symbols:
        # 使用较安全的符号集，排除可能引起问题的符号
        safe_symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        char_pool += safe_symbols
        required_chars.append(secrets.choice(safe_symbols))

    if not char_pool:
        raise ValueError("至少需要选择一种字符类型")

    # 先用必须字符填充
    remaining = length - len(required_chars)
    if remaining < 0:
        # 如果长度不足，从必须字符中随机选择
        password_chars = secrets.SystemRandom().sample(required_chars, length)
    else:
        # 剩余位置随机填充
        password_chars = required_chars + [
            secrets.choice(char_pool) for _ in range(remaining)
        ]

    # 打乱顺序
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def get_password_strength_label(password: str) -> tuple:
    """
    评估密码强度（简单启发式）。

    Args:
        password: 密码字符串

    Returns:
        (强度标签, 颜色代码) 元组
        例如: ("弱", "#e74c3c"), ("中等", "#f39c12"), ("强", "#27ae60"), ("很强", "#2ecc71")
    """
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    diversity = sum([has_upper, has_lower, has_digit, has_symbol])

    score = 0
    # 长度得分
    if length >= 32:
        score += 3
    elif length >= 24:
        score += 2
    elif length >= 16:
        score += 1

    # 字符多样性得分
    score += diversity

    if score <= 2:
        return ("弱", "#e74c3c")
    elif score <= 4:
        return ("中等", "#f39c12")
    elif score <= 5:
        return ("强", "#27ae60")
    else:
        return ("很强", "#2ecc71")
