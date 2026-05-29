"""
离线文件保险箱 - 应用程序入口

初始化 PySide6 应用并启动主窗口。
"""

import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.ui.main_window import MainWindow


def main():
    """启动离线文件保险箱应用程序。"""
    app = QApplication(sys.argv)
    app.setApplicationName("离线文件保险箱")
    app.setOrganizationName("Cymaple")

    # 设置应用级样式
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
