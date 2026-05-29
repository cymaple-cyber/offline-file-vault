"""
密码生成器模块测试
"""

import os
import sys
import string
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.password_utils import (
    generate_password,
    get_password_strength_label,
    LENGTH_OPTIONS,
)


class TestPasswordUtils(unittest.TestCase):
    """密码生成器测试。"""

    def test_generate_default_password(self):
        """测试默认参数生成密码。"""
        pwd = generate_password()
        self.assertEqual(len(pwd), 16)
        # 至少包含一种字符类型
        self.assertTrue(any(c.isupper() for c in pwd))
        self.assertTrue(any(c.islower() for c in pwd))
        self.assertTrue(any(c.isdigit() for c in pwd))
        self.assertTrue(any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd))

    def test_generate_password_length_16(self):
        pwd = generate_password(length=16)
        self.assertEqual(len(pwd), 16)

    def test_generate_password_length_24(self):
        pwd = generate_password(length=24)
        self.assertEqual(len(pwd), 24)

    def test_generate_password_length_32(self):
        pwd = generate_password(length=32)
        self.assertEqual(len(pwd), 32)

    def test_generate_password_length_48(self):
        pwd = generate_password(length=48)
        self.assertEqual(len(pwd), 48)

    def test_generate_only_uppercase(self):
        pwd = generate_password(
            length=16,
            include_uppercase=True,
            include_lowercase=False,
            include_digits=False,
            include_symbols=False,
        )
        self.assertEqual(len(pwd), 16)
        self.assertTrue(all(c.isupper() for c in pwd))

    def test_generate_only_lowercase(self):
        pwd = generate_password(
            length=16,
            include_uppercase=False,
            include_lowercase=True,
            include_digits=False,
            include_symbols=False,
        )
        self.assertEqual(len(pwd), 16)
        self.assertTrue(all(c.islower() for c in pwd))

    def test_generate_only_digits(self):
        pwd = generate_password(
            length=16,
            include_uppercase=False,
            include_lowercase=False,
            include_digits=True,
            include_symbols=False,
        )
        self.assertEqual(len(pwd), 16)
        self.assertTrue(all(c.isdigit() for c in pwd))

    def test_generate_only_symbols(self):
        pwd = generate_password(
            length=16,
            include_uppercase=False,
            include_lowercase=False,
            include_digits=False,
            include_symbols=True,
        )
        self.assertEqual(len(pwd), 16)
        safe_symbols = set("!@#$%^&*()_+-=[]{}|;:,.<>?")
        self.assertTrue(all(c in safe_symbols for c in pwd))

    def test_generate_no_character_type(self):
        """测试未选择任何字符类型时抛出异常。"""
        with self.assertRaises(ValueError):
            generate_password(
                include_uppercase=False,
                include_lowercase=False,
                include_digits=False,
                include_symbols=False,
            )

    def test_generate_password_too_short(self):
        """测试密码长度过短。"""
        with self.assertRaises(ValueError):
            generate_password(length=3)

    def test_generate_password_randomness(self):
        """测试生成的密码具有随机性（连续生成不应相同）。"""
        passwords = set()
        for _ in range(20):
            passwords.add(generate_password(length=16))
        # 20 次生成中，至少应有 15 个不同的密码
        self.assertGreater(len(passwords), 15)

    def test_generate_password_has_each_type(self):
        """测试启用所有类型时，密码包含每种字符类型。"""
        for _ in range(50):
            pwd = generate_password(
                length=16,
                include_uppercase=True,
                include_lowercase=True,
                include_digits=True,
                include_symbols=True,
            )
            has_upper = any(c.isupper() for c in pwd)
            has_lower = any(c.islower() for c in pwd)
            has_digit = any(c.isdigit() for c in pwd)
            has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd)

            self.assertTrue(has_upper, f"缺少大写字母: {pwd}")
            self.assertTrue(has_lower, f"缺少小写字母: {pwd}")
            self.assertTrue(has_digit, f"缺少数字: {pwd}")
            self.assertTrue(has_symbol, f"缺少符号: {pwd}")

    def test_get_password_strength_weak(self):
        """测试弱密码强度评估。"""
        strength, color = get_password_strength_label("abc")
        self.assertEqual(strength, "弱")
        self.assertEqual(color, "#e74c3c")

    def test_get_password_strength_strong(self):
        """测试强密码强度评估。"""
        strength, color = get_password_strength_label("MySecureP@ssw0rd2024")
        self.assertEqual(strength, "强")

    def test_get_password_strength_very_strong(self):
        """测试很强密码强度评估。"""
        strength, color = get_password_strength_label(
            "Xy9#mLp2@Qw8$Nk5&Tr3^Vb7!Cs1*Jh4"
        )
        self.assertEqual(strength, "很强")
        self.assertEqual(color, "#2ecc71")

    def test_length_options(self):
        """测试长度选项定义。"""
        self.assertIn(16, LENGTH_OPTIONS)
        self.assertIn(24, LENGTH_OPTIONS)
        self.assertIn(32, LENGTH_OPTIONS)
        self.assertIn(48, LENGTH_OPTIONS)


if __name__ == "__main__":
    unittest.main()
