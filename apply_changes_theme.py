"""
修复 macOS 深色模式下文字与背景同色（不可见）的问题

根本原因：所有 setStyleSheet 写死了浅色背景，但 macOS 深色模式下
          Qt 会把文字色自动调成白色以适应系统主题，导致白字白底。
          Windows 不受影响，因为 Windows Qt 默认样式不跟随系统深色模式改文字色。

修复方法：在 main.py 创建 QApplication 后，强制使用跨平台 Fusion 样式，
          并写死浅色调色板，让文字色固定为深色，不再随系统主题变化。
          只改 main.py 一个文件，不动任何 GUI 代码。
"""

import os
import sys

TARGET_FILE = os.path.join(os.path.dirname(__file__), "main.py")

OLD_BLOCK = """    app = QApplication(sys.argv)
    app.setApplicationName("网页自动取数助手")
    app.setApplicationVersion("1.1.2")
    app.setOrganizationName("WebAutoDownloader")

    # 设置全局字体（优先使用微软雅黑）
    font = QFont()
    font.setFamilies(["Microsoft YaHei", "微软雅黑", "SimHei", "Arial"])
    font.setPixelSize(13)
    app.setFont(font)"""

NEW_BLOCK = """    app = QApplication(sys.argv)
    app.setApplicationName("网页自动取数助手")
    app.setApplicationVersion("1.1.2")
    app.setOrganizationName("WebAutoDownloader")

    # 强制 Fusion 样式 + 写死浅色调色板
    # 避免 macOS 深色模式下 Qt 把文字色改成白色，导致白字白底不可见
    from PySide6.QtWidgets import QStyleFactory
    from PySide6.QtGui import QPalette, QColor
    app.setStyle(QStyleFactory.create("Fusion"))
    light_palette = QPalette()
    _c = QColor
    light_palette.setColor(QPalette.ColorRole.Window,          _c("#f0f2f5"))
    light_palette.setColor(QPalette.ColorRole.WindowText,      _c("#2c3e50"))
    light_palette.setColor(QPalette.ColorRole.Base,            _c("#ffffff"))
    light_palette.setColor(QPalette.ColorRole.AlternateBase,   _c("#f8f9fa"))
    light_palette.setColor(QPalette.ColorRole.Text,            _c("#2c3e50"))
    light_palette.setColor(QPalette.ColorRole.BrightText,      _c("#2c3e50"))
    light_palette.setColor(QPalette.ColorRole.Button,          _c("#ecf0f1"))
    light_palette.setColor(QPalette.ColorRole.ButtonText,      _c("#2c3e50"))
    light_palette.setColor(QPalette.ColorRole.Highlight,       _c("#3498db"))
    light_palette.setColor(QPalette.ColorRole.HighlightedText, _c("#ffffff"))
    light_palette.setColor(QPalette.ColorRole.ToolTipBase,     _c("#ffffff"))
    light_palette.setColor(QPalette.ColorRole.ToolTipText,     _c("#2c3e50"))
    light_palette.setColor(QPalette.ColorRole.PlaceholderText, _c("#95a5a6"))
    light_palette.setColor(QPalette.ColorRole.Link,            _c("#2980b9"))
    light_palette.setColor(QPalette.ColorRole.Midlight,        _c("#e0e0e0"))
    app.setPalette(light_palette)

    # 设置全局字体（优先使用微软雅黑）
    font = QFont()
    font.setFamilies(["Microsoft YaHei", "微软雅黑", "SimHei", "Arial"])
    font.setPixelSize(13)
    app.setFont(font)"""


def main():
    if not os.path.exists(TARGET_FILE):
        print(f"[失败] 找不到目标文件: {TARGET_FILE}")
        sys.exit(1)

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if OLD_BLOCK not in content:
        if NEW_BLOCK in content:
            print("[警告] main.py 已是最新版本，无需修改")
        else:
            print("[失败] 找不到预期代码块，请检查 main.py")
        sys.exit(1)

    new_content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("[成功] main.py 已更新")
    print("  修复内容：强制 Fusion 样式 + 写死浅色调色板")
    print("  效果：macOS 深色模式 / Windows / Linux 下文字均清晰可见")


if __name__ == "__main__":
    main()
