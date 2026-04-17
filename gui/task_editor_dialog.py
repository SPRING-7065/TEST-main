"""
任务编辑对话框
包含：任务基本信息、步骤链编辑、调度配置
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QGroupBox, QCheckBox, QComboBox, QSpinBox, QTimeEdit,
    QMessageBox, QWidget, QSplitter, QFrame, QScrollArea,
    QButtonGroup, QRadioButton, QGridLayout, QTabWidget,
    QFileDialog
)
from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtGui import QFont

from models.task import Task, ScheduleConfig
from models.step import Step, StepType, STEP_TYPE_LABELS
from gui.visual_picker_window import VisualPickerWindow

class StepListItem(QListWidgetItem):
    """步骤列表项，持有Step对象引用"""
    def __init__(self, step: Step):
        super().__init__()
        self.step = step
        self.refresh_text()

    def refresh_text(self):
        self.setText(self.step.get_display_name())

class ManualStepDialog(QDialog):
    """
    手动添加/编辑单个步骤的对话框
    当用户不使用可视化拾取时，通过此对话框手动填写步骤参数
    """
    def __init__(self, step: Step = None, parent=None):
        super().__init__(parent)
        self.step = step or Step()
        self._is_new = step is None
        self.setWindowTitle("配置步骤")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        self._load_step()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)

        # 步骤类型
        grid.addWidget(QLabel("步骤类型 *："), 0, 0)
        self.type_combo = QComboBox()
        for stype, label in STEP_TYPE_LABELS.items():
            self.type_combo.addItem(label, stype)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        grid.addWidget(self.type_combo, 0, 1)

        # 步骤名称
        grid.addWidget(QLabel("步骤名称："), 1, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("给这步骤起个好记的名字（可选）")
        grid.addWidget(self.name_input, 1, 1)

        # CSS选择器
        self.selector_label = QLabel("CSS选择器 *：")
        grid.addWidget(self.selector_label, 2, 0)
        self.selector_input = QLineEdit()
        self.selector_input.setFont(QFont("Consolas", 10))
        self.selector_input.setPlaceholderText("例如：#loginBtn 或 input[name='username']")
        grid.addWidget(self.selector_input, 2, 1)

        # 选择器类型
        grid.addWidget(QLabel("选择器类型："), 3, 0)
        self.sel_type_combo = QComboBox()
        self.sel_type_combo.addItem("CSS选择器（推荐）", "css")
        self.sel_type_combo.addItem("XPath", "xpath")
        self.sel_type_combo.addItem("文本内容匹配", "text")
        grid.addWidget(self.sel_type_combo, 3, 1)

        # 值/URL
        self.value_label = QLabel("输入内容/URL：")
        grid.addWidget(self.value_label, 4, 0)
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("支持时间占位符：[TODAY] [TODAY-1] [MONTH_START]")
        grid.addWidget(self.value_input, 4, 1)

        # 超时
        grid.addWidget(QLabel("超时时间："), 5, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(120)
        self.timeout_spin.setSuffix(" 秒")
        grid.addWidget(self.timeout_spin, 5, 1)

        # 可选步骤
        self.optional_check = QCheckBox("可选步骤（失败后不中断任务，继续下一步）")
        grid.addWidget(self.optional_check, 6, 0, 1, 2)

        layout.addLayout(grid)

        # 选择器校验警告（当选择器为纯标签名时显示）
        self.selector_warn_label = QLabel(
            "⚠️  当前选择器是纯标签名（如 i / div / span），页面上往往有很多这样的元素，"
            "运行时会随机点到别的地方。\n"
            "请改用带 class 的精准写法，例如：div.switch-login-icon 或 i.ri-nr-code-line\n"
            "提示：在调试模式的浏览器里，右键目标元素 → 检查，可以看到正确的 class 名称。"
        )
        self.selector_warn_label.setWordWrap(True)
        self.selector_warn_label.setStyleSheet(
            "background:#fff3cd; color:#856404; border:1px solid #ffc107; "
            "border-radius:4px; padding:8px 12px; font-size:11px;"
        )
        self.selector_warn_label.setVisible(False)
        layout.addWidget(self.selector_warn_label)
        self.selector_input.textChanged.connect(self._check_selector_warn)

        # 占位符说明
        hint_box = QGroupBox("💡 时间占位符说明")
        hint_layout = QVBoxLayout(hint_box)
        from core.variable_parser import get_available_placeholders
        hints = get_available_placeholders()
        hint_text = "  ".join([f"{ph} → {desc}" for ph, desc in hints[:5]])
        hint_label = QLabel(hint_text)
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: #555; font-size: 11px;")
        hint_layout.addWidget(hint_label)
        layout.addWidget(hint_box)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("✅ 确定")
        ok_btn.setFixedSize(100, 35)
        ok_btn.setStyleSheet(
            "QPushButton { background: #2980b9; color: white; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #3498db; }"
        )
        ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 35)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _load_step(self):
        """加载步骤数据到界面"""
        # 设置步骤类型
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.step.step_type:
                self.type_combo.setCurrentIndex(i)
                break
        self.name_input.setText(self.step.description)
        self.selector_input.setText(self.step.selector)
        self.value_input.setText(self.step.value)
        self.timeout_spin.setValue(self.step.timeout)
        self.optional_check.setChecked(self.step.optional)

        # 设置选择器类型
        for i in range(self.sel_type_combo.count()):
            if self.sel_type_combo.itemData(i) == self.step.selector_type:
                self.sel_type_combo.setCurrentIndex(i)
                break

        self._on_type_changed()

    def _check_selector_warn(self, text: str):
        """当选择器是纯标签名时显示警告"""
        import re
        text = text.strip()
        # 纯字母（bare tag name）才报警，带 . # [ 等的都是精准选择器
        is_bare_tag = bool(text) and bool(re.fullmatch(r'[a-zA-Z][a-zA-Z0-9]*', text))
        if hasattr(self, 'selector_warn_label'):
            self.selector_warn_label.setVisible(is_bare_tag)

    def _on_type_changed(self):
        """根据步骤类型动态调整界面"""
        stype = self.type_combo.currentData()

        # 控制选择器显示
        need_selector = stype not in (StepType.OPEN_URL, StepType.WAIT)
        self.selector_label.setVisible(need_selector)
        self.selector_input.setVisible(need_selector)
        self.sel_type_combo.setVisible(need_selector)
        # 选择器隐藏时同步隐藏警告
        if not need_selector and hasattr(self, 'selector_warn_label'):
            self.selector_warn_label.setVisible(False)

        # 控制值显示及提示
        need_value = stype in (
            StepType.OPEN_URL, StepType.INPUT, StepType.SELECT,
            StepType.WAIT, StepType.SCROLL
        )
        self.value_label.setVisible(need_value)
        self.value_input.setVisible(need_value)

        if stype == StepType.OPEN_URL:
            self.value_label.setText("网页地址 *：")
            self.value_input.setPlaceholderText("https://www.example.com")
        elif stype == StepType.INPUT:
            self.value_label.setText("输入内容 *：")
            self.value_input.setPlaceholderText("支持占位符：[TODAY] [TODAY-1] [MONTH_START]")
        elif stype == StepType.SELECT:
            self.value_label.setText("选择选项 *：")
            self.value_input.setPlaceholderText("下拉框的选项文字")
        elif stype == StepType.WAIT:
            self.value_label.setText("等待秒数 *：")
            self.value_input.setPlaceholderText("例如：3")
        elif stype == StepType.SCROLL:
            self.value_label.setText("滚动方式：")
            self.value_input.setPlaceholderText("bottom=底部  top=顶部  数字=像素数")

    def _on_ok(self):
        """保存步骤"""
        stype = self.type_combo.currentData()

        # 验证必填项
        if stype == StepType.OPEN_URL and not self.value_input.text().strip():
            QMessageBox.warning(self, "提示", "请填写网页地址！")
            return
        if stype not in (StepType.OPEN_URL, StepType.WAIT) and not self.selector_input.text().strip():
            QMessageBox.warning(self, "提示", "请填写CSS选择器！\n（可使用可视化拾取自动获取）")
            return

        self.step.step_type = stype
        self.step.description = self.name_input.text().strip()
        self.step.selector = self.selector_input.text().strip()
        self.step.selector_type = self.sel_type_combo.currentData()
        self.step.value = self.value_input.text().strip()
        self.step.timeout = self.timeout_spin.value()
        self.step.optional = self.optional_check.isChecked()

        self.accept()

    def get_step(self) -> Step:
        return self.step

class TaskEditorDialog(QDialog):
    """任务编辑对话框（完整版）"""

    def __init__(self, task: Task = None, parent=None):
        super().__init__(parent)
        self.task = task or Task()
        self._is_new = task is None
        self._picker_window: VisualPickerWindow = None

        self.setWindowTitle(f"{'新建任务' if self._is_new else '编辑任务'} — {self.task.name}")
        self.setMinimumSize(850, 720)
        self.resize(950, 780)

        self._setup_ui()
        self._load_task_data()
        self._apply_styles()

    # ─────────────────────────────────────────────
    # UI 搭建
    # ─────────────────────────────────────────────
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(10, 10, 10, 10)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1 基本信息
        basic_widget = QWidget()
        self._setup_basic_tab(basic_widget)
        tabs.addTab(basic_widget, "📋  基本信息")

        # Tab 2 步骤配置
        steps_widget = QWidget()
        self._setup_steps_tab(steps_widget)
        tabs.addTab(steps_widget, "🔧  操作步骤")

        # Tab 3 调度设置
        schedule_widget = QWidget()
        self._setup_schedule_tab(schedule_widget)
        tabs.addTab(schedule_widget, "⏰  定时计划")

        main_layout.addWidget(tabs, 1)

        # 底部按钮栏
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #ddd;")
        main_layout.addWidget(sep)

        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 8, 0, 0)
        btn_bar.addStretch()

        save_btn = QPushButton("💾  保存任务")
        save_btn.setFixedSize(130, 42)
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_task)
        btn_bar.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 42)
        cancel_btn.clicked.connect(self.reject)
        btn_bar.addWidget(cancel_btn)

        main_layout.addLayout(btn_bar)

    # ── Tab1: 基本信息 ──
    def _setup_basic_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        # 任务标识
        id_group = QGroupBox("任务标识")
        id_grid = QGridLayout(id_group)
        id_grid.setColumnStretch(1, 1)

        id_grid.addWidget(QLabel("任务名称 *"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：每日销售报表下载")
        id_grid.addWidget(self.name_input, 0, 1)

        id_grid.addWidget(QLabel("任务说明"), 1, 0)
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("可选，描述这个任务的用途")
        id_grid.addWidget(self.desc_input, 1, 1)

        layout.addWidget(id_group)

        # 高级设置
        adv_group = QGroupBox("高级设置")
        adv_grid = QGridLayout(adv_group)
        adv_grid.setColumnStretch(1, 1)

        adv_grid.addWidget(QLabel("最大重试次数"), 0, 0)
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.setSuffix(" 次")
        self.retry_spin.setFixedWidth(100)
        adv_grid.addWidget(self.retry_spin, 0, 1, Qt.AlignmentFlag.AlignLeft)

        adv_grid.addWidget(QLabel("每步超时时间"), 1, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(120)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.setFixedWidth(100)
        adv_grid.addWidget(self.timeout_spin, 1, 1, Qt.AlignmentFlag.AlignLeft)

        adv_grid.addWidget(QLabel("自定义保存目录"), 2, 0)
        save_row = QHBoxLayout()
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setPlaceholderText(
            "留空则使用默认路径：程序目录/下载数据库/YYYY-MM-DD/"
        )
        save_row.addWidget(self.save_dir_input)
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_save_dir)
        save_row.addWidget(browse_btn)
        adv_grid.addLayout(save_row, 2, 1)

        layout.addWidget(adv_group)
        layout.addStretch()

    # ── Tab2: 步骤配置 ──
    def _setup_steps_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # 顶部提示
        hint = QLabel(
            "💡 <b>推荐使用「🎯 可视化拾取」</b>：点击按钮后会弹出真实浏览器，"
            "可直接“开始录制”真实操作，也可进入拾取模式单步捕获。步骤可拖拽排序。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "background:#fef9e7; padding:8px 12px; border-radius:5px; "
            "color:#7d6608; border:1px solid #f9ca24;"
        )
        layout.addWidget(hint)

        # 主体：左侧列表 + 右侧操作
        body = QHBoxLayout()
        body.setSpacing(10)

        # 左侧：步骤列表
        list_group = QGroupBox("步骤列表（从上到下依次执行，可拖拽排序）")
        list_vbox = QVBoxLayout(list_group)

        self.steps_list = QListWidget()
        self.steps_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.steps_list.setAlternatingRowColors(True)
        self.steps_list.setMinimumHeight(280)
        self.steps_list.setSpacing(2)
        self.steps_list.currentRowChanged.connect(self._on_step_selected)
        self.steps_list.itemDoubleClicked.connect(self._edit_selected_step)
        list_vbox.addWidget(self.steps_list)

        # 步骤操作按钮行
        step_op_row = QHBoxLayout()
        self.move_up_btn = QPushButton("⬆ 上移")
        self.move_up_btn.clicked.connect(self._move_step_up)
        step_op_row.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("⬇ 下移")
        self.move_down_btn.clicked.connect(self._move_step_down)
        step_op_row.addWidget(self.move_down_btn)

        self.edit_step_btn = QPushButton("✏️ 编辑")
        self.edit_step_btn.clicked.connect(self._edit_selected_step)
        step_op_row.addWidget(self.edit_step_btn)

        self.del_step_btn = QPushButton("🗑 删除")
        self.del_step_btn.setStyleSheet("color:#c0392b;")
        self.del_step_btn.clicked.connect(self._delete_step)
        step_op_row.addWidget(self.del_step_btn)

        list_vbox.addLayout(step_op_row)
        body.addWidget(list_group, 3)

        # 右侧：添加步骤面板
        add_group = QGroupBox("添加步骤")
        add_vbox = QVBoxLayout(add_group)
        add_vbox.setSpacing(8)

        # 可视化拾取（最醒目）
        visual_btn = QPushButton("🎯  可视化拾取\n（推荐小白使用）")
        visual_btn.setFixedHeight(72)
        visual_btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #8e44ad,stop:1 #3498db);color:white;font-size:13px;"
            "font-weight:bold;border-radius:8px;border:none;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #9b59b6,stop:1 #2980b9);}"
        )
        visual_btn.clicked.connect(self._open_visual_picker)
        add_vbox.addWidget(visual_btn)

        add_vbox.addWidget(self._make_separator("── 或手动添加 ──"))

        manual_steps = [
            ("🌐  打开网址", StepType.OPEN_URL),
            ("⌨️  输入文本", StepType.INPUT),
            ("🖱️  点击元素", StepType.CLICK),
            ("⬇️  点击下载", StepType.DOWNLOAD_CLICK),
            ("📋  下拉选择", StepType.SELECT),
            ("⏱️  等待秒数", StepType.WAIT),
            ("📜  滚动页面", StepType.SCROLL),
            ("🗑️  清空输入框", StepType.CLEAR_INPUT),
        ]
        for label, stype in manual_steps:
            btn = QPushButton(label)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked=False, st=stype: self._add_manual_step(st))
            add_vbox.addWidget(btn)

        add_vbox.addStretch()
        body.addWidget(add_group, 2)

        layout.addLayout(body, 1)

    # ── Tab3: 调度设置 ──
    def _setup_schedule_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        # 启用开关
        enable_group = QGroupBox("定时开关")
        enable_layout = QHBoxLayout(enable_group)
        self.schedule_enabled_check = QCheckBox(
            "启用定时自动执行（关闭则只能手动点击「立即执行」）"
        )
        self.schedule_enabled_check.stateChanged.connect(self._on_schedule_toggle)
        enable_layout.addWidget(self.schedule_enabled_check)
        layout.addWidget(enable_group)

        # 调度类型
        self.schedule_config_group = QGroupBox("执行计划配置")
        sched_layout = QVBoxLayout(self.schedule_config_group)

        # 类型选择
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("执行频率："))
        self.sched_type_combo = QComboBox()
        self.sched_type_combo.addItem("单次执行（到时间执行一次）", "once")
        self.sched_type_combo.addItem("每天执行", "daily")
        self.sched_type_combo.addItem("每周指定星期几执行", "weekly")
        self.sched_type_combo.addItem("每月指定日期执行", "monthly")
        self.sched_type_combo.currentIndexChanged.connect(self._on_sched_type_changed)
        type_row.addWidget(self.sched_type_combo)
        type_row.addStretch()
        sched_layout.addLayout(type_row)

        # 执行时间
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("执行时间："))
        self.run_time_edit = QTimeEdit()
        self.run_time_edit.setDisplayFormat("HH:mm")
        self.run_time_edit.setTime(QTime(9, 0))
        self.run_time_edit.setFixedWidth(100)
        time_row.addWidget(self.run_time_edit)
        time_row.addWidget(QLabel("（24小时制）"))
        time_row.addStretch()
        sched_layout.addLayout(time_row)

        # 星期选择（weekly模式）
        self.weekday_group = QGroupBox("选择星期几（可多选）")
        weekday_layout = QHBoxLayout(self.weekday_group)
        self.weekday_checks = []
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, name in enumerate(weekday_names):
            cb = QCheckBox(name)
            self.weekday_checks.append(cb)
            weekday_layout.addWidget(cb)
        weekday_layout.addStretch()
        sched_layout.addWidget(self.weekday_group)

        # 月份日期选择（monthly模式）
        self.monthday_group = QGroupBox("选择每月几号（可多选）")
        monthday_layout = QGridLayout(self.monthday_group)
        self.monthday_checks = []
        for i in range(1, 32):
            cb = QCheckBox(str(i))
            self.monthday_checks.append(cb)
            row = (i - 1) // 10
            col = (i - 1) % 10
            monthday_layout.addWidget(cb, row, col)
        sched_layout.addWidget(self.monthday_group)

        layout.addWidget(self.schedule_config_group)

        # 下次执行预览
        preview_group = QGroupBox("📅 计划说明")
        preview_layout = QVBoxLayout(preview_group)
        self.schedule_preview_label = QLabel("请配置上方的执行计划")
        self.schedule_preview_label.setStyleSheet(
            "color:#2980b9; font-size:13px; font-weight:bold;"
        )
        self.schedule_preview_label.setWordWrap(True)
        preview_layout.addWidget(self.schedule_preview_label)
        layout.addWidget(preview_group)

        layout.addStretch()

        # 初始化显示状态
        self._on_schedule_toggle()
        self._on_sched_type_changed()

    # ─────────────────────────────────────────────
    # 数据加载
    # ─────────────────────────────────────────────
    def _load_task_data(self):
        """将task对象的数据填充到界面"""
        # 基本信息
        self.name_input.setText(self.task.name)
        self.desc_input.setText(self.task.description)
        self.retry_spin.setValue(self.task.max_retries)
        self.timeout_spin.setValue(self.task.timeout_per_step)
        self.save_dir_input.setText(self.task.save_dir_override)

        # 步骤列表
        self.steps_list.clear()
        for step in self.task.steps:
            item = StepListItem(step)
            self.steps_list.addItem(item)

        # 调度配置
        sch = self.task.schedule
        self.schedule_enabled_check.setChecked(sch.enabled)

        for i in range(self.sched_type_combo.count()):
            if self.sched_type_combo.itemData(i) == sch.schedule_type:
                self.sched_type_combo.setCurrentIndex(i)
                break

        try:
            h, m = map(int, sch.run_time.split(":"))
            self.run_time_edit.setTime(QTime(h, m))
        except Exception:
            self.run_time_edit.setTime(QTime(9, 0))

        for i, cb in enumerate(self.weekday_checks):
            cb.setChecked(i in sch.weekdays)

        for i, cb in enumerate(self.monthday_checks):
            cb.setChecked((i + 1) in sch.monthdays)

        self._on_schedule_toggle()
        self._on_sched_type_changed()

    # ─────────────────────────────────────────────
    # 步骤管理
    # ─────────────────────────────────────────────
    def _open_visual_picker(self):
        """打开可视化拾取窗口"""
        # 获取第一个打开URL步骤的URL作为初始URL
        initial_url = ""
        for step in self._get_current_steps():
            if step.step_type == StepType.OPEN_URL:
                initial_url = step.value
                break

        if self._picker_window and not self._picker_window.isHidden():
            self._picker_window.raise_()
            self._picker_window.activateWindow()
            return

        self._picker_window = VisualPickerWindow(self, initial_url=initial_url)
        self._picker_window.step_configured.connect(self._on_step_from_picker)
        self._picker_window.show()

    def _on_step_from_picker(self, step: Step):
        """接收来自可视化拾取窗口的步骤"""
        item = StepListItem(step)
        self.steps_list.addItem(item)
        self.steps_list.setCurrentItem(item)
        self.steps_list.scrollToBottom()

    def _add_manual_step(self, step_type: StepType):
        """手动添加指定类型的步骤"""
        step = Step(step_type=step_type)
        dlg = ManualStepDialog(step, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item = StepListItem(dlg.get_step())
            self.steps_list.addItem(item)
            self.steps_list.setCurrentItem(item)
            self.steps_list.scrollToBottom()

    def _edit_selected_step(self):
        """编辑当前选中的步骤"""
        item = self.steps_list.currentItem()
        if not item or not isinstance(item, StepListItem):
            return
        import copy
        step_copy = copy.deepcopy(item.step)
        dlg = ManualStepDialog(step_copy, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            item.step = dlg.get_step()
            item.refresh_text()

    def _delete_step(self):
        """删除当前选中的步骤"""
        row = self.steps_list.currentRow()
        if row < 0:
            return
        item = self.steps_list.item(row)
        if not item:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除步骤「{item.text()}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.steps_list.takeItem(row)

    def _move_step_up(self):
        """将选中步骤上移一位"""
        row = self.steps_list.currentRow()
        if row <= 0:
            return
        item = self.steps_list.takeItem(row)
        self.steps_list.insertItem(row - 1, item)
        self.steps_list.setCurrentRow(row - 1)

    def _move_step_down(self):
        """将选中步骤下移一位"""
        row = self.steps_list.currentRow()
        if row < 0 or row >= self.steps_list.count() - 1:
            return
        item = self.steps_list.takeItem(row)
        self.steps_list.insertItem(row + 1, item)
        self.steps_list.setCurrentRow(row + 1)

    def _on_step_selected(self, row: int):
        """步骤选中状态变化"""
        has_selection = row >= 0
        self.move_up_btn.setEnabled(has_selection and row > 0)
        self.move_down_btn.setEnabled(
            has_selection and row < self.steps_list.count() - 1
        )
        self.edit_step_btn.setEnabled(has_selection)
        self.del_step_btn.setEnabled(has_selection)

    def _get_current_steps(self):
        """从列表控件中提取当前所有步骤"""
        steps = []
        for i in range(self.steps_list.count()):
            item = self.steps_list.item(i)
            if isinstance(item, StepListItem):
                steps.append(item.step)
        return steps

    # ─────────────────────────────────────────────
    # 调度配置
    # ─────────────────────────────────────────────
    def _on_schedule_toggle(self):
        """启用/禁用调度配置区域"""
        enabled = self.schedule_enabled_check.isChecked()
        self.schedule_config_group.setEnabled(enabled)
        if enabled:
            self._update_schedule_preview()
        else:
            self.schedule_preview_label.setText("定时计划已关闭，只能手动触发执行")

    def _on_sched_type_changed(self):
        """调度类型变化时显示/隐藏对应控件"""
        stype = self.sched_type_combo.currentData()
        self.weekday_group.setVisible(stype == "weekly")
        self.monthday_group.setVisible(stype == "monthly")
        self._update_schedule_preview()

    def _update_schedule_preview(self):
        """更新调度计划预览文字"""
        if not self.schedule_enabled_check.isChecked():
            return
        stype = self.sched_type_combo.currentData()
        t = self.run_time_edit.time().toString("HH:mm")

        if stype == "once":
            self.schedule_preview_label.setText(f"📅 将在今天（或明天）{t} 执行一次")
        elif stype == "daily":
            self.schedule_preview_label.setText(f"📅 每天 {t} 自动执行")
        elif stype == "weekly":
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            selected = [weekday_names[i] for i, cb in enumerate(self.weekday_checks) if cb.isChecked()]
            days_str = "、".join(selected) if selected else "（请选择星期几）"
            self.schedule_preview_label.setText(f"📅 每周 {days_str} {t} 自动执行")
        elif stype == "monthly":
            selected = [str(i + 1) for i, cb in enumerate(self.monthday_checks) if cb.isChecked()]
            days_str = "、".join(selected) + "号" if selected else "（请选择日期）"
            self.schedule_preview_label.setText(f"📅 每月 {days_str} {t} 自动执行")

    # ─────────────────────────────────────────────
    # 其他操作
    # ─────────────────────────────────────────────
    def _browse_save_dir(self):
        """浏览选择保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择文件保存目录", "",
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.save_dir_input.setText(directory)

    def _make_separator(self, text: str) -> QLabel:
        """创建带文字的分隔线标签"""
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color:#999; font-size:11px; margin:4px 0;")
        return label

    # ─────────────────────────────────────────────
    # 保存
    # ─────────────────────────────────────────────
    def _save_task(self):
        """验证并保存任务"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "任务名称不能为空！")
            return

        steps = self._get_current_steps()
        if not steps:
            reply = QMessageBox.question(
                self, "提示",
                "当前任务没有配置任何步骤，确定要保存吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 写回task对象
        self.task.name = name
        self.task.description = self.desc_input.text().strip()
        self.task.steps = steps
        self.task.max_retries = self.retry_spin.value()
        self.task.timeout_per_step = self.timeout_spin.value()
        self.task.save_dir_override = self.save_dir_input.text().strip()

        # 调度配置
        sch = self.task.schedule
        sch.enabled = self.schedule_enabled_check.isChecked()
        sch.schedule_type = self.sched_type_combo.currentData()
        sch.run_time = self.run_time_edit.time().toString("HH:mm")
        sch.weekdays = [i for i, cb in enumerate(self.weekday_checks) if cb.isChecked()]
        sch.monthdays = [i + 1 for i, cb in enumerate(self.monthday_checks) if cb.isChecked()]

        self.accept()

    def get_task(self) -> Task:
        return self.task

    # ─────────────────────────────────────────────
    # 样式
    # ─────────────────────────────────────────────
    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background: #f0f2f5; }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 18px;
                font-size: 13px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background: #e8e8e8;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
                color: #2980b9;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px 8px 8px 8px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #34495e;
            }
            QLineEdit, QSpinBox, QComboBox, QTimeEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 8px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QPushButton {
                border: 1px solid #bbb;
                border-radius: 4px;
                padding: 5px 12px;
                background: #ecf0f1;
                font-size: 12px;
            }
            QPushButton:hover { background: #d5dbdb; }
            QPushButton#primaryBtn {
                background: #2980b9;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton#primaryBtn:hover { background: #3498db; }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                font-size: 12px;
            }
            QListWidget::item { padding: 6px 8px; }
            QListWidget::item:selected {
                background: #d6eaf8;
                color: #1a5276;
            }
            QListWidget::item:alternate { background: #f8f9fa; }
        """)