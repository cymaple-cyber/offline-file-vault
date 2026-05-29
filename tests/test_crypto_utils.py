"""
加密解密模块测试

测试覆盖：
- 正常加密解密
- 错误密码
- 文件被篡改
- 空文件
- 中文文件名
- 较大文件
"""

import os
import sys
import tempfile
import unittest

# 确保可以导入 src 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crypto_utils import encrypt_file, decrypt_file, verify_cysafe_file


class TestCryptoUtils(unittest.TestCase):
    """加密解密核心测试。"""

    def setUp(self):
        """创建临时目录。"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理临时目录。"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_temp_file(self, filename, content):
        """在临时目录中创建测试文件。"""
        path = os.path.join(self.temp_dir, filename)
        with open(path, "wb") as f:
            if isinstance(content, str):
                f.write(content.encode("utf-8"))
            else:
                f.write(content)
        return path

    def test_encrypt_decrypt_normal(self):
        """测试正常加密和解密流程。"""
        content = b"Hello, World! This is a test file for encryption."
        input_path = self._make_temp_file("test_normal.txt", content)
        encrypted_path = input_path + ".cysafe"

        # 加密
        encrypt_file(input_path, encrypted_path, "mypassword123")

        # 验证加密文件存在且格式正确
        self.assertTrue(os.path.exists(encrypted_path))
        self.assertTrue(verify_cysafe_file(encrypted_path))

        # 加密后原文件还在
        self.assertTrue(os.path.exists(input_path))

        # 解密
        output_path = decrypt_file(encrypted_path, self.temp_dir, "mypassword123")

        # 验证解密内容
        with open(output_path, "rb") as f:
            decrypted_content = f.read()
        self.assertEqual(content, decrypted_content)

    def test_encrypt_decrypt_wrong_password(self):
        """测试错误密码解密。"""
        content = b"Secret data that should not be revealed."
        input_path = self._make_temp_file("test_wrong_pwd.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "correct_password")

        # 使用错误密码解密
        with self.assertRaises(ValueError) as ctx:
            decrypt_file(encrypted_path, self.temp_dir, "wrong_password")
        self.assertIn("密码错误或文件已损坏", str(ctx.exception))

    def test_encrypt_decrypt_empty_file(self):
        """测试空文件加密解密。"""
        input_path = self._make_temp_file("test_empty.txt", b"")
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "password")
        self.assertTrue(verify_cysafe_file(encrypted_path))

        output_path = decrypt_file(encrypted_path, self.temp_dir, "password")
        with open(output_path, "rb") as f:
            decrypted_content = f.read()
        self.assertEqual(b"", decrypted_content)

    def test_encrypt_decrypt_chinese_filename(self):
        """测试中文文件名。"""
        content = b"Content with Chinese filename."
        input_path = self._make_temp_file("中文文件_测试.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "测试密码123")

        self.assertTrue(verify_cysafe_file(encrypted_path))

        # 删除原文件避免解密时冲突
        os.remove(input_path)

        output_path = decrypt_file(encrypted_path, self.temp_dir, "测试密码123")

        # 验证文件名正确恢复
        self.assertEqual(os.path.basename(output_path), "中文文件_测试.txt")

        with open(output_path, "rb") as f:
            self.assertEqual(content, f.read())

    def test_encrypt_decrypt_binary_data(self):
        """测试二进制数据（包含所有字节值）。"""
        content = bytes(range(256)) * 10  # 2560 字节
        input_path = self._make_temp_file("test_binary.bin", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "binary_pwd")
        output_path = decrypt_file(encrypted_path, self.temp_dir, "binary_pwd")

        with open(output_path, "rb") as f:
            self.assertEqual(content, f.read())

    def test_tampered_file_magic_header(self):
        """测试篡改 magic header 后解密失败。"""
        content = b"Test data for tampering."
        input_path = self._make_temp_file("test_tamper.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "password")

        # 篡改 magic header（前4字节）
        with open(encrypted_path, "r+b") as f:
            f.seek(0)
            f.write(b"XXXX")

        self.assertFalse(verify_cysafe_file(encrypted_path))

        with self.assertRaises(ValueError) as ctx:
            decrypt_file(encrypted_path, self.temp_dir, "password")
        self.assertIn("密码错误或文件已损坏", str(ctx.exception))

    def test_tampered_file_ciphertext(self):
        """测试篡改密文后解密失败。"""
        content = b"Test data for ciphertext tampering."
        input_path = self._make_temp_file("test_tamper_ct.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "password")

        # 修改密文区域的一个字节（跳过头部 100 字节后）
        with open(encrypted_path, "r+b") as f:
            f.seek(100)
            byte_val = f.read(1)
            f.seek(100)
            f.write(bytes([byte_val[0] ^ 0xFF]))  # 翻转所有位

        with self.assertRaises(ValueError) as ctx:
            decrypt_file(encrypted_path, self.temp_dir, "password")
        self.assertIn("密码错误或文件已损坏", str(ctx.exception))

    def test_tampered_file_salt(self):
        """测试篡改 salt 后解密失败。"""
        content = b"Test data for salt tampering."
        input_path = self._make_temp_file("test_tamper_salt.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "password")

        # 修改 salt（偏移 11，固定头部 magic+version+salt_len+nonce_len+filename_len = 11 字节）
        with open(encrypted_path, "r+b") as f:
            f.seek(11)
            f.write(b"\x00" * 16)

        with self.assertRaises(ValueError) as ctx:
            decrypt_file(encrypted_path, self.temp_dir, "password")
        self.assertIn("密码错误或文件已损坏", str(ctx.exception))

    def test_verify_cysafe_valid(self):
        """测试验证有效的 .cysafe 文件。"""
        content = b"Valid file content."
        input_path = self._make_temp_file("test_valid.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "password")
        self.assertTrue(verify_cysafe_file(encrypted_path))

    def test_verify_cysafe_invalid_file(self):
        """测试验证无效文件。"""
        # 普通文本文件不是有效的 .cysafe 文件
        path = self._make_temp_file("test_not_cysafe.txt", b"This is not a cysafe file.")
        self.assertFalse(verify_cysafe_file(path))

    def test_verify_cysafe_nonexistent(self):
        """测试验证不存在的文件。"""
        self.assertFalse(verify_cysafe_file("/nonexistent/path/file.cysafe"))

    def test_verify_cysafe_empty_file(self):
        """测试验证空文件。"""
        path = self._make_temp_file("test_empty.cysafe", b"")
        self.assertFalse(verify_cysafe_file(path))

    def test_encrypt_nonexistent_file(self):
        """测试加密不存在的文件。"""
        with self.assertRaises(FileNotFoundError):
            encrypt_file("/nonexistent/file.txt", "/tmp/out.cysafe", "password")

    def test_decrypt_nonexistent_file(self):
        """测试解密不存在的文件。"""
        with self.assertRaises(FileNotFoundError):
            decrypt_file("/nonexistent/file.cysafe", self.temp_dir, "password")

    def test_filename_collision(self):
        """测试文件名冲突时自动重命名。"""
        content = b"First file content."
        input_path = self._make_temp_file("collision.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "password")

        # 删除原文件，这样第一次解密不会冲突
        os.remove(input_path)

        # 第一次解密
        output1 = decrypt_file(encrypted_path, self.temp_dir, "password")
        self.assertEqual(os.path.basename(output1), "collision.txt")

        # 第二次解密（同名冲突）
        output2 = decrypt_file(encrypted_path, self.temp_dir, "password")
        self.assertEqual(os.path.basename(output2), "collision(1).txt")

        # 验证两个文件都存在
        self.assertTrue(os.path.exists(output1))
        self.assertTrue(os.path.exists(output2))

    def test_encrypt_decrypt_large_content(self):
        """测试较大内容加密解密（1MB 随机数据）。"""
        content = os.urandom(1024 * 1024)  # 1MB
        input_path = self._make_temp_file("test_large.bin", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "large_pwd")

        output_path = decrypt_file(encrypted_path, self.temp_dir, "large_pwd")

        with open(output_path, "rb") as f:
            self.assertEqual(content, f.read())

    def test_password_cannot_recover_with_wrong_password(self):
        """验证密码丢失后无法通过其他方式恢复。"""
        # 这条测试确认了安全特性：只有正确的密码才能解密
        content = b"Highly sensitive data."
        input_path = self._make_temp_file("sensitive.txt", content)
        encrypted_path = input_path + ".cysafe"

        encrypt_file(input_path, encrypted_path, "correct_horse_battery_staple")

        # 尝试多个错误密码
        wrong_passwords = ["wrong1", "correct_horse_battery_staple!", "", "12345678"]
        for pwd in wrong_passwords:
            with self.assertRaises(ValueError, msg=f"密码 '{pwd}' 不应该能解密"):
                decrypt_file(encrypted_path, self.temp_dir, pwd)

        # 正确的密码仍然能解密
        output_path = decrypt_file(encrypted_path, self.temp_dir, "correct_horse_battery_staple")
        with open(output_path, "rb") as f:
            self.assertEqual(content, f.read())

    def test_different_salts_for_same_password(self):
        """测试同一密码加密不同文件产生不同的密文。"""
        content = b"Same content."
        path1 = self._make_temp_file("test_salt1.txt", content)
        path2 = self._make_temp_file("test_salt2.txt", content)

        encrypted1 = path1 + ".cysafe"
        encrypted2 = path2 + ".cysafe"

        encrypt_file(path1, encrypted1, "same_password")
        encrypt_file(path2, encrypted2, "same_password")

        # 密文应该不同（因为 salt 不同）
        with open(encrypted1, "rb") as f1, open(encrypted2, "rb") as f2:
            ct1 = f1.read()
            ct2 = f2.read()

        self.assertNotEqual(ct1, ct2, "相同密码加密应有不同的密文")

        # 但都能正确解密
        out1 = decrypt_file(encrypted1, self.temp_dir, "same_password")
        out2 = decrypt_file(encrypted2, self.temp_dir, "same_password")

        with open(out1, "rb") as f:
            self.assertEqual(content, f.read())
        with open(out2, "rb") as f:
            self.assertEqual(content, f.read())


if __name__ == "__main__":
    unittest.main()
