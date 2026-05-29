"""
离线文件保险箱 - 主窗口界面

包含四个功能标签页：文件加密、文件解密、哈希校验、密码生成器。
"""

import os
import sys

from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QComboBox,
    QTextEdit,
    QGroupBox,
    QApplication,
    QProgressBar,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPalette, QColor

# 确保可以导入 src 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.crypto_utils import encrypt_file, decrypt_file, verify_cysafe_file
from src.hash_utils import compute_hashes
from src.password_utils import (
    generate_password,
    get_password_strength_label,
    LENGTH_OPTIONS,
)


# --- 颜色常量（暗色主题）---
COLOR_PRIMARY = "#64B5F6"
COLOR_SUCCESS = "#81C784"
COLOR_DANGER = "#E57373"
COLOR_WARNING = "#FFB74D"
COLOR_BG = "#1E1E1E"
COLOR_SURFACE = "#2D2D2D"
COLOR_SURFACE_ALT = "#353535"
COLOR_BORDER = "#404040"
COLOR_BORDER_HOVER = "#555555"
COLOR_TEXT = "#E0E0E0"
COLOR_TEXT_SECONDARY = "#9E9E9E"
COLOR_INPUT_BG = "#252525"
COLOR_MONO_BG = "#1A1A2E"


class EncryptWorker(QThread):
    """后台加密工作线程，避免阻塞 UI。"""
    finished = Signal(bool, str)  # success, message/path
    progress = Signal(int)

    def __init__(self, input_path, output_path, password, delete_original=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.password = password
        self.delete_original = delete_original

    def run(self):
        try:
            self.progress.emit(30)
            encrypt_file(self.input_path, self.output_path, self.password)
            self.progress.emit(80)

            # 删除原文件（可选）
            if self.delete_original:
                try:
                    os.remove(self.input_path)
                except OSError as e:
                    self.finished.emit(False, f"加密成功，但删除原文件失败: {e}")
                    return

            self.progress.emit(100)
            self.finished.emit(True, self.output_path)
        except Exception as e:
            self.finished.emit(False, str(e))


class DecryptWorker(QThread):
    """后台解密工作线程。"""
    finished = Signal(bool, str)  # success, message
    progress = Signal(int)

    def __init__(self, input_path, output_dir, password):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.password = password

    def run(self):
        try:
            self.progress.emit(30)
            output_path = decrypt_file(self.input_path, self.output_dir, self.password)
            self.progress.emit(100)
            self.finished.emit(True, output_path)
        except Exception as e:
            self.finished.emit(False, str(e))


class HashWorker(QThread):
    """后台哈希计算工作线程。"""
    finished = Signal(bool, object)  # success, result (dict or error str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            result = compute_hashes(self.filepath)
            self.finished.emit(True, result)
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """离线文件保险箱主窗口。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("离线文件保险箱")
        self.resize(720, 580)
        self.setMinimumSize(600, 480)

        # 全局暗色样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BG};
            }}
            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                background-color: {COLOR_SURFACE};
            }}
            QTabBar::tab {{
                padding: 10px 24px;
                font-size: 14px;
                border: 1px solid {COLOR_BORDER};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                background-color: {COLOR_SURFACE_ALT};
                color: {COLOR_TEXT_SECONDARY};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_PRIMARY};
                font-weight: bold;
                border-bottom: 2px solid {COLOR_PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #3A3A3A;
                color: {COLOR_TEXT};
            }}
            QPushButton {{
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
                border: 1px solid {COLOR_BORDER};
                background-color: {COLOR_SURFACE_ALT};
                color: {COLOR_TEXT};
            }}
            QPushButton:hover {{
                background-color: #404040;
                border-color: {COLOR_BORDER_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #505050;
            }}
            QPushButton#btnPrimary {{
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                font-weight: bold;
            }}
            QPushButton#btnPrimary:hover {{
                background-color: #1565C0;
            }}
            QPushButton#btnDanger {{
                background-color: #C62828;
                color: white;
                border: none;
            }}
            QPushButton#btnDanger:hover {{
                background-color: #B71C1C;
            }}
            QPushButton#btnSuccess {{
                background-color: #2E7D32;
                color: white;
                border: none;
            }}
            QPushButton#btnSuccess:hover {{
                background-color: #1B5E20;
            }}
            QLineEdit {{
                padding: 8px 12px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-size: 13px;
                background-color: {COLOR_INPUT_BG};
                color: {COLOR_TEXT};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_PRIMARY};
            }}
            QLineEdit[readOnly="true"] {{
                background-color: {COLOR_BG};
                color: {COLOR_TEXT_SECONDARY};
            }}
            QComboBox {{
                padding: 8px 12px;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-size: 13px;
                background-color: {COLOR_INPUT_BG};
                color: {COLOR_TEXT};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT};
                selection-background-color: #1976D2;
                border: 1px solid {COLOR_BORDER};
            }}
            QTextEdit {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-size: 13px;
                font-family: "SF Mono", "Menlo", "Consolas", monospace;
                background-color: {COLOR_MONO_BG};
                color: {COLOR_TEXT};
            }}
            QGroupBox {{
                font-size: 14px;
                font-weight: bold;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 16px;
                background-color: {COLOR_SURFACE};
                color: {COLOR_TEXT};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {COLOR_PRIMARY};
            }}
            QCheckBox {{
                font-size: 13px;
                spacing: 8px;
                color: {COLOR_TEXT};
            }}
            QLabel {{
                font-size: 13px;
                color: {COLOR_TEXT};
            }}
            QProgressBar {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                text-align: center;
                font-size: 12px;
                height: 20px;
                background-color: {COLOR_BG};
                color: {COLOR_TEXT};
            }}
            QProgressBar::chunk {{
                background-color: #1976D2;
                border-radius: 3px;
            }}
        """)

        self._init_ui()

    def _init_ui(self):
        """初始化主界面布局。"""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)

        # 标题
        title_label = QLabel("离线文件保险箱")
        title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLOR_PRIMARY};
            padding: 8px 4px;
        """)
        layout.addWidget(title_label)

        # 标签页
        self.tabs = QTabWidget()

        self.tabs.addTab(self._create_encrypt_tab(), "  文件加密  ")
        self.tabs.addTab(self._create_decrypt_tab(), "  文件解密  ")
        self.tabs.addTab(self._create_hash_tab(), "  哈希校验  ")
        self.tabs.addTab(self._create_password_tab(), "  密码生成器  ")

        layout.addWidget(self.tabs)

    # ==================== 文件加密标签页 ====================

    def _create_encrypt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 文件选择
        file_group = QGroupBox("选择文件")
        file_layout = QHBoxLayout()
        self.encrypt_file_path = QLineEdit()
        self.encrypt_file_path.setReadOnly(True)
        self.encrypt_file_path.setPlaceholderText("请选择要加密的文件...")
        btn_select = QPushButton("浏览...")
        btn_select.clicked.connect(self._encrypt_select_file)
        file_layout.addWidget(self.encrypt_file_path, 1)
        file_layout.addWidget(btn_select)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 密码输入
        pwd_group = QGroupBox("设置密码")
        pwd_layout = QVBoxLayout()
        pwd_layout.setSpacing(8)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("密码："))
        self.encrypt_password = QLineEdit()
        self.encrypt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.encrypt_password.setPlaceholderText("请输入加密密码（至少 4 位）")
        row1.addWidget(self.encrypt_password, 1)
        pwd_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("确认："))
        self.encrypt_password_confirm = QLineEdit()
        self.encrypt_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.encrypt_password_confirm.setPlaceholderText("请再次输入密码")
        row2.addWidget(self.encrypt_password_confirm, 1)
        pwd_layout.addLayout(row2)

        pwd_group.setLayout(pwd_layout)
        layout.addWidget(pwd_group)

        # 选项
        options_layout = QHBoxLayout()
        self.encrypt_delete_original = QCheckBox("加密后删除原文件")
        self.encrypt_delete_original.setToolTip("启用后，加密成功将删除原始文件。请谨慎使用。")
        options_layout.addWidget(self.encrypt_delete_original)
        options_layout.addStretch()

        # 安全提示
        warning_label = QLabel("⚠ 密码丢失后无法恢复加密文件，请妥善保管密码。")
        warning_label.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 12px;")
        options_layout.addWidget(warning_label)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # 进度条
        self.encrypt_progress = QProgressBar()
        self.encrypt_progress.setVisible(False)
        self.encrypt_progress.setRange(0, 100)
        layout.addWidget(self.encrypt_progress)

        # 加密按钮
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_encrypt = QPushButton("开始加密")
        btn_encrypt.setObjectName("btnPrimary")
        btn_encrypt.setMinimumWidth(140)
        btn_encrypt.setMinimumHeight(40)
        btn_encrypt.setStyleSheet("QPushButton#btnPrimary { font-size: 15px; padding: 10px 30px; }")
        btn_encrypt.clicked.connect(self._do_encrypt)
        btn_layout.addWidget(btn_encrypt)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return tab

    def _encrypt_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择要加密的文件")
        if path:
            self.encrypt_file_path.setText(path)

    def _do_encrypt(self):
        """执行加密操作。"""
        input_path = self.encrypt_file_path.text().strip()
        password = self.encrypt_password.text()
        password_confirm = self.encrypt_password_confirm.text()

        # 验证输入
        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择要加密的文件。")
            return

        if not os.path.isfile(input_path):
            QMessageBox.warning(self, "提示", "选择的文件不存在，请重新选择。")
            return

        if not password:
            QMessageBox.warning(self, "提示", "请输入加密密码。")
            return

        if len(password) < 4:
            QMessageBox.warning(self, "提示", "密码长度至少为 4 位。")
            return

        if password != password_confirm:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致，请重新输入。")
            return

        # 确认删除原文件
        delete_original = self.encrypt_delete_original.isChecked()
        if delete_original:
            reply = QMessageBox.question(
                self,
                "确认操作",
                f"即将加密并删除原文件：\n\n{os.path.basename(input_path)}\n\n"
                "删除后原文件将无法恢复，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 确定输出路径
        output_path = input_path + ".cysafe"
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"输出文件已存在：\n\n{output_path}\n\n是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 启动加密线程
        self.encrypt_progress.setVisible(True)
        self.encrypt_progress.setValue(0)

        self.encrypt_worker = EncryptWorker(input_path, output_path, password, delete_original)
        self.encrypt_worker.progress.connect(self.encrypt_progress.setValue)
        self.encrypt_worker.finished.connect(self._on_encrypt_finished)
        self.encrypt_worker.start()

    def _on_encrypt_finished(self, success, message):
        """加密完成回调。"""
        self.encrypt_progress.setVisible(False)

        if success:
            self.encrypt_file_path.clear()
            self.encrypt_password.clear()
            self.encrypt_password_confirm.clear()

            QMessageBox.information(
                self,
                "加密成功",
                f"文件加密成功！\n\n加密文件：{message}\n\n"
                "请妥善保管您的密码，丢失后无法恢复。",
            )
        else:
            QMessageBox.critical(self, "加密失败", f"加密过程中出现错误：\n{message}")

    # ==================== 文件解密标签页 ====================

    def _create_decrypt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 文件选择
        file_group = QGroupBox("选择 .cysafe 文件")
        file_layout = QHBoxLayout()
        self.decrypt_file_path = QLineEdit()
        self.decrypt_file_path.setReadOnly(True)
        self.decrypt_file_path.setPlaceholderText("请选择 .cysafe 加密文件...")
        btn_select = QPushButton("浏览...")
        btn_select.clicked.connect(self._decrypt_select_file)
        file_layout.addWidget(self.decrypt_file_path, 1)
        file_layout.addWidget(btn_select)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 密码输入
        pwd_group = QGroupBox("输入密码")
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(QLabel("密码："))
        self.decrypt_password = QLineEdit()
        self.decrypt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.decrypt_password.setPlaceholderText("请输入解密密码")
        self.decrypt_password.returnPressed.connect(self._do_decrypt)
        pwd_layout.addWidget(self.decrypt_password, 1)
        pwd_group.setLayout(pwd_layout)
        layout.addWidget(pwd_group)

        # 进度条
        self.decrypt_progress = QProgressBar()
        self.decrypt_progress.setVisible(False)
        self.decrypt_progress.setRange(0, 100)
        layout.addWidget(self.decrypt_progress)

        # 解密按钮
        layout.addStretch()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_decrypt = QPushButton("开始解密")
        btn_decrypt.setObjectName("btnPrimary")
        btn_decrypt.setMinimumWidth(140)
        btn_decrypt.setMinimumHeight(40)
        btn_decrypt.setStyleSheet("QPushButton#btnPrimary { font-size: 15px; padding: 10px 30px; }")
        btn_decrypt.clicked.connect(self._do_decrypt)
        btn_layout.addWidget(btn_decrypt)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return tab

    def _decrypt_select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 .cysafe 加密文件", "", "加密文件 (*.cysafe);;所有文件 (*)"
        )
        if path:
            self.decrypt_file_path.setText(path)

    def _do_decrypt(self):
        """执行解密操作。"""
        input_path = self.decrypt_file_path.text().strip()
        password = self.decrypt_password.text()

        if not input_path:
            QMessageBox.warning(self, "提示", "请先选择 .cysafe 加密文件。")
            return

        if not os.path.isfile(input_path):
            QMessageBox.warning(self, "提示", "选择的文件不存在，请重新选择。")
            return

        if not password:
            QMessageBox.warning(self, "提示", "请输入解密密码。")
            return

        # 验证是否为有效的 .cysafe 文件
        if not verify_cysafe_file(input_path):
            QMessageBox.warning(self, "提示", "选择的文件不是有效的加密文件或文件已损坏。")
            return

        # 启动解密线程
        output_dir = os.path.dirname(input_path)
        self.decrypt_progress.setVisible(True)
        self.decrypt_progress.setValue(0)

        self.decrypt_worker = DecryptWorker(input_path, output_dir, password)
        self.decrypt_worker.progress.connect(self.decrypt_progress.setValue)
        self.decrypt_worker.finished.connect(self._on_decrypt_finished)
        self.decrypt_worker.start()

    def _on_decrypt_finished(self, success, message):
        """解密完成回调。"""
        self.decrypt_progress.setVisible(False)

        if success:
            self.decrypt_file_path.clear()
            self.decrypt_password.clear()

            QMessageBox.information(
                self,
                "解密成功",
                f"文件解密成功！\n\n恢复文件：{message}",
            )
        else:
            QMessageBox.critical(
                self,
                "解密失败",
                f"密码错误或文件已损坏",
            )

    # ==================== 哈希校验标签页 ====================

    def _create_hash_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 文件选择
        file_group = QGroupBox("选择文件")
        file_layout = QHBoxLayout()
        self.hash_file_path = QLineEdit()
        self.hash_file_path.setReadOnly(True)
        self.hash_file_path.setPlaceholderText("请选择要计算哈希的文件...")
        btn_select = QPushButton("浏览...")
        btn_select.clicked.connect(self._hash_select_file)
        file_layout.addWidget(self.hash_file_path, 1)
        file_layout.addWidget(btn_select)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 计算按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_calc = QPushButton("计算哈希")
        btn_calc.setObjectName("btnPrimary")
        btn_calc.setMinimumWidth(120)
        btn_calc.clicked.connect(self._do_hash)
        btn_layout.addWidget(btn_calc)
        layout.addLayout(btn_layout)

        # 结果展示
        result_group = QGroupBox("哈希计算结果")
        result_layout = QVBoxLayout()

        self.hash_result_text = QTextEdit()
        self.hash_result_text.setReadOnly(True)
        self.hash_result_text.setMaximumHeight(140)
        self.hash_result_text.setPlaceholderText("选择文件后点击「计算哈希」查看结果...")
        result_layout.addWidget(self.hash_result_text)

        # 复制按钮
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()
        btn_copy_md5 = QPushButton("复制 MD5")
        btn_copy_md5.clicked.connect(lambda: self._copy_hash("MD5"))
        btn_copy_sha1 = QPushButton("复制 SHA-1")
        btn_copy_sha1.clicked.connect(lambda: self._copy_hash("SHA-1"))
        btn_copy_sha256 = QPushButton("复制 SHA-256")
        btn_copy_sha256.clicked.connect(lambda: self._copy_hash("SHA-256"))
        btn_copy_all = QPushButton("一键复制全部")
        btn_copy_all.clicked.connect(self._copy_all_hashes)

        copy_layout.addWidget(btn_copy_md5)
        copy_layout.addWidget(btn_copy_sha1)
        copy_layout.addWidget(btn_copy_sha256)
        copy_layout.addWidget(btn_copy_all)
        result_layout.addLayout(copy_layout)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        layout.addStretch()

        return tab

    def _hash_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if path:
            self.hash_file_path.setText(path)

    def _do_hash(self):
        """执行哈希计算。"""
        filepath = self.hash_file_path.text().strip()
        if not filepath:
            QMessageBox.warning(self, "提示", "请先选择文件。")
            return

        if not os.path.isfile(filepath):
            QMessageBox.warning(self, "提示", "选择的文件不存在。")
            return

        self.hash_result_text.setPlainText("正在计算...")

        self.hash_worker = HashWorker(filepath)
        self.hash_worker.finished.connect(self._on_hash_finished)
        self.hash_worker.start()

    def _on_hash_finished(self, success, result):
        """哈希计算完成回调。"""
        if success:
            self._hash_result = result
            text = f"MD5:     {result['MD5']}\n"
            text += f"SHA-1:   {result['SHA-1']}\n"
            text += f"SHA-256: {result['SHA-256']}"
            self.hash_result_text.setPlainText(text)
        else:
            QMessageBox.critical(self, "计算失败", f"哈希计算出错：\n{result}")

    def _copy_hash(self, algo):
        """复制指定算法的哈希值。"""
        if not hasattr(self, "_hash_result"):
            QMessageBox.warning(self, "提示", "请先计算哈希值。")
            return

        value = self._hash_result.get(algo, "")
        if value:
            clipboard = QApplication.clipboard()
            clipboard.setText(value)
            QMessageBox.information(self, "已复制", f"{algo} 值已复制到剪贴板。")
        else:
            QMessageBox.warning(self, "提示", f"未找到 {algo} 值。")

    def _copy_all_hashes(self):
        """一键复制所有哈希结果。"""
        if not hasattr(self, "_hash_result"):
            QMessageBox.warning(self, "提示", "请先计算哈希值。")
            return

        text = f"MD5: {self._hash_result['MD5']}\n"
        text += f"SHA-1: {self._hash_result['SHA-1']}\n"
        text += f"SHA-256: {self._hash_result['SHA-256']}"

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "已复制", "全部哈希值已复制到剪贴板。")

    # ==================== 密码生成器标签页 ====================

    def _create_password_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 密码长度
        len_group = QGroupBox("密码长度")
        len_layout = QHBoxLayout()
        len_layout.addWidget(QLabel("长度："))
        self.pwd_length_combo = QComboBox()
        for length in LENGTH_OPTIONS:
            self.pwd_length_combo.addItem(str(length), length)
        self.pwd_length_combo.setCurrentText("16")
        len_layout.addWidget(self.pwd_length_combo)
        len_layout.addStretch()
        len_group.setLayout(len_layout)
        layout.addWidget(len_group)

        # 字符类型
        type_group = QGroupBox("包含字符类型")
        type_layout = QHBoxLayout()
        self.pwd_uppercase = QCheckBox("大写字母 (A-Z)")
        self.pwd_uppercase.setChecked(True)
        self.pwd_lowercase = QCheckBox("小写字母 (a-z)")
        self.pwd_lowercase.setChecked(True)
        self.pwd_digits = QCheckBox("数字 (0-9)")
        self.pwd_digits.setChecked(True)
        self.pwd_symbols = QCheckBox("符号 (!@#$...)")
        self.pwd_symbols.setChecked(True)

        type_layout.addWidget(self.pwd_uppercase)
        type_layout.addWidget(self.pwd_lowercase)
        type_layout.addWidget(self.pwd_digits)
        type_layout.addWidget(self.pwd_symbols)
        type_layout.addStretch()
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # 生成按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_gen = QPushButton("生成密码")
        btn_gen.setObjectName("btnPrimary")
        btn_gen.setMinimumWidth(120)
        btn_gen.clicked.connect(self._do_generate_password)
        btn_layout.addWidget(btn_gen)
        layout.addLayout(btn_layout)

        # 结果显示
        result_group = QGroupBox("生成的密码")
        result_layout = QVBoxLayout()

        self.pwd_result = QTextEdit()
        self.pwd_result.setReadOnly(True)
        self.pwd_result.setMaximumHeight(80)
        self.pwd_result.setPlaceholderText("点击「生成密码」生成随机安全密码...")
        self.pwd_result.setStyleSheet("""
            QTextEdit {
                font-size: 18px;
                font-family: "SF Mono", "Menlo", "Consolas", monospace;
                padding: 8px;
                background-color: #1A1A2E;
                color: #81C784;
            }
        """)
        result_layout.addWidget(self.pwd_result)

        # 强度 + 复制
        action_layout = QHBoxLayout()
        self.pwd_strength_label = QLabel("")
        action_layout.addWidget(self.pwd_strength_label)
        action_layout.addStretch()
        btn_copy_pwd = QPushButton("复制密码")
        btn_copy_pwd.clicked.connect(self._copy_password)
        action_layout.addWidget(btn_copy_pwd)
        result_layout.addLayout(action_layout)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        layout.addStretch()

        return tab

    def _do_generate_password(self):
        """生成随机密码。"""
        try:
            length = self.pwd_length_combo.currentData()
            include_upper = self.pwd_uppercase.isChecked()
            include_lower = self.pwd_lowercase.isChecked()
            include_digits = self.pwd_digits.isChecked()
            include_symbols = self.pwd_symbols.isChecked()

            password = generate_password(
                length=length,
                include_uppercase=include_upper,
                include_lowercase=include_lower,
                include_digits=include_digits,
                include_symbols=include_symbols,
            )

            self.pwd_result.setPlainText(password)

            # 显示强度
            strength, color = get_password_strength_label(password)
            self.pwd_strength_label.setText(f"密码强度：{strength}")
            self.pwd_strength_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: bold;
                color: {color};
            """)

            self._generated_password = password

        except ValueError as e:
            QMessageBox.warning(self, "提示", str(e))

    def _copy_password(self):
        """复制生成的密码。"""
        if not hasattr(self, "_generated_password"):
            QMessageBox.warning(self, "提示", "请先生成密码。")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(self._generated_password)
        QMessageBox.information(self, "已复制", "密码已复制到剪贴板。")
