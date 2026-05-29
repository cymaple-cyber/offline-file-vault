"""
哈希校验模块测试
"""

import os
import sys
import tempfile
import hashlib
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hash_utils import compute_hashes


class TestHashUtils(unittest.TestCase):
    """哈希计算测试。"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_temp_file(self, filename, content):
        path = os.path.join(self.temp_dir, filename)
        with open(path, "wb") as f:
            if isinstance(content, str):
                f.write(content.encode("utf-8"))
            else:
                f.write(content)
        return path

    def test_compute_hashes_normal(self):
        """测试正常哈希计算。"""
        content = b"Hello, Hash World!"
        path = self._make_temp_file("test_hash.txt", content)

        result = compute_hashes(path)

        # 验证手动计算的结果
        expected_md5 = hashlib.md5(content).hexdigest()
        expected_sha1 = hashlib.sha1(content).hexdigest()
        expected_sha256 = hashlib.sha256(content).hexdigest()

        self.assertEqual(result["MD5"], expected_md5)
        self.assertEqual(result["SHA-1"], expected_sha1)
        self.assertEqual(result["SHA-256"], expected_sha256)

    def test_compute_hashes_empty_file(self):
        """测试空文件哈希。"""
        path = self._make_temp_file("test_empty.txt", b"")

        result = compute_hashes(path)

        expected_md5 = hashlib.md5(b"").hexdigest()
        expected_sha1 = hashlib.sha1(b"").hexdigest()
        expected_sha256 = hashlib.sha256(b"").hexdigest()

        self.assertEqual(result["MD5"], expected_md5)
        self.assertEqual(result["SHA-1"], expected_sha1)
        self.assertEqual(result["SHA-256"], expected_sha256)

    def test_compute_hashes_chinese_filename(self):
        """测试中文文件名哈希。"""
        content = b"Chinese filename test."
        path = self._make_temp_file("中文hash测试.txt", content)

        result = compute_hashes(path)

        expected_sha256 = hashlib.sha256(content).hexdigest()
        self.assertEqual(result["SHA-256"], expected_sha256)

    def test_compute_hashes_large_file(self):
        """测试大文件哈希（10MB）。"""
        content = os.urandom(10 * 1024 * 1024)  # 10MB
        path = self._make_temp_file("test_large.bin", content)

        result = compute_hashes(path)

        expected_md5 = hashlib.md5(content).hexdigest()
        expected_sha1 = hashlib.sha1(content).hexdigest()
        expected_sha256 = hashlib.sha256(content).hexdigest()

        self.assertEqual(result["MD5"], expected_md5)
        self.assertEqual(result["SHA-1"], expected_sha1)
        self.assertEqual(result["SHA-256"], expected_sha256)

    def test_compute_hashes_nonexistent_file(self):
        """测试不存在的文件。"""
        with self.assertRaises(FileNotFoundError):
            compute_hashes("/nonexistent/path/file.txt")

    def test_compute_hashes_all_algorithms_present(self):
        """测试返回结果包含全部三种算法。"""
        path = self._make_temp_file("test_all.txt", b"data")

        result = compute_hashes(path)

        self.assertIn("MD5", result)
        self.assertIn("SHA-1", result)
        self.assertIn("SHA-256", result)
        self.assertEqual(len(result), 3)

    def test_compute_hashes_hex_format(self):
        """测试哈希值均为十六进制格式。"""
        path = self._make_temp_file("test_hex.txt", b"data")

        result = compute_hashes(path)

        for algo, value in result.items():
            # 验证是十六进制字符串（只包含 0-9, a-f）
            self.assertTrue(
                all(c in "0123456789abcdef" for c in value),
                f"{algo} 不是有效的十六进制: {value}",
            )
            # 验证正确长度
            if algo == "MD5":
                self.assertEqual(len(value), 32)
            elif algo == "SHA-1":
                self.assertEqual(len(value), 40)
            elif algo == "SHA-256":
                self.assertEqual(len(value), 64)


if __name__ == "__main__":
    unittest.main()
