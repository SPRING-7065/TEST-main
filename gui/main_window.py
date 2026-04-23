"""
主窗口
包含：任务列表面板、实时日志面板、帮助Tab、系统托盘
"""
import datetime
import json
import uuid
from typing import List, Optional
 
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit,
    QSplitter, QFrame, QSystemTrayIcon, QMenu,
    QMessageBox, QFileDialog, QApplication, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot, QTimer
from PySide6.QtGui import QIcon, QFont, QTextCursor, QColor, QAction
 
from models.task import Task
from storage.task_store import load_tasks, save_tasks, update_task_status
from storage.settings_store import load_settings
from core import logger, concurrency
from core.scheduler import TaskScheduler
from core.engine import run_task_in_thread, migrate_legacy_cache_if_needed
from gui.task_list_widget import TaskListWidget
from gui.help_widget import HelpWidget
from gui.settings_widget import SettingsWidget
 
class LogSignalBridge(QObject):
    """
    线程安全的日志信号桥
    后台线程产生的日志通过此信号安全传递到GUI线程
    """
    new_log = Signal(str)
 
class MainWindow(QMainWindow):
    """主窗口"""
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖 网页自动取数助手 v1.1.5")
        self.setMinimumSize(900, 560)
        self.resize(1100, 700)

        # 数据
        self._tasks: List[Task] = load_tasks()
        self._running_tasks = {}  # task_id -> TaskThreadWrapper

        # 应用设置（先于调度器/引擎初始化，确保并发上限就位）
        self._settings = load_settings()
        concurrency.set_limit(self._settings.get("concurrency_limit", 2))

        # 一次性迁移老的共享 browser_cache 到首个任务的子目录，保留登录态
        migrate_legacy_cache_if_needed([t.task_id for t in self._tasks])
 
        # 日志信号桥（确保跨线程安全）
        self._log_bridge = LogSignalBridge()
        self._log_bridge.new_log.connect(self._append_log_to_gui)
 
        # 注册日志回调
        logger.register_gui_callback(
            lambda msg: self._log_bridge.new_log.emit(msg)
        )
 
        # 调度器
        self._scheduler = TaskScheduler(task_runner=self._run_task)
        self._scheduler.start()
        self._scheduler.register_all_tasks(self._tasks)
 
        # 构建UI
        self._setup_ui()
        self._setup_tray()
        self._apply_styles()
 
        # 刷新任务列表
        self._task_list_widget.refresh_tasks(self._tasks)
 
        # 启动状态刷新定时器
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_task_status)
        self._status_timer.start(5000)  # 每5秒刷新一次
 
        logger.log_info("网页自动取数助手已启动，欢迎使用！")
 
    # ─────────────────────────────────────────────
    # UI 搭建
    # ─────────────────────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
 
        # 顶部标题栏
        header = self._build_header()
        root_layout.addWidget(header)
 
        # 主体：左右分栏
        main_tabs = QTabWidget()
        main_tabs.setTabPosition(QTabWidget.TabPosition.West)
        main_tabs.setIconSize(__import__('PySide6.QtCore', fromlist=['QSize']).QSize(20, 20))
 
        # Tab: 任务中心
        task_center = self._build_task_center()
        main_tabs.addTab(task_center, "📋\n任务\n中心")
 
        # Tab: 运行日志
        log_tab = self._build_log_tab()
        main_tabs.addTab(log_tab, "📜\n运行\n日志")
 
        # Tab: 设置
        self._settings_tab = SettingsWidget()
        self._settings_tab.settings_changed.connect(self._on_setting_changed)
        main_tabs.addTab(self._settings_tab, "⚙️\n设置")

        # Tab: 使用帮助
        help_tab = HelpWidget()
        main_tabs.addTab(help_tab, "❓\n使用\n帮助")
 
        root_layout.addWidget(main_tabs, 1)
 
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 | 调度中心运行中")
 
    def _build_header(self) -> QWidget:
        """构建顶部标题栏"""
        header = QFrame()
        header.setFixedHeight(44)
        header.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #1a1a2e,stop:0.5 #16213e,stop:1 #0f3460); }"
        )
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
 
        title = QLabel("🤖  网页自动取数助手")
        title.setStyleSheet("color:white; font-size:16px; font-weight:bold;")
        layout.addWidget(title)
 
        layout.addStretch()
 
        subtitle = QLabel("后台静默运行 · 定时自动下载 · 零代码配置")
        subtitle.setStyleSheet("color:#a0aec0; font-size:11px;")
        layout.addWidget(subtitle)
 
        return header
 
    def _build_task_center(self) -> QWidget:
        """构建任务中心面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
 
        # 工具栏
        toolbar = QHBoxLayout()
 
        new_btn = QPushButton("➕  新建任务")
        new_btn.setFixedHeight(38)
        new_btn.setObjectName("primaryBtn")
        new_btn.clicked.connect(self._new_task)
        toolbar.addWidget(new_btn)
 
        import_btn = QPushButton("📥  导入任务")
        import_btn.setFixedHeight(38)
        import_btn.clicked.connect(self._import_task)
        toolbar.addWidget(import_btn)
 
        toolbar.addStretch()
 
        run_all_btn = QPushButton("▶  立即执行所有任务")
        run_all_btn.setFixedHeight(38)
        run_all_btn.clicked.connect(self._run_all_tasks)
        toolbar.addWidget(run_all_btn)
 
        layout.addLayout(toolbar)
 
        # 任务列表组件
        self._task_list_widget = TaskListWidget()
        self._task_list_widget.task_run_requested.connect(self._run_task_by_id)
        self._task_list_widget.task_edit_requested.connect(self._edit_task)
        self._task_list_widget.task_delete_requested.connect(self._delete_task)
        self._task_list_widget.task_stop_requested.connect(self._stop_task)
        self._task_list_widget.task_share_requested.connect(self._share_task)
        layout.addWidget(self._task_list_widget, 1)
 
        return widget
 
    def _build_log_tab(self) -> QWidget:
        """构建日志面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
 
        # 工具栏
        log_toolbar = QHBoxLayout()
        log_toolbar.addWidget(QLabel("📜  实时运行日志"))
        log_toolbar.addStretch()
 
        clear_btn = QPushButton("🗑  清空显示")
        clear_btn.clicked.connect(self._clear_log_display)
        log_toolbar.addWidget(clear_btn)
 
        open_log_btn = QPushButton("📂  打开日志文件")
        open_log_btn.clicked.connect(self._open_log_file)
        log_toolbar.addWidget(open_log_btn)
 
        layout.addLayout(log_toolbar)
 
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet(
            "QTextEdit { background:#1e1e2e; color:#cdd6f4; "
            "border:none; border-radius:6px; padding:8px; }"
        )
        layout.addWidget(self.log_text, 1)
 
        return widget
 
    def _setup_tray(self):
        """设置系统托盘图标"""
        self._tray = QSystemTrayIcon(self)
 
        # 尝试加载图标，失败则使用默认
        try:
            import os, sys
            if getattr(sys, 'frozen', False):
                base = sys._MEIPASS
            else:
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base, "assets", "icon.ico")
            if os.path.exists(icon_path):
                self._tray.setIcon(QIcon(icon_path))
            else:
                self._tray.setIcon(self.style().standardIcon(
                    __import__('PySide6.QtWidgets', fromlist=['QStyle']).QStyle.StandardPixmap.SP_ComputerIcon
                ))
        except Exception:
            pass
 
        tray_menu = QMenu()
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_and_raise)
        tray_menu.addAction(show_action)
 
        tray_menu.addSeparator()
 
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)
 
        self._tray.setContextMenu(tray_menu)
        self._tray.setToolTip("网页自动取数助手 - 后台运行中")
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()
 
    # ─────────────────────────────────────────────
    # 任务操作
    # ─────────────────────────────────────────────
    def _new_task(self):
        """新建任务"""
        from gui.task_editor_dialog import TaskEditorDialog
        from models.task import Task
        dlg = TaskEditorDialog(parent=self)
        if dlg.exec():
            new_task = dlg.get_task()
            self._tasks.append(new_task)
            save_tasks(self._tasks)
            if new_task.schedule.enabled:
                self._scheduler.register_task(new_task)
            self._task_list_widget.refresh_tasks(self._tasks)
            logger.log_info(f"新任务「{new_task.name}」已创建并保存")
 
    def _edit_task(self, task_id: str):
        """编辑任务"""
        task = self._find_task(task_id)
        if not task:
            return
        from gui.task_editor_dialog import TaskEditorDialog
        import copy
        task_copy = copy.deepcopy(task)
        dlg = TaskEditorDialog(task=task_copy, parent=self)
        if dlg.exec():
            updated = dlg.get_task()
            # 替换原任务
            for i, t in enumerate(self._tasks):
                if t.task_id == task_id:
                    self._tasks[i] = updated
                    break
            save_tasks(self._tasks)
            # 重新注册调度
            self._scheduler.unregister_task(task_id)
            if updated.schedule.enabled:
                self._scheduler.register_task(updated)
            self._task_list_widget.refresh_tasks(self._tasks)
            logger.log_info(f"任务「{updated.name}」已更新")
 
    def _delete_task(self, task_id: str):
        """删除任务"""
        task = self._find_task(task_id)
        if not task:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除任务「{task.name}」吗？\n此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._scheduler.unregister_task(task_id)
            self._tasks = [t for t in self._tasks if t.task_id != task_id]
            save_tasks(self._tasks)
            self._task_list_widget.refresh_tasks(self._tasks)
            logger.log_info(f"任务「{task.name}」已删除")

    def _share_task(self, task_id: str):
        """导出任务为可分享文件"""
        task = self._find_task(task_id)
        if not task:
            return

        default_name = f"{task.name}.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出任务", default_name,
            "任务文件 (*.json);;所有文件 (*)"
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"task": task.to_dict()}, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "导出成功", f"任务已保存到：{path}")
            logger.log_info(f"任务「{task.name}」已导出：{path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"任务导出失败：{e}")

    def _import_task(self):
        """从任务文件导入任务"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入任务", "", "任务文件 (*.json);;所有文件 (*)"
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            task_data = data.get("task") if isinstance(data, dict) else None
            if not isinstance(task_data, dict):
                raise ValueError("文件不是有效的任务数据")

            imported = Task.from_dict(task_data)
            # 防止与现有任务ID冲突
            existing_ids = {t.task_id for t in self._tasks}
            if imported.task_id in existing_ids or not imported.task_id:
                imported.task_id = str(uuid.uuid4())[:8]

            self._tasks.append(imported)
            save_tasks(self._tasks)
            self._task_list_widget.refresh_tasks(self._tasks)
            QMessageBox.information(self, "导入成功", f"任务「{imported.name}」已导入")
            logger.log_info(f"任务「{imported.name}」已导入：{path}")
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"任务导入失败：{e}")
 
    def _run_task(self, task: Task):
        """执行任务（供调度器调用，默认静默模式）"""
        self._run_task_by_id(task.task_id, debug_mode=False)
 
    def _run_task_by_id(self, task_id: str, debug_mode: bool = False):
        """通过ID执行任务，debug_mode=True时显示浏览器窗口"""
        task = self._find_task(task_id)
        if not task:
            return

        if task_id in self._running_tasks:
            runner = self._running_tasks[task_id]
            if runner.is_alive():
                logger.log_warning(f"任务「{task.name}」正在运行中，请等待完成后再触发")
                return

        def on_status_change(tid: str, status: str):
            update_task_status(
                tid, status,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            # 携带 task_id：让 UI 只更新该任务卡片，不重建整个列表
            # （v1.1.4 重建会清掉其他正在运行任务的截图/进度）
            self._log_bridge.new_log.emit(f"__STATUS_UPDATE__{tid}")

        def on_completion(tid: str, success: bool):
            if tid in self._running_tasks:
                del self._running_tasks[tid]
            self._log_bridge.new_log.emit(f"__CLEAR_RUNNING_UI__{tid}")

        def on_screenshot(img_bytes: bytes):
            import base64
            b64 = base64.b64encode(img_bytes).decode()
            self._log_bridge.new_log.emit(f"__SCREENSHOT__{task_id}__{b64}")

        def on_progress(current: int, total: int, step_name: str):
            self._log_bridge.new_log.emit(
                f"__PROGRESS__{task_id}__{current}__{total}__{step_name}"
            )

        runner = run_task_in_thread(
            task=task,
            status_callback=on_status_change,
            completion_callback=on_completion,
            screenshot_callback=on_screenshot,
            progress_callback=on_progress,
            debug_mode=debug_mode,
        )
        self._running_tasks[task_id] = runner
 
    def _run_all_tasks(self):
        """立即执行所有任务"""
        if not self._tasks:
            QMessageBox.information(self, "提示", "还没有配置任何任务，请先新建任务！")
            return
        for task in self._tasks:
            self._run_task_by_id(task.task_id)
 
    def _on_setting_changed(self, key: str, value):
        """设置面板改动时触发，目前并发上限已在 SettingsWidget 内部直接生效"""
        self._settings[key] = value
        if key == "concurrency_limit":
            logger.log_info(f"并发上限已更新为 {value}")

    def _stop_task(self, task_id: str):
        """停止正在运行的任务"""
        task = self._find_task(task_id)
        if not task:
            return
 
        runner = self._running_tasks.get(task_id)
        if not runner:
            QMessageBox.information(self, "提示", f"任务「{task.name}」当前未在运行，无需停止。")
            return
 
        if not runner.is_alive():
            self._running_tasks.pop(task_id, None)
            QMessageBox.information(self, "提示", f"任务「{task.name}」已完成或已停止，无需重复停止。")
            return
 
        runner.stop()
        logger.log_warning(f"已请求停止任务「{task.name}」，将在当前步骤完成后停止。")
        QMessageBox.information(
            self, "停止请求已发送",
            f"任务「{task.name}」的停止请求已发送，程序会在当前步骤完成后安全终止。"
        )
 
    def _find_task(self, task_id: str) -> Optional[Task]:
        for t in self._tasks:
            if t.task_id == task_id:
                return t
        return None
 
    # ─────────────────────────────────────────────
    # 日志
    # ─────────────────────────────────────────────
    @Slot(str)
    def _append_log_to_gui(self, message: str):
        """将日志追加到GUI文本框（主线程安全）"""
        if message.startswith("__STATUS_UPDATE__"):
            tid = message.replace("__STATUS_UPDATE__", "", 1)
            # 仅同步内存中该任务的状态字段，避免重建任务列表
            from storage.task_store import load_tasks as _ld
            disk_tasks = {t.task_id: t for t in _ld()}
            for t in self._tasks:
                disk_t = disk_tasks.get(t.task_id)
                if disk_t is not None:
                    t.last_run_status = disk_t.last_run_status
                    t.last_run_time = disk_t.last_run_time
            if tid:
                self._task_list_widget.update_task_status_only(tid)
            else:
                # 兜底：旧消息格式无 task_id 时回退到全量刷新
                self._task_list_widget.refresh_tasks(self._tasks)
            return

        if message.startswith("__CLEAR_RUNNING_UI__"):
            task_id = message.replace("__CLEAR_RUNNING_UI__", "")
            self._task_list_widget.clear_task_running_ui(task_id)
            return

        if message.startswith("__PROGRESS__"):
            parts = message.split("__")
            if len(parts) >= 6:
                task_id = parts[2]
                try:
                    current = int(parts[3])
                    total = int(parts[4])
                    step_name = "__".join(parts[5:])
                    self._task_list_widget.update_task_progress(
                        task_id, current, total, step_name
                    )
                except ValueError:
                    pass
            return

        if message.startswith("__SCREENSHOT__"):
            parts = message.split("__", 4)
            if len(parts) >= 4:
                task_id = parts[2]
                b64 = parts[3]
                try:
                    import base64
                    img_bytes = base64.b64decode(b64)
                    self._task_list_widget.update_task_screenshot(
                        task_id, img_bytes
                    )
                except Exception:
                    pass
            return
 
        # 根据日志级别设置颜色
        if "✅ 成功" in message:
            color = "#a6e3a1"   # 绿色
        elif "❌ 错误" in message:
            color = "#f38ba8"   # 红色
        elif "⚠️ 警告" in message:
            color = "#fab387"   # 橙色
        else:
            color = "#cdd6f4"   # 默认白色
 
        if not hasattr(self, 'log_text'):
            return
        self.log_text.setTextColor(QColor(color))
        self.log_text.append(message)
 
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
 
        # 更新状态栏
        self.status_bar.showMessage(message[:80] + "..." if len(message) > 80 else message)
 
    def _clear_log_display(self):
        """清空日志显示区（不影响文件）"""
        self.log_text.clear()
 
    def _open_log_file(self):
        """用系统默认程序打开日志文件"""
        import os, subprocess
        log_path = logger.get_log_file_path()
        if os.path.exists(log_path):
            os.startfile(log_path)
        else:
            QMessageBox.information(self, "提示", "日志文件还不存在，运行任务后会自动生成")
 
    def _refresh_task_status(self):
        """定期刷新任务状态显示
        仅同步状态字段并精准更新对应卡片，不重建整个列表，
        否则会清空正在运行任务的截图和进度。
        """
        disk_tasks = {t.task_id: t for t in load_tasks()}
        changed_ids = []
        for t in self._tasks:
            disk_t = disk_tasks.get(t.task_id)
            if disk_t is None:
                continue
            if (t.last_run_status != disk_t.last_run_status or
                    t.last_run_time != disk_t.last_run_time):
                t.last_run_status = disk_t.last_run_status
                t.last_run_time = disk_t.last_run_time
                changed_ids.append(t.task_id)
        for tid in changed_ids:
            self._task_list_widget.update_task_status_only(tid)
 
    # ─────────────────────────────────────────────
    # 窗口事件
    # ─────────────────────────────────────────────
    def show_and_raise(self):
        self.show()
        self.raise_()
        self.activateWindow()
 
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_raise()
 
    def closeEvent(self, event):
        """关闭时最小化到托盘而非退出"""
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "网页自动取数助手",
            "程序已最小化到系统托盘，定时任务继续在后台运行。\n双击托盘图标可重新显示窗口。",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
 
    def _quit_app(self):
        """真正退出程序"""
        reply = QMessageBox.question(
            self, "确认退出",
            "退出后所有定时任务将停止运行。\n确定要退出吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._scheduler.stop()
            self._tray.hide()
            QApplication.quit()
 
    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background: #f0f2f5; }
            QTabWidget[tabPosition="2"]::pane {
                border: none;
                background: #f0f2f5;
            }
            QTabWidget[tabPosition="2"] QTabBar::tab {
                width: 52px;
                height: 58px;
                font-size: 10px;
                text-align: center;
                border: 1px solid #ddd;
                border-right: none;
                border-radius: 4px 0 0 4px;
                background: #e8e8e8;
                margin-bottom: 3px;
                padding: 5px;
            }
            QTabWidget[tabPosition="2"] QTabBar::tab:selected {
                background: white;
                font-weight: bold;
                color: #2980b9;
                border-right: 2px solid white;
            }
            QPushButton#primaryBtn {
                background: #2980b9;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 5px;
                padding: 0 16px;
            }
            QPushButton#primaryBtn:hover { background: #3498db; }
            QStatusBar { 
                background: #2c3e50; 
                color: #ecf0f1; 
                font-size: 11px;
                padding: 2px 8px;
            }
        """)