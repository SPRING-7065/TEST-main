"""
应用设置面板
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QCheckBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from storage.settings_store import load_settings, update_setting
from core import concurrency


class SettingsWidget(QWidget):
    settings_changed = Signal(str, object)  # key, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = load_settings()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QLabel("⚙️  应用设置")
        header.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#2c3e50; "
            "padding:16px 20px; background:white; "
            "border-bottom:2px solid #3498db;"
        )
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, 1)

        body = QWidget()
        body.setStyleSheet("background:#f7f9fc;")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        layout.addWidget(self._build_concurrency_section())
        layout.addWidget(self._build_window_section())
        layout.addStretch(1)

        scroll.setWidget(body)

    def _build_concurrency_section(self) -> QWidget:
        card = QFrame()
        card.setStyleSheet(
            "QFrame{background:white; border:1px solid #dfe6ec; border-radius:8px;}"
        )
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(10)

        title = QLabel("🚀 并发执行上限")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#2c3e50;")
        v.addWidget(title)

        row = QHBoxLayout()
        row.addWidget(QLabel("同时最多执行任务数："))
        self._concurrency_spin = QSpinBox()
        self._concurrency_spin.setRange(1, 8)
        self._concurrency_spin.setValue(self._settings.get("concurrency_limit", 2))
        self._concurrency_spin.setFixedWidth(80)
        self._concurrency_spin.valueChanged.connect(self._on_concurrency_changed)
        row.addWidget(self._concurrency_spin)
        row.addStretch(1)
        v.addLayout(row)

        explain = QLabel(
            "<div style='color:#34495e; font-size:12px; line-height:1.7;'>"
            "<b>这个数值代表什么：</b>同一时刻最多可并行执行多少个任务"
            "（包含调度器自动触发 + 手动点击执行）。超过上限的任务会进入"
            "「⏳ 等待槽位」状态排队，前一个跑完才启动下一个。<br><br>"
            "<b>推荐配置：</b>"
            "<ul style='margin:4px 0 0 0; padding-left:20px;'>"
            "<li><b>1</b>：完全串行。最稳定、内存占用最低。"
            "适合 4GB 内存或赛扬/奔腾老旧机器。</li>"
            "<li><b>2（默认）</b>：双任务并行。"
            "i5/i7 + 8-16GB 内存的稳妥选择。</li>"
            "<li><b>3-4</b>：i7-7700 / i7-12700 + 16GB 这类配置的甜蜜点；"
            "若任务页面很重（含大量图片/视频/复杂 JS）建议降到 2-3。</li>"
            "<li><b>5+</b>：仅推荐 i9/Ryzen 9 + 32GB+ 高配机。"
            "集成显卡（如 HD 630 / UHD 770）超过 4 个浏览器并发"
            "可能出现渲染白屏或截图全黑。</li>"
            "</ul><br>"
            "<b>资源占用参考：</b>每个任务约占 <b>300-500MB 内存</b> + "
            "<b>~1 个 CPU 核心</b>。超出可承受范围后表现为"
            "页面加载缓慢、超时增多、偶发白屏。"
            "</div>"
        )
        explain.setWordWrap(True)
        explain.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(explain)

        return card

    def _build_window_section(self) -> QWidget:
        card = QFrame()
        card.setStyleSheet(
            "QFrame{background:white; border:1px solid #dfe6ec; border-radius:8px;}"
        )
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(10)

        title = QLabel("🪟 窗口行为")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#2c3e50;")
        v.addWidget(title)

        self._auto_min_chk = QCheckBox("拾取/录制时自动最小化主窗口（避免遮挡浏览器）")
        self._auto_min_chk.setChecked(
            self._settings.get("auto_minimize_on_picker", True)
        )
        self._auto_min_chk.toggled.connect(self._on_auto_minimize_changed)
        v.addWidget(self._auto_min_chk)

        return card

    def _on_concurrency_changed(self, value: int):
        update_setting("concurrency_limit", int(value))
        concurrency.set_limit(int(value))
        self.settings_changed.emit("concurrency_limit", int(value))

    def _on_auto_minimize_changed(self, checked: bool):
        update_setting("auto_minimize_on_picker", bool(checked))
        self.settings_changed.emit("auto_minimize_on_picker", bool(checked))
