"""
程序入口
负责：初始化Qt应用、设置高DPI、启动主窗口
"""
import sys
import os

def setup_environment():
    """
    设置运行环境
    PyInstaller打包后需要正确设置工作目录和资源路径
    """
    # 如果是PyInstaller打包后的exe
    if getattr(sys, 'frozen', False):
        # exe所在目录作为工作目录
        app_dir = os.path.dirname(sys.executable)
        os.chdir(app_dir)

        # 将打包的内部资源路径加入sys.path
        bundle_dir = sys._MEIPASS
        if bundle_dir not in sys.path:
            sys.path.insert(0, bundle_dir)
    else:
        # 开发模式：项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_root)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

def main():
    setup_environment()

    # 必须在创建QApplication之前设置高DPI属性
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QIcon

    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("网页自动取数助手")
    app.setApplicationVersion("1.1.3")
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
    app.setFont(font)

    # 设置应用图标
    try:
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "assets", "icon.ico")
        else:
            icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "assets", "icon.ico"
            )
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass

    # 启动主窗口
    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()