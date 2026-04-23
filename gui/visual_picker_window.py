"""
可视化元素拾取窗口（侧边栏模式）
"""
import time
from typing import Optional

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QWidget, QFrame, QScrollArea, QApplication,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QPoint
from PySide6.QtGui import QFont, QCursor

from models.step import Step, StepType, STEP_TYPE_LABELS

PICKER_JS = """
(function() {
    if (window.__webAutoPickerInjected) return;
    window.__webAutoPickerInjected = true;
    window.__webAutoPickerActive = false;
    window.__webAutoRecorderActive = false;
    window.__lastPickedElement = null;
    window.__webAutoRecorderEvents = [];
    window.__pickerExitRequested = false;

    function generateSelector(el) {
        if (!el || el === document.body) return 'body';
        if (el.id && el.id.trim()) {
            return '#' + CSS.escape(el.id.trim());
        }
        var attrs = ['name', 'data-testid', 'data-id', 'aria-label', 'placeholder', 'type'];
        for (var i = 0; i < attrs.length; i++) {
            var val = el.getAttribute(attrs[i]);
            if (val && val.trim()) {
                var sel = el.tagName.toLowerCase() + '[' + attrs[i] + '="' + val.trim() + '"]';
                if (document.querySelectorAll(sel).length === 1) return sel;
            }
        }
        if (el.className && typeof el.className === 'string') {
            var classes = el.className.trim().split(/\s+/).filter(c => c && !c.includes(':'));
            if (classes.length > 0) {
                var classSel = el.tagName.toLowerCase() + '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                if (document.querySelectorAll(classSel).length === 1) return classSel;
            }
        }
        var parent = el.parentElement;
        if (!parent) return el.tagName.toLowerCase();
        var siblings = Array.from(parent.children);
        var index = siblings.indexOf(el) + 1;
        return generateSelector(parent) + ' > ' + el.tagName.toLowerCase() + ':nth-child(' + index + ')';
    }

    function getElementDescription(el) {
        var tag = el.tagName.toLowerCase();
        var text = (el.innerText || el.value || el.placeholder || el.alt || '').trim().substring(0, 30);
        var type = el.getAttribute('type') || '';
        return tag + (type ? '[' + type + ']' : '') + (text ? ' "' + text + '"' : '');
    }

    window.__webAutoRecorderReset = function() { window.__webAutoRecorderEvents = []; };
    window.__webAutoRecorderGetEvents = function() {
        var events = window.__webAutoRecorderEvents.slice();
        window.__webAutoRecorderEvents = [];
        return events;
    };

    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;pointer-events:none;background:rgba(0,120,255,0.25);border:2px solid #0078ff;border-radius:3px;z-index:999999;display:none;box-sizing:border-box;';
    document.body.appendChild(overlay);

    var tooltip = document.createElement('div');
    tooltip.style.cssText = 'position:fixed;background:#1a1a2e;color:#00d4ff;padding:6px 10px;border-radius:4px;font-size:12px;font-family:monospace;z-index:9999999;pointer-events:none;max-width:400px;word-break:break-all;display:none;border:1px solid #00d4ff;';
    document.body.appendChild(tooltip);

    var banner = document.createElement('div');
    banner.id = '__webAutoBanner';
    banner.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:linear-gradient(135deg,#667eea,#764ba2);color:white;text-align:center;padding:6px;font-size:13px;font-weight:bold;z-index:9999999;font-family:Microsoft YaHei,sans-serif;box-shadow:0 -2px 10px rgba(0,0,0,0.3);opacity:0.92;';
    banner.innerHTML = '🎯 拾取/录制模式 | 左键单击捕获元素 | 右键退出';
    document.body.appendChild(banner);

    document.addEventListener('mousemove', function(e) {
        var el = e.target;
        if (el === overlay || el === tooltip || el === banner || banner.contains(el)) return;
        var rect = el.getBoundingClientRect();
        overlay.style.cssText += ';display:block;left:' + rect.left + 'px;top:' + rect.top + 'px;width:' + rect.width + 'px;height:' + rect.height + 'px;';
        var selector = generateSelector(el);
        var desc = getElementDescription(el);
        tooltip.style.display = 'block';
        tooltip.style.left = Math.min(e.clientX + 10, window.innerWidth - 420) + 'px';
        tooltip.style.top = Math.min(e.clientY + 10, window.innerHeight - 60) + 'px';
        tooltip.innerHTML = '<b>元素:</b>' + desc + '<br><b>选择器:</b>' + selector;
        window.__currentSelector = selector;
        window.__currentDescription = desc;
    }, true);

    document.addEventListener('click', function(e) {
        var el = e.target;
        if (el === banner || banner.contains(el)) return;

        if (window.__webAutoPickerActive) {
            e.preventDefault();
            e.stopPropagation();
            var selector = generateSelector(el);
            var desc = getElementDescription(el);
            window.__lastPickedElement = {
                selector: selector, description: desc,
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type') || '',
                text: (el.innerText || '').trim().substring(0, 50),
                value: el.value || '',
                href: el.href || '',
                name: el.getAttribute('name') || '',
                id: el.id || ''
            };
            overlay.style.background = 'rgba(0,200,100,0.3)';
            overlay.style.border = '3px solid #00c864';
            setTimeout(function() {
                overlay.style.background = 'rgba(0,120,255,0.25)';
                overlay.style.border = '2px solid #0078ff';
            }, 500);
            return;
        }

        if (window.__webAutoRecorderActive) {
            var selector = generateSelector(el);
            var desc = getElementDescription(el);
            window.__webAutoRecorderEvents.push({
                type: 'click', selector: selector, description: desc,
                tag: el.tagName.toLowerCase(),
                inputType: el.getAttribute('type') || '',
                value: el.value || '', href: el.href || '',
                name: el.getAttribute('name') || '', id: el.id || '',
                timestamp: Date.now()
            });
        }
    }, true);

    document.addEventListener('change', function(e) {
        if (!window.__webAutoRecorderActive) return;
        var el = e.target;
        var tag = el.tagName.toLowerCase();
        if (tag !== 'input' && tag !== 'textarea' && tag !== 'select') return;
        var selector = generateSelector(el);
        var desc = getElementDescription(el);
        var value = '', optionText = '', optionValue = '';
        if (tag === 'select') {
            var option = el.options[el.selectedIndex];
            value = option ? option.value : '';
            optionText = option ? (option.text || '') : '';
            optionValue = value;
        } else {
            value = el.value || '';
        }
        window.__webAutoRecorderEvents.push({
            type: tag === 'select' ? 'select' : 'input',
            selector: selector, description: desc, tag: tag,
            value: value, optionText: optionText, optionValue: optionValue,
            name: el.getAttribute('name') || '', id: el.id || '',
            timestamp: Date.now()
        });
    }, true);

    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        window.__webAutoPickerActive = false;
        window.__webAutoRecorderActive = false;
        window.__pickerExitRequested = true;
        overlay.remove(); tooltip.remove(); banner.remove();
    }, true);
})();
"""

# 顶部黄色警告横幅：浏览器就绪后立即注入，提醒用户去控制台开启录制/拾取。
# 用户进入任一模式后自动隐藏；用户也可点 × 主动关闭。
WARN_BANNER_JS = """
(function() {
    if (window.__webAutoWarnInjected) return;
    window.__webAutoWarnInjected = true;
    window.__webAutoWarnDismissed = false;

    var warn = document.createElement('div');
    warn.id = '__webAutoWarn';
    warn.style.cssText = 'position:fixed;top:0;left:0;right:0;' +
        'background:linear-gradient(135deg,#f39c12,#e67e22);color:white;' +
        'text-align:center;padding:14px 50px 14px 16px;font-size:15px;' +
        'font-weight:bold;z-index:9999998;font-family:Microsoft YaHei,sans-serif;' +
        'box-shadow:0 2px 12px rgba(0,0,0,0.35);';
    warn.innerHTML = '\u26A0\uFE0F \u5F55\u5236\u672A\u5F00\u542F \u2014 ' +
        '\u8BF7\u5230\u53F3\u4FA7\u201C\uD83C\uDFAF \u62FE\u53D6\u63A7\u5236\u53F0\u201D\u70B9\u51FB' +
        '\u300C\uD83C\uDFAC \u5F00\u59CB\u5F55\u5236\u300D\u6216\u300C\uD83C\uDFAF \u8FDB\u5165\u62FE\u53D6\u300D' +
        '<span id="__webAutoWarnClose" style="position:absolute;right:14px;top:50%;' +
        'transform:translateY(-50%);cursor:pointer;background:rgba(0,0,0,0.25);' +
        'border-radius:50%;width:26px;height:26px;display:inline-flex;' +
        'align-items:center;justify-content:center;font-size:18px;line-height:1;">\u00D7</span>';
    document.body.appendChild(warn);

    document.getElementById('__webAutoWarnClose').onclick = function(e){
        e.stopPropagation();
        warn.style.display = 'none';
        window.__webAutoWarnDismissed = true;
    };

    setInterval(function(){
        if (window.__webAutoWarnDismissed) return;
        var active = window.__webAutoPickerActive || window.__webAutoRecorderActive;
        warn.style.display = active ? 'none' : '';
    }, 300);
})();
"""

class PickerThread(QThread):
    element_picked = Signal(dict)
    action_recorded = Signal(dict)
    picker_exited = Signal()
    browser_ready = Signal()

    def __init__(self, url: str = "about:blank"):
        super().__init__()
        self.url = url
        self._page = None
        self._stop = False
        self._last_picked = None
        self._recorder_should_be_active = False  # 跨页跳转时自动恢复录制状态

    def run(self):
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
            from core.engine import get_chromium_path
            options = ChromiumOptions()
            options.headless(False)
            options.set_argument('--window-size=1280,800')
            options.set_argument('--window-position=100,100')
            # 隐藏自动化特征
            options.set_argument('--disable-blink-features=AutomationControlled')
            options.set_argument('--exclude-switches=enable-automation')
            options.set_argument('--disable-infobars')
            import platform as _plt
            if _plt.system() != 'Windows':
                options.set_argument('--no-sandbox')
                options.set_argument('--disable-dev-shm-usage')
            from core.engine import CHROME_NOT_FOUND_MSG
            chromium_path = get_chromium_path()
            if not chromium_path:
                raise RuntimeError(CHROME_NOT_FOUND_MSG)
            options.set_browser_path(chromium_path)
            self._page = ChromiumPage(options)
            _stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
                const _pq = navigator.permissions.query.bind(navigator.permissions);
                navigator.permissions.query = p =>
                    p.name === 'notifications'
                    ? Promise.resolve({state: Notification.permission})
                    : _pq(p);
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh','en']});
            """
            try:
                self._page.run_cdp('Page.addScriptToEvaluateOnNewDocument',
                                   source=_stealth_js)
            except Exception:
                pass
            if self.url and self.url != "about:blank":
                self._page.get(self.url)
                time.sleep(2)
            self.browser_ready.emit()

            while not self._stop:
                try:
                    exit_req = self._page.run_js("return window.__pickerExitRequested || false;")
                    if exit_req:
                        self.picker_exited.emit()
                        break

                    # 检测页面跳转后脚本丢失，自动重新注入并恢复录制状态
                    injected = self._page.run_js(
                        "return window.__webAutoPickerInjected || false;"
                    )
                    if not injected:
                        self._page.run_js(PICKER_JS)
                        if self._recorder_should_be_active:
                            self._page.run_js(
                                "window.__webAutoRecorderActive = true;"
                                "window.__webAutoPickerActive = false;"
                                "window.__pickerExitRequested = false;"
                            )

                    # 警告横幅：跨页跳转后同样自动重注（用户主动 × 关闭过的不再显示）
                    warn_injected = self._page.run_js(
                        "return window.__webAutoWarnInjected || false;"
                    )
                    if not warn_injected:
                        self._page.run_js(WARN_BANNER_JS)

                    picked = self._page.run_js(
                        "var r = window.__lastPickedElement; window.__lastPickedElement = null; return r;"
                    )
                    if picked and isinstance(picked, dict) and picked != self._last_picked:
                        self._last_picked = picked
                        self.element_picked.emit(picked)

                    recorded = self._page.run_js(
                        "return (window.__webAutoRecorderGetEvents ? window.__webAutoRecorderGetEvents() : []);"
                    )
                    if recorded and isinstance(recorded, list):
                        for action in recorded:
                            if isinstance(action, dict):
                                self.action_recorded.emit(action)
                except Exception:
                    self.picker_exited.emit()
                    break
                time.sleep(0.3)
        except Exception as e:
            print(f"[PickerThread] error: {e}")
            self.picker_exited.emit()
        finally:
            self._cleanup()

    def navigate_to(self, url: str):
        if self._page:
            try:
                self._page.get(url)
                time.sleep(2)
                self._page.run_js(PICKER_JS)
            except Exception as e:
                print(f"[PickerThread] navigate error: {e}")

    def reinject_script(self):
        if self._page:
            try:
                self._page.run_js("window.__webAutoPickerInjected = false;")
                self._page.run_js(PICKER_JS)
            except Exception:
                pass

    def run_js(self, js: str):
        if self._page:
            return self._page.run_js(js)

    def stop(self):
        self._stop = True

    def _cleanup(self):
        try:
            if self._page:
                self._page.quit()
                self._page = None
        except Exception:
            pass

_PANEL_W = 260  # 侧边栏固定宽度


class VisualPickerWindow(QWidget):
    """拾取/录制侧边栏，固定 260px 宽，始终置顶，自动停靠屏幕右侧。

    全局唯一：同一时刻只允许一个 picker 存在（单次只支持配置一个任务）。
    通过 `current_instance()` 类方法访问当前活跃实例。
    """

    step_configured = Signal(object)
    # v1.2.0: 登录模板录制完毕（list[LoginAction]）
    login_recorded = Signal(object)
    # v1.2.0: 单次拾取（用于 skip_check 选择器）
    single_element_picked = Signal(object)

    _active_instance: "Optional[VisualPickerWindow]" = None

    @classmethod
    def current_instance(cls) -> "Optional[VisualPickerWindow]":
        """返回当前活跃 picker（已 show 且未 close）；无则返回 None。"""
        try:
            inst = cls._active_instance
            if inst is None:
                return None
            # isVisible 检查应对窗口被销毁但引用尚存的情况
            if not inst.isVisible():
                return None
            return inst
        except RuntimeError:
            # 底层 C++ 对象已被销毁
            cls._active_instance = None
            return None

    def __init__(self, parent=None, initial_url: str = "", mode: str = "normal"):
        """mode:
        - "normal"   : 默认，可拾取/录制操作步骤
        - "login"    : 登录模板录制；保存时 emit login_recorded(list[LoginAction])
        - "pick_one" : 单次拾取一个元素（用于 skip_check）；
                       首次 element_picked 后立即 emit single_element_picked + 关闭
        """
        super().__init__(
            parent,
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint,
        )
        title_map = {
            "normal":   "🎯 拾取控制台",
            "login":    "🔐 登录录制控制台",
            "pick_one": "🎯 拾取已登录标志元素",
        }
        self.setWindowTitle(title_map.get(mode, "🎯 拾取控制台"))
        self.setFixedWidth(_PANEL_W)

        self._mode = mode
        self._picker_thread: Optional[PickerThread] = None
        self._initial_url = initial_url
        self._pick_mode = False
        self._record_mode = False
        self._recorded_actions = []

        # 注册为全局唯一实例
        VisualPickerWindow._active_instance = self

        self._setup_ui()
        self._apply_styles()

    def show(self):
        """首次显示时自动定位到屏幕右侧边缘。"""
        super().show()
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - _PANEL_W - 8
        y = screen.top() + 80
        self.move(x, y)

    # ── UI构建 ──────────────────────────────────────
    def _sep(self) -> QFrame:
        """水平细分隔线。"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #e0e0e0;")
        return line

    def _section_label(self, text: str) -> QLabel:
        """小节标题标签。"""
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size:10px; font-weight:bold; color:#7f8c8d; letter-spacing:0.5px;"
        )
        return lbl

    def _setup_ui(self):
        # 可滚动的根容器，防止小屏高度不够时内容被截断
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # ── URL 区 ──────────────────────────────────
        layout.addWidget(self._section_label("目标网址"))
        url_row = QHBoxLayout()
        url_row.setSpacing(4)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        self.url_input.setText(self._initial_url)
        url_row.addWidget(self.url_input, 1)
        self.open_btn = QPushButton("打开")
        self.open_btn.setFixedWidth(46)
        self.open_btn.clicked.connect(self._start_picker)
        url_row.addWidget(self.open_btn)
        layout.addLayout(url_row)

        layout.addWidget(self._sep())

        # ── 模式按钮 ────────────────────────────────
        layout.addWidget(self._section_label("操作模式"))
        mode_row = QHBoxLayout()
        mode_row.setSpacing(4)
        self.pick_mode_btn = QPushButton("🔍 拾取")
        self.pick_mode_btn.setEnabled(False)
        self.pick_mode_btn.clicked.connect(self._toggle_pick_mode)
        mode_row.addWidget(self.pick_mode_btn, 1)
        self.record_btn = QPushButton("🎬 录制")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self._toggle_record_mode)
        mode_row.addWidget(self.record_btn, 1)
        layout.addLayout(mode_row)

        self.reinject_btn = QPushButton("🔄 重新激活脚本")
        self.reinject_btn.setEnabled(False)
        self.reinject_btn.setFixedHeight(24)
        self.reinject_btn.clicked.connect(self._reinject_and_reset)
        layout.addWidget(self.reinject_btn)

        layout.addWidget(self._sep())

        # ── 状态行 ──────────────────────────────────
        self.desc_label = QLabel("等待浏览器启动…")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color:#7f8c8d; font-size:11px; font-style:italic;")
        layout.addWidget(self.desc_label)

        layout.addWidget(self._sep())

        # ── 拾取结果区 ──────────────────────────────
        layout.addWidget(self._section_label("拾取结果"))

        layout.addWidget(QLabel("CSS 选择器"))
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("点击元素后自动填入")
        self.selector_input.setFont(QFont("Consolas", 9))
        layout.addWidget(self.selector_input)

        layout.addWidget(QLabel("步骤名称"))
        self.step_name_input = QLineEdit()
        self.step_name_input.setPlaceholderText("可选")
        layout.addWidget(self.step_name_input)

        layout.addWidget(QLabel("步骤类型"))
        self.step_type_combo = QComboBox()
        # 排除：OPEN_URL（不需要从浏览器拾取）
        # v1.3.0：UPLOAD_FILE / READ_EXCEL / APPEND_EXCEL 不从浏览器拾取，
        # 只在编辑器手动配置；EXTRACT_DOM 可以拾取（用 value_input 当变量名输入）
        _picker_excluded = {
            StepType.OPEN_URL, StepType.UPLOAD_FILE,
            StepType.READ_EXCEL, StepType.APPEND_EXCEL,
        }
        for step_type, label in STEP_TYPE_LABELS.items():
            if step_type not in _picker_excluded:
                self.step_type_combo.addItem(label, step_type)
        self.step_type_combo.currentIndexChanged.connect(self._on_step_type_changed)
        layout.addWidget(self.step_type_combo)

        self.value_label = QLabel("输入内容")
        layout.addWidget(self.value_label)
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("[TODAY] [TODAY-1] [MONTH_START]…")
        layout.addWidget(self.value_input)

        self.var_hint = QLabel("💡 [TODAY] [TODAY-1] [MONTH_START] [MONTH_END]")
        self.var_hint.setWordWrap(True)
        self.var_hint.setStyleSheet("color:#95a5a6; font-size:10px;")
        layout.addWidget(self.var_hint)

        add_single_btn = QPushButton("✅ 添加此步骤")
        add_single_btn.setObjectName("addBtn")
        add_single_btn.clicked.connect(self._add_step)
        layout.addWidget(add_single_btn)

        layout.addWidget(self._sep())

        # ── 录制结果区 ──────────────────────────────
        rec_header = QHBoxLayout()
        rec_header.addWidget(self._section_label("录制结果"))
        rec_header.addStretch()
        self.rec_count_label = QLabel("0 步")
        self.rec_count_label.setStyleSheet("font-size:10px; color:#7f8c8d;")
        rec_header.addWidget(self.rec_count_label)
        layout.addLayout(rec_header)

        self.record_list = QListWidget()
        self.record_list.setAlternatingRowColors(True)
        self.record_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.record_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.record_list.itemSelectionChanged.connect(self._update_record_selection_buttons)
        self.record_list.setMinimumHeight(80)
        self.record_list.setMaximumHeight(200)
        self.record_list.setStyleSheet("font-size:11px;")
        layout.addWidget(self.record_list)

        rec_btns = QHBoxLayout()
        rec_btns.setSpacing(4)
        # 登录模式按钮文案与行为不同
        self.add_recorded_btn = QPushButton(
            "💾 保存为登录模板" if self._mode == "login" else "✅ 全部添加"
        )
        self.add_recorded_btn.setEnabled(False)
        self.add_recorded_btn.setObjectName("addBtn")
        self.add_recorded_btn.clicked.connect(self._add_recorded_steps)
        rec_btns.addWidget(self.add_recorded_btn, 1)
        self.remove_selected_btn = QPushButton("🗑")
        self.remove_selected_btn.setEnabled(False)
        self.remove_selected_btn.setFixedWidth(32)
        self.remove_selected_btn.setToolTip("删除选中")
        self.remove_selected_btn.clicked.connect(self._remove_selected_recorded_actions)
        rec_btns.addWidget(self.remove_selected_btn)
        clear_btn = QPushButton("清空")
        clear_btn.setFixedWidth(40)
        clear_btn.clicked.connect(self._clear_recorded_actions)
        rec_btns.addWidget(clear_btn)
        layout.addLayout(rec_btns)

        # v1.2.0: 登录模式专用 — 占位符插入按钮
        if self._mode == "login":
            ph_label = QLabel("把选中的输入步骤替换为占位符（密码不录入明文）：")
            ph_label.setWordWrap(True)
            ph_label.setStyleSheet(
                "color:#7d6608; font-size:11px; padding:6px 4px; "
                "background:#fef9e7; border-radius:3px;"
            )
            layout.addWidget(ph_label)

            ph_row = QHBoxLayout()
            ph_row.setSpacing(4)
            self.insert_user_btn = QPushButton("🔑 替换为 ${username}")
            self.insert_user_btn.setEnabled(False)
            self.insert_user_btn.clicked.connect(
                lambda: self._replace_selected_input_value("${username}")
            )
            ph_row.addWidget(self.insert_user_btn, 1)
            self.insert_pwd_btn = QPushButton("🔒 替换为 ${password}")
            self.insert_pwd_btn.setEnabled(False)
            self.insert_pwd_btn.clicked.connect(
                lambda: self._replace_selected_input_value("${password}")
            )
            ph_row.addWidget(self.insert_pwd_btn, 1)
            layout.addLayout(ph_row)
            self.record_list.itemSelectionChanged.connect(
                self._update_placeholder_btn_state
            )

        layout.addWidget(self._sep())

        # ── 底部关闭 ────────────────────────────────
        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(30)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        layout.addStretch()
        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self._on_step_type_changed()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget { background: #f8f9fa; font-size: 12px; }
            QScrollArea { background: #f8f9fa; }
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px 6px;
                background: white;
            }
            QLineEdit:focus { border-color: #3498db; }
            QPushButton {
                border: 1px solid #c8c8c8;
                border-radius: 4px;
                padding: 4px 8px;
                background: #ecf0f1;
                font-size: 12px;
            }
            QPushButton:hover { background: #dde4e6; }
            QPushButton:disabled { color: #b0b0b0; background: #f0f0f0; border-color: #ddd; }
            QPushButton#addBtn {
                background: #27ae60; color: white;
                font-weight: bold; border: none;
            }
            QPushButton#addBtn:hover { background: #2ecc71; }
            QPushButton#addBtn:disabled { background: #95a5a6; }
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 3px 6px;
                background: white;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item { padding: 3px 6px; }
            QListWidget::item:selected { background: #d6eaf8; color: #1a5276; }
        """)

    # ── 浏览器控制 ──────────────────────────────────
    def _start_picker(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请先输入目标网页地址！")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_input.setText(url)

        if self._picker_thread and self._picker_thread.isRunning():
            # 已有浏览器，导航到新地址
            self.open_btn.setEnabled(False)
            self.open_btn.setText("⏳ 导航中...")
            try:
                self._picker_thread.navigate_to(url)
                self._set_status("✅ 已导航到新地址，登录状态已保留", "#27ae60")
            except Exception as e:
                QMessageBox.warning(self, "导航失败", str(e))
            finally:
                self.open_btn.setText("🔄 重新导航")
                self.open_btn.setEnabled(True)
            return

        # 启动新浏览器
        self._picker_thread = PickerThread(url)
        self._picker_thread.element_picked.connect(self._on_element_picked)
        self._picker_thread.action_recorded.connect(self._on_recorded_action)
        self._picker_thread.picker_exited.connect(self._on_picker_exited)
        self._picker_thread.browser_ready.connect(self._on_browser_ready)
        self._picker_thread.start()

        self.open_btn.setText("⏳ 浏览器启动中...")
        self.open_btn.setEnabled(False)
        self._set_status("正在启动浏览器，请稍候...", "#e67e22")

    def _on_browser_ready(self):
        self.open_btn.setText("🔄 重新导航")
        self.open_btn.setEnabled(True)
        self.pick_mode_btn.setEnabled(True)
        self.record_btn.setEnabled(True)
        self.reinject_btn.setEnabled(True)
        self._pick_mode = False
        self._record_mode = False
        self._reset_mode_buttons()

        # v1.2.0 模式分支
        if self._mode == "pick_one":
            self._toggle_pick_mode()
            self._set_status(
                "🎯 浏览器已就绪，请在页面中点击一个【已登录后才出现】的元素",
                "#2980b9"
            )
            return
        if self._mode == "login":
            self._toggle_record_mode()
            self._set_status(
                "🔴 已自动进入登录录制模式：请走一遍真实登录流程，"
                "密码填好后选中该步并点「替换为 ${password}」",
                "#d35400"
            )
            return

        self._set_status(
            "✅ 浏览器已就绪！可先登录/浏览，然后点击「进入拾取模式」或「开始录制」",
            "#27ae60"
        )

    def _reinject_and_reset(self):
        if self._picker_thread and self._picker_thread.isRunning():
            self._picker_thread.reinject_script()
            self._pick_mode = False
            self._record_mode = False
            self._reset_mode_buttons()
            self._set_status("✅ 脚本已重新注入，可重新进入拾取或录制模式", "#27ae60")

    def _toggle_pick_mode(self):
        if not (self._picker_thread and self._picker_thread.isRunning()):
            return
        if self._record_mode:
            self._toggle_record_mode()

        if not self._pick_mode:
            try:
                self._picker_thread.run_js(
                    "window.__webAutoPickerActive = true;"
                    "window.__webAutoRecorderActive = false;"
                    "window.__pickerExitRequested = false;"
                )
            except Exception:
                pass
            self._pick_mode = True
            self.pick_mode_btn.setText("⏹ 退出拾取模式")
            self.pick_mode_btn.setStyleSheet(
                "QPushButton{background:#27ae60;color:white;border-radius:4px;"
                "font-weight:bold;border:none;}"
            )
            self._set_status("✅ 已进入拾取模式，请在浏览器中点击目标元素", "#27ae60")
        else:
            try:
                self._picker_thread.run_js(
                    "window.__webAutoPickerActive = false;"
                )
            except Exception:
                pass
            self._pick_mode = False
            self.pick_mode_btn.setText("🔍 进入拾取模式")
            self.pick_mode_btn.setStyleSheet("")
            self._set_status("已退出拾取模式", "#3498db")

    def _toggle_record_mode(self):
        if not (self._picker_thread and self._picker_thread.isRunning()):
            return
        if self._pick_mode:
            self._toggle_pick_mode()

        if not self._record_mode:
            self._record_mode = True
            self._recorded_actions = []
            self.record_list.clear()
            self.add_recorded_btn.setEnabled(False)
            self.record_btn.setText("⏹ 停止录制")
            self.record_btn.setStyleSheet(
                "QPushButton{background:#d35400;color:white;border-radius:4px;"
                "font-weight:bold;border:none;}"
            )
            try:
                self._picker_thread.run_js(
                    "window.__webAutoRecorderActive = true;"
                    "window.__webAutoPickerActive = false;"
                    "window.__pickerExitRequested = false;"
                    "window.__webAutoRecorderReset && window.__webAutoRecorderReset();"
                )
            except Exception:
                pass
            self._picker_thread._recorder_should_be_active = True
            self._set_status(
                "🔴 录制中，您的浏览操作将自动转为步骤，完成后点击停止录制",
                "#d35400"
            )
        else:
            self._record_mode = False
            self.record_btn.setText("🎬 开始录制")
            self.record_btn.setStyleSheet("")
            self._picker_thread._recorder_should_be_active = False
            try:
                self._picker_thread.run_js("window.__webAutoRecorderActive = false;")
            except Exception:
                pass
            self.add_recorded_btn.setEnabled(bool(self._recorded_actions))
            self._set_status(
                f"✅ 录制已停止，共录制 {len(self._recorded_actions)} 个步骤",
                "#3498db"
            )

    def _reset_mode_buttons(self):
        self.pick_mode_btn.setText("🔍 进入拾取模式")
        self.pick_mode_btn.setStyleSheet("")
        self.record_btn.setText("🎬 开始录制")
        self.record_btn.setStyleSheet("")

    # ── 拾取回调 ────────────────────────────────────
    def _on_element_picked(self, element_info: dict):
        selector = element_info.get("selector", "")
        description = element_info.get("description", "")
        tag = element_info.get("tag", "")

        # v1.2.0 pick_one 模式：单次拾取，立即 emit 并关闭
        if self._mode == "pick_one":
            self.single_element_picked.emit(element_info)
            self._set_status(f"✅ 已捕获：{description}，正在关闭...", "#27ae60")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(300, self.close)
            return

        self.selector_input.setText(selector)
        self._set_status(f"✅ 已捕获：{description}", "#27ae60")

        el_type = element_info.get("type", "").lower()
        if tag in ("input", "textarea"):
            if el_type in ("text", "password", "email", "number", "search", ""):
                for i in range(self.step_type_combo.count()):
                    if self.step_type_combo.itemData(i) == StepType.INPUT:
                        self.step_type_combo.setCurrentIndex(i)
                        break
        elif tag == "select":
            for i in range(self.step_type_combo.count()):
                if self.step_type_combo.itemData(i) == StepType.SELECT:
                    self.step_type_combo.setCurrentIndex(i)
                    break

        if not self.step_name_input.text():
            text = element_info.get("text", "")
            if text:
                self.step_name_input.setText(f"操作：{text[:20]}")

    def _on_picker_exited(self):
        self._pick_mode = False
        self._record_mode = False
        self._reset_mode_buttons()
        self._set_status("拾取/录制模式已退出（右键退出）", "#e67e22")

    # ── 录制回调 ────────────────────────────────────
    def _on_recorded_action(self, action: dict):
        action_type = action.get('type')
        description = action.get('description') or action.get('selector', '')
        selector = action.get('selector', '')
        value = action.get('value', '')
        option_text = action.get('optionText', '')

        if action_type == 'click':
            step = Step(
                step_type=StepType.CLICK,
                description=description,
                selector=selector,
                selector_type='css',
                value='',
                timeout=120,
            )
            label = f"🖱️ 点击：{description}"
        elif action_type == 'input':
            step = Step(
                step_type=StepType.INPUT,
                description=f"输入：{value}" if value else description,
                selector=selector,
                selector_type='css',
                value=value,
                timeout=120,
            )
            label = f"⌨️ 输入：{value}"
        elif action_type == 'select':
            select_value = option_text or value
            step = Step(
                step_type=StepType.SELECT,
                description=f"选择：{select_value}" if select_value else description,
                selector=selector,
                selector_type='css',
                value=select_value,
                timeout=120,
            )
            label = f"📋 选择：{select_value}"
        else:
            return

        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, step)
        self.record_list.addItem(item)
        self._recorded_actions.append(step)
        self.add_recorded_btn.setEnabled(True)
        self.rec_count_label.setText(f"{self.record_list.count()} 步")

    def _add_recorded_steps(self):
        # 登录模式：转换为 LoginAction list 并 emit login_recorded
        if self._mode == "login":
            from models.login import LoginAction
            actions = []
            # 任务执行时通常需要先回到登录入口页，记录一个 open_url 动作作为首步
            url = self.url_input.text().strip()
            if url:
                actions.append(LoginAction(action_type="open_url", value=url))
            for i in range(self.record_list.count()):
                item = self.record_list.item(i)
                step = item.data(Qt.ItemDataRole.UserRole)
                if not isinstance(step, Step):
                    continue
                if step.step_type == StepType.CLICK:
                    actions.append(LoginAction(
                        action_type="click",
                        selector=step.selector,
                        selector_type=step.selector_type or "css",
                    ))
                elif step.step_type == StepType.INPUT:
                    actions.append(LoginAction(
                        action_type="input",
                        selector=step.selector,
                        selector_type=step.selector_type or "css",
                        value=step.value or "",
                    ))
                elif step.step_type == StepType.SELECT:
                    # SELECT 在登录场景少见但兼容，复用 input 动作
                    actions.append(LoginAction(
                        action_type="input",
                        selector=step.selector,
                        selector_type=step.selector_type or "css",
                        value=step.value or "",
                    ))
            self.login_recorded.emit(actions)
            self._set_status(f"✅ 登录模板已保存（{len(actions)} 步），请关闭本窗口", "#27ae60")
            return

        # 普通模式：为每条 emit step_configured（原有行为）
        count = 0
        for i in range(self.record_list.count()):
            item = self.record_list.item(i)
            step = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(step, Step):
                self.step_configured.emit(step)
                count += 1
        self._clear_recorded_actions()
        self._set_status(f"✅ 已将 {count} 个录制步骤添加到任务", "#27ae60")

    # v1.2.0 登录模式：占位符替换
    def _update_placeholder_btn_state(self):
        if not hasattr(self, "insert_user_btn"):
            return
        item = self.record_list.currentItem()
        is_input = False
        if item is not None:
            step = item.data(Qt.ItemDataRole.UserRole)
            is_input = isinstance(step, Step) and step.step_type == StepType.INPUT
        self.insert_user_btn.setEnabled(is_input)
        self.insert_pwd_btn.setEnabled(is_input)

    def _replace_selected_input_value(self, placeholder: str):
        """把当前选中的录制项（必须是 INPUT 步骤）的 value 改为占位符。
        显示文案同步更新成 🔒/🔑 形式，避免列表里残留明文密码。
        """
        item = self.record_list.currentItem()
        if item is None:
            return
        step = item.data(Qt.ItemDataRole.UserRole)
        if not (isinstance(step, Step) and step.step_type == StepType.INPUT):
            return
        step.value = placeholder
        step.description = f"输入：{placeholder}"
        icon = "🔒" if "password" in placeholder else "🔑"
        item.setText(f"⌨️ {icon} 输入：{placeholder}  ←  {step.selector[:40]}")

    def _remove_selected_recorded_actions(self):
        selected = self.record_list.selectedItems()
        if not selected:
            return
        rows = sorted(
            {self.record_list.row(item) for item in selected}, reverse=True
        )
        for row in rows:
            self.record_list.takeItem(row)
        self._recorded_actions = []
        for i in range(self.record_list.count()):
            item = self.record_list.item(i)
            step = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(step, Step):
                self._recorded_actions.append(step)
        self.add_recorded_btn.setEnabled(self.record_list.count() > 0)
        self.rec_count_label.setText(f"{self.record_list.count()} 步")
        self._update_record_selection_buttons()

    def _update_record_selection_buttons(self):
        self.remove_selected_btn.setEnabled(
            bool(self.record_list.selectedItems())
        )

    def _clear_recorded_actions(self):
        self._recorded_actions = []
        self.record_list.clear()
        self.add_recorded_btn.setEnabled(False)
        self.remove_selected_btn.setEnabled(False)
        self.rec_count_label.setText("0 步")

    # ── 步骤手动添加 ────────────────────────────────
    def _on_step_type_changed(self):
        step_type = self.step_type_combo.currentData()
        # v1.3.0：EXTRACT_DOM 也用 value_input，但当作"变量名"
        show_value = step_type in (
            StepType.INPUT, StepType.SELECT,
            StepType.WAIT, StepType.SCROLL, StepType.WAIT_ELEMENT,
            StepType.EXTRACT_DOM,
        )
        self.value_label.setVisible(show_value)
        self.value_input.setVisible(show_value)
        self.var_hint.setVisible(step_type == StepType.INPUT)

        if step_type == StepType.INPUT:
            self.value_label.setText("输入内容：")
            self.value_input.setPlaceholderText("支持 ${变量} [TODAY] 等占位符")
        elif step_type == StepType.SELECT:
            self.value_label.setText("选择选项：")
            self.value_input.setPlaceholderText("下拉框的选项文字或值")
        elif step_type == StepType.WAIT:
            self.value_label.setText("等待秒数：")
            self.value_input.setPlaceholderText("例如：3")
        elif step_type == StepType.SCROLL:
            self.value_label.setText("滚动方向：")
            self.value_input.setPlaceholderText("bottom / top / 像素数")
        elif step_type == StepType.EXTRACT_DOM:
            self.value_label.setText("变量名 *：")
            self.value_input.setPlaceholderText("如 评论列表（默认抽 innerText，详细配置去编辑器）")

    def _add_step(self):
        step_type = self.step_type_combo.currentData()
        selector = self.selector_input.text().strip()
        value = self.value_input.text().strip() if self.value_input.isVisible() else ""
        description = self.step_name_input.text().strip()

        if step_type not in (StepType.WAIT,) and not selector:
            QMessageBox.warning(
                self, "配置不完整",
                "请先在浏览器中点击目标元素，或手动输入CSS选择器！"
            )
            return

        # v1.3.0：EXTRACT_DOM 把 value_input 当变量名收集到 extra
        extra = {}
        step_value = value
        if step_type == StepType.EXTRACT_DOM:
            if not value:
                QMessageBox.warning(self, "配置不完整", "请填写变量名！")
                return
            extra = {
                "var_name": value,
                "attribute": "innerText",
                "concat_all": False,
                "separator": "\n",
            }
            step_value = ""  # value 字段不再存数据

        step = Step(
            step_type=step_type,
            description=description,
            selector=selector,
            selector_type="css",
            value=step_value,
            timeout=120,
            extra=extra,
        )
        self.step_configured.emit(step)

        self.selector_input.clear()
        self.step_name_input.clear()
        self.value_input.clear()
        self._set_status("步骤已添加！继续点击网页元素配置下一步骤...", "#3498db")

    # ── 工具方法 ────────────────────────────────────
    def _set_status(self, text: str, color: str = "#666"):
        self.desc_label.setText(text)
        self.desc_label.setStyleSheet(
            f"color:{color}; font-weight:bold;"
        )

    def closeEvent(self, event):
        if self._picker_thread and self._picker_thread.isRunning():
            self._picker_thread.stop()
            self._picker_thread.wait(3000)
        # 清掉单例引用，避免后续 current_instance() 仍返回已死实例
        if VisualPickerWindow._active_instance is self:
            VisualPickerWindow._active_instance = None
        super().closeEvent(event)
