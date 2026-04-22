"""
任务列表管理面板
卡片支持：进度条、截图预览、调试模式执行
"""
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
    QProgressBar, QMenu, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage

from models.task import Task

STATUS_CONFIG = {
    "never":   {"text": "从未执行",    "color": "#95a5a6", "bg": "#ecf0f1"},
    "running": {"text": "⚙️ 执行中...", "color": "#e67e22", "bg": "#fef9e7"},
    "success": {"text": "✅ 上次成功",  "color": "#27ae60", "bg": "#eafaf1"},
    "failed":  {"text": "❌ 上次失败",  "color": "#e74c3c", "bg": "#fdedec"},
    "stopped": {"text": "⏹ 已停止",    "color": "#7f8c8d", "bg": "#f2f3f4"},
}

class ScreenshotDialog(QDialog):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("浏览器实时画面")
        self.setModal(False)
        layout = QVBoxLayout(self)
        label = QLabel()
        scaled = pixmap.scaled(
            1280, 800,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(scaled)
        layout.addWidget(label)
        self.resize(scaled.width() + 20, scaled.height() + 20)

class TaskCard(QFrame):
    run_clicked = Signal(str, bool)
    edit_clicked = Signal(str)
    delete_clicked = Signal(str)
    stop_clicked = Signal(str)
    share_clicked = Signal(str)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self._current_pixmap: Optional[QPixmap] = None
        self._screenshot_dialog: Optional[ScreenshotDialog] = None
        self._setup_ui()
        self._apply_card_style()

    def _setup_ui(self):
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(6)

        # 第一行：状态条 + 信息 + 按钮
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        status_bar = QFrame()
        status_bar.setFixedWidth(5)
        status_bar.setStyleSheet(
            f"background:{STATUS_CONFIG.get(self.task.last_run_status, STATUS_CONFIG['never'])['color']};"
            "border-radius:3px;"
        )
        top_row.addWidget(status_bar)

        info = QVBoxLayout()
        info.setSpacing(3)

        name_row = QHBoxLayout()
        self.name_label = QLabel(self.task.name)
        self.name_label.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#2c3e50;"
        )
        name_row.addWidget(self.name_label)

        if self.task.schedule.enabled:
            sched_label = QLabel(f"⏰ {self._get_schedule_text()}")
            sched_label.setStyleSheet(
                "background:#d6eaf8; color:#1a5276; padding:2px 8px;"
                "border-radius:10px; font-size:11px;"
            )
            name_row.addWidget(sched_label)
        name_row.addStretch()
        info.addLayout(name_row)

        if self.task.description:
            desc = QLabel(self.task.description)
            desc.setStyleSheet("color:#7f8c8d; font-size:12px;")
            info.addWidget(desc)

        meta_row = QHBoxLayout()
        steps_lbl = QLabel(f"📋 {len(self.task.steps)} 个步骤")
        steps_lbl.setStyleSheet("color:#95a5a6; font-size:11px;")
        meta_row.addWidget(steps_lbl)

        status_cfg = STATUS_CONFIG.get(
            self.task.last_run_status, STATUS_CONFIG["never"]
        )
        self.status_label = QLabel(status_cfg["text"])
        self.status_label.setStyleSheet(
            f"color:{status_cfg['color']}; font-size:11px; font-weight:bold;"
        )
        meta_row.addWidget(self.status_label)

        if self.task.last_run_time:
            time_lbl = QLabel(f"  最后执行：{self.task.last_run_time}")
            time_lbl.setStyleSheet("color:#bdc3c7; font-size:11px;")
            meta_row.addWidget(time_lbl)
        meta_row.addStretch()
        info.addLayout(meta_row)
        top_row.addLayout(info, 1)

        # 右侧按钮
        btn_col = QVBoxLayout()
        btn_col.setSpacing(5)
        is_running = self.task.last_run_status == "running"

        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setFixedSize(88, 28)
        self._stop_btn.setStyleSheet(
            "QPushButton{background:#e74c3c;color:white;border-radius:4px;"
            "font-weight:bold;border:none;}"
            "QPushButton:hover{background:#c0392b;}"
        )
        self._stop_btn.clicked.connect(
            lambda: self.stop_clicked.emit(self.task.task_id)
        )
        self._stop_btn.setVisible(is_running)
        btn_col.addWidget(self._stop_btn)

        self._run_btn = QPushButton("▶ 立即执行 ▼")
        self._run_btn.setFixedSize(88, 28)
        self._run_btn.setStyleSheet(
            "QPushButton{background:#27ae60;color:white;border-radius:4px;"
            "font-weight:bold;border:none;padding-left:6px;}"
            "QPushButton:hover{background:#2ecc71;}"
        )
        self._run_btn.clicked.connect(self._show_run_menu)
        self._run_btn.setVisible(not is_running)
        btn_col.addWidget(self._run_btn)

        edit_btn = QPushButton("✏️ 编辑")
        edit_btn.setFixedSize(88, 28)
        edit_btn.setStyleSheet(
            "QPushButton{background:#3498db;color:white;border-radius:4px;"
            "font-weight:bold;border:none;}"
            "QPushButton:hover{background:#2980b9;}"
        )
        edit_btn.clicked.connect(
            lambda: self.edit_clicked.emit(self.task.task_id)
        )
        btn_col.addWidget(edit_btn)

        share_btn = QPushButton("🔗 分享")
        share_btn.setFixedSize(88, 28)
        share_btn.setStyleSheet(
            "QPushButton{background:#9b59b6;color:white;border-radius:4px;"
            "font-weight:bold;border:none;}"
            "QPushButton:hover{background:#8e44ad;}"
        )
        share_btn.clicked.connect(
            lambda: self.share_clicked.emit(self.task.task_id)
        )
        btn_col.addWidget(share_btn)

        del_btn = QPushButton("🗑 删除")
        del_btn.setFixedSize(88, 28)
        del_btn.setStyleSheet(
            "QPushButton{background:#ecf0f1;color:#e74c3c;border-radius:4px;"
            "border:1px solid #e74c3c;}"
            "QPushButton:hover{background:#fdedec;}"
        )
        del_btn.clicked.connect(
            lambda: self.delete_clicked.emit(self.task.task_id)
        )
        btn_col.addWidget(del_btn)

        top_row.addLayout(btn_col)
        root.addLayout(top_row)

        # 第二行：进度条
        self.progress_widget = QWidget()
        pw_layout = QHBoxLayout(self.progress_widget)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none; border-radius: 4px; background: #ecf0f1;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #3498db, stop:1 #27ae60);
            }
        """)
        self.progress_label = QLabel("准备中...")
        self.progress_label.setStyleSheet("color:#7f8c8d; font-size:11px;")
        self.progress_label.setFixedWidth(180)

        pw_layout.addWidget(self.progress_bar)
        pw_layout.addWidget(self.progress_label)
        self.progress_widget.setVisible(False)
        root.addWidget(self.progress_widget)

        # 第三行：截图预览
        self.screenshot_widget = QWidget()
        ss_layout = QHBoxLayout(self.screenshot_widget)
        ss_layout.setContentsMargins(0, 0, 0, 0)
        ss_layout.setSpacing(12)

        self.screenshot_label = QLabel("等待截图...")
        self.screenshot_label.setFixedSize(192, 108)
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setStyleSheet(
            "background:#1e1e2e; color:#666; border-radius:4px;"
            "border:1px solid #444; font-size:11px;"
        )
        self.screenshot_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.screenshot_label.mousePressEvent = self._on_screenshot_clicked
        ss_layout.addWidget(self.screenshot_label)

        hint = QLabel(
            "🖥️ 浏览器实时画面\n（每4秒自动刷新）\n\n点击截图可放大查看"
        )
        hint.setStyleSheet("color:#7f8c8d; font-size:10px;")
        ss_layout.addWidget(hint)
        ss_layout.addStretch()

        self.screenshot_widget.setVisible(False)
        root.addWidget(self.screenshot_widget)

    def _show_run_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white; border: 1px solid #ddd;
                border-radius: 6px; padding: 4px;
            }
            QMenu::item { padding: 8px 20px; border-radius: 4px; font-size: 13px; }
            QMenu::item:selected { background: #eaf2ff; color: #2980b9; }
        """)
        normal_action = menu.addAction("🔇  后台静默执行（默认）")
        debug_action  = menu.addAction("🖥️  调试模式执行（显示浏览器）")

        btn = self.sender()
        action = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

        if action == normal_action:
            self.run_clicked.emit(self.task.task_id, False)
        elif action == debug_action:
            self.run_clicked.emit(self.task.task_id, True)

    def update_progress(self, current: int, total: int, step_name: str):
        self.progress_widget.setVisible(True)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"[{current}/{total}] {step_name[:28]}")

    def update_screenshot(self, img_bytes: bytes):
        try:
            image = QImage.fromData(img_bytes)
            if image.isNull():
                return
            pixmap = QPixmap.fromImage(image)
            self._current_pixmap = pixmap
            scaled = pixmap.scaled(
                192, 108,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.screenshot_label.setPixmap(scaled)
            self.screenshot_label.setText("")
            self.screenshot_widget.setVisible(True)
            if self._screenshot_dialog and self._screenshot_dialog.isVisible():
                self._screenshot_dialog.close()
                self._screenshot_dialog = ScreenshotDialog(pixmap, self)
                self._screenshot_dialog.show()
        except Exception:
            pass

    def show_screenshot_panel(self, visible: bool):
        self.screenshot_widget.setVisible(visible)
        if not visible:
            self.progress_widget.setVisible(False)

    def refresh_status(self):
        """任务完成后刷新按钮状态和状态标签"""
        is_running = self.task.last_run_status == "running"
        self._stop_btn.setVisible(is_running)
        self._run_btn.setVisible(not is_running)
        status_cfg = STATUS_CONFIG.get(
            self.task.last_run_status, STATUS_CONFIG["never"]
        )
        self.status_label.setText(status_cfg["text"])
        self.status_label.setStyleSheet(
            f"color:{status_cfg['color']}; font-size:11px; font-weight:bold;"
        )
        self._apply_card_style()

    def _on_screenshot_clicked(self, event):
        if self._current_pixmap:
            self._screenshot_dialog = ScreenshotDialog(
                self._current_pixmap, self
            )
            self._screenshot_dialog.show()

    def _get_schedule_text(self) -> str:
        sch = self.task.schedule
        t = sch.run_time
        if sch.schedule_type == "daily":
            return f"每天{t}"
        elif sch.schedule_type == "weekly":
            names = ["一","二","三","四","五","六","日"]
            days = "".join(
                f"周{names[d]}" for d in sch.weekdays if 0 <= d <= 6
            )
            return f"{days} {t}"
        elif sch.schedule_type == "monthly":
            days = ",".join(str(d) for d in sch.monthdays)
            return f"每月{days}号 {t}"
        return f"单次 {t}"

    def _apply_card_style(self):
        status = self.task.last_run_status
        bg = STATUS_CONFIG.get(status, STATUS_CONFIG["never"])["bg"]
        self.setStyleSheet(f"""
            TaskCard {{
                background: {bg};
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
            TaskCard:hover {{
                border-color: #3498db;
                background: white;
            }}
        """)

class TaskListWidget(QWidget):
    task_run_requested  = Signal(str, bool)
    task_edit_requested = Signal(str)
    task_delete_requested = Signal(str)
    task_stop_requested = Signal(str)
    task_share_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(4, 4, 4, 4)

        self._empty_label = QLabel(
            "🎉 还没有任何任务\n\n"
            "点击上方「➕ 新建任务」开始配置您的第一个自动化任务"
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            "color:#bdc3c7; font-size:16px; padding:60px;"
        )
        self._cards_layout.addWidget(self._empty_label)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_container)
        layout.addWidget(scroll)

    def refresh_tasks(self, tasks: List[Task]):
        while self._cards_layout.count() > 0:
            item = self._cards_layout.takeAt(0)
            if item.widget() and item.widget() is not self._empty_label:
                item.widget().deleteLater()
        self._cards.clear()

        if not tasks:
            self._empty_label.setVisible(True)
            self._cards_layout.addWidget(self._empty_label)
            self._cards_layout.addStretch()
            return

        self._empty_label.setVisible(False)
        for task in tasks:
            card = TaskCard(task)
            card.run_clicked.connect(self.task_run_requested)
            card.edit_clicked.connect(self.task_edit_requested)
            card.delete_clicked.connect(self.task_delete_requested)
            card.stop_clicked.connect(self.task_stop_requested)
            card.share_clicked.connect(self.task_share_requested)
            self._cards_layout.addWidget(card)
            self._cards[task.task_id] = card
        self._cards_layout.addStretch()

    def update_task_progress(self, task_id: str,
                              current: int, total: int, step_name: str):
        card = self._cards.get(task_id)
        if card:
            card.update_progress(current, total, step_name)

    def update_task_screenshot(self, task_id: str, img_bytes: bytes):
        card = self._cards.get(task_id)
        if card:
            card.update_screenshot(img_bytes)

    def clear_task_running_ui(self, task_id: str):
        card = self._cards.get(task_id)
        if card:
            card.show_screenshot_panel(False)
            card.refresh_status()
