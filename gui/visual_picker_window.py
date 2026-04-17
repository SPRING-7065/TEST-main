"""
可视化元素拾取窗口
"""
import time
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

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
    banner.style.cssText = 'position:fixed;top:0;left:0;right:0;background:linear-gradient(135deg,#667eea,#764ba2);color:white;text-align:center;padding:10px;font-size:14px;font-weight:bold;z-index:9999999;font-family:Microsoft YaHei,sans-serif;box-shadow:0 2px 10px rgba(0,0,0,0.3);';
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
            import platform as _plt
            if _plt.system() != 'Windows':
                options.set_argument('--no-sandbox')
                options.set_argument('--disable-dev-shm-usage')
            chromium_path = get_chromium_path()
            if chromium_path:
                options.set_browser_path(chromium_path)
            self._page = ChromiumPage(options)
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

class VisualPickerWindow(QDialog):
    step_configured = Signal(object)

    def __init__(self, parent=None, initial_url: str = ""):
        super().__init__(parent)
        self.setWindowTitle("🎯 可视化元素拾取 - 点击网页元素来配置步骤")
        self.setMinimumSize(720, 680)
        self.setModal(False)

        self._picker_thread: Optional[PickerThread] = None
        self._initial_url = initial_url
        self._pick_mode = False
        self._record_mode = False
        self._recorded_actions = []

        self._setup_ui()
        self._apply_styles()

    # ── UI构建 ──────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # 顶部说明
        info_label = QLabel(
            "📖 <b>使用说明</b>：在弹出的浏览器中操作，"
            "点击「进入拾取模式」后鼠标悬停高亮元素，左键单击即可捕获。"
            "或点击「开始录制」自动记录您的操作。右键退出拾取/录制。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "background:#e8f4fd; padding:10px; border-radius:5px; color:#1a5276;"
        )
        layout.addWidget(info_label)

        # URL输入区
        url_group = QGroupBox("目标网页地址")
        url_layout = QHBoxLayout(url_group)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入要打开的网页地址，例如：https://www.example.com")
        self.url_input.setText(self._initial_url)
        url_layout.addWidget(self.url_input)

        self.open_btn = QPushButton("🚀 打开浏览器")
        self.open_btn.setFixedWidth(130)
        self.open_btn.clicked.connect(self._start_picker)
        url_layout.addWidget(self.open_btn)

        layout.addWidget(url_group)

        # 模式控制区
        mode_group = QGroupBox("操作模式")
        mode_layout = QHBoxLayout(mode_group)

        self.pick_mode_btn = QPushButton("🔍 进入拾取模式")
        self.pick_mode_btn.setEnabled(False)
        self.pick_mode_btn.clicked.connect(self._toggle_pick_mode)
        mode_layout.addWidget(self.pick_mode_btn)

        self.record_btn = QPushButton("🎬 开始录制")
        self.record_btn.setEnabled(False)
        self.record_btn.clicked.connect(self._toggle_record_mode)
        mode_layout.addWidget(self.record_btn)

        self.reinject_btn = QPushButton("🔄 重新激活脚本")
        self.reinject_btn.setEnabled(False)
        self.reinject_btn.clicked.connect(self._reinject_and_reset)
        mode_layout.addWidget(self.reinject_btn)

        layout.addWidget(mode_group)

        # 步骤类型选择
        type_group = QGroupBox("步骤类型（拾取模式下使用）")
        type_layout = QHBoxLayout(type_group)
        type_layout.addWidget(QLabel("这个步骤要做什么："))
        self.step_type_combo = QComboBox()
        for step_type, label in STEP_TYPE_LABELS.items():
            if step_type != StepType.OPEN_URL:
                self.step_type_combo.addItem(label, step_type)
        self.step_type_combo.currentIndexChanged.connect(self._on_step_type_changed)
        type_layout.addWidget(self.step_type_combo, 1)
        layout.addWidget(type_group)

        # 捕获结果显示区
        result_group = QGroupBox("📍 捕获到的元素信息（拾取模式）")
        result_layout = QVBoxLayout(result_group)

        desc_row = QHBoxLayout()
        desc_row.addWidget(QLabel("状态："))
        self.desc_label = QLabel("等待浏览器启动...")
        self.desc_label.setStyleSheet("color:#666; font-style:italic;")
        desc_row.addWidget(self.desc_label, 1)
        result_layout.addLayout(desc_row)

        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("CSS选择器："))
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("点击网页元素后自动填入，也可手动修改")
        self.selector_input.setFont(QFont("Consolas", 10))
        sel_row.addWidget(self.selector_input, 1)
        result_layout.addLayout(sel_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("步骤名称："))
        self.step_name_input = QLineEdit()
        self.step_name_input.setPlaceholderText("给这个步骤起个名字（可选）")
        name_row.addWidget(self.step_name_input, 1)
        result_layout.addLayout(name_row)

        self.value_row = QHBoxLayout()
        self.value_label = QLabel("输入内容：")
        self.value_row.addWidget(self.value_label)
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("支持 [TODAY]、[TODAY-1] 等时间占位符")
        self.value_row.addWidget(self.value_input, 1)
        result_layout.addLayout(self.value_row)

        self.var_hint = QLabel(
            "💡 [TODAY]=今天  [TODAY-1]=昨天  [TODAY-7]=7天前  "
            "[MONTH_START]=本月初  [MONTH_END]=本月末"
        )
        self.var_hint.setStyleSheet("color:#666; font-size:11px;")
        self.var_hint.setWordWrap(True)
        result_layout.addWidget(self.var_hint)

        add_single_btn = QPushButton("✅ 添加此步骤到任务")
        add_single_btn.setStyleSheet(
            "QPushButton{background:#27ae60;color:white;font-weight:bold;"
            "border-radius:4px;padding:6px 16px;border:none;}"
            "QPushButton:hover{background:#2ecc71;}"
        )
        add_single_btn.clicked.connect(self._add_step)
        result_layout.addWidget(add_single_btn)

        layout.addWidget(result_group)

        # 录制结果区
        record_group = QGroupBox("📼 录制结果（录制模式）")
        record_layout = QVBoxLayout(record_group)

        self.record_list = QListWidget()
        self.record_list.setAlternatingRowColors(True)
        self.record_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )
        self.record_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.record_list.itemSelectionChanged.connect(
            self._update_record_selection_buttons
        )
        self.record_list.setMinimumHeight(120)
        self.record_list.setMaximumHeight(160)
        record_layout.addWidget(self.record_list)

        record_btn_row = QHBoxLayout()

        self.add_recorded_btn = QPushButton("✅ 添加录制步骤到任务")
        self.add_recorded_btn.setEnabled(False)
        self.add_recorded_btn.setStyleSheet(
            "QPushButton{background:#2980b9;color:white;font-weight:bold;"
            "border-radius:4px;border:none;}"
            "QPushButton:hover{background:#3498db;}"
            "QPushButton:disabled{background:#bdc3c7;}"
        )
        self.add_recorded_btn.clicked.connect(self._add_recorded_steps)
        record_btn_row.addWidget(self.add_recorded_btn)

        self.remove_selected_btn = QPushButton("🗑 删除选中")
        self.remove_selected_btn.setEnabled(False)
        self.remove_selected_btn.clicked.connect(self._remove_selected_recorded_actions)
        record_btn_row.addWidget(self.remove_selected_btn)

        clear_btn = QPushButton("🧹 清空")
        clear_btn.clicked.connect(self._clear_recorded_actions)
        record_btn_row.addWidget(clear_btn)

        record_layout.addLayout(record_btn_row)
        layout.addWidget(record_group)

        # 底部关闭按钮
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        close_btn = QPushButton("关闭拾取窗口")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.close)
        bottom_row.addWidget(close_btn)
        layout.addLayout(bottom_row)

        self._on_step_type_changed()

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background: #f5f6fa; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                background: white;
            }
            QLineEdit:focus { border-color: #3498db; }
            QPushButton {
                border: 1px solid #bbb;
                border-radius: 4px;
                padding: 5px 12px;
                background: #ecf0f1;
            }
            QPushButton:hover { background: #d5dbdb; }
            QPushButton:disabled { color: #aaa; background: #f0f0f0; }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QListWidget::item { padding: 4px 8px; }
            QListWidget::item:selected { background: #d6eaf8; color: #1a5276; }
            QListWidget::item:alternate { background: #f8f9fa; }
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

    def _add_recorded_steps(self):
        count = 0
        for i in range(self.record_list.count()):
            item = self.record_list.item(i)
            step = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(step, Step):
                self.step_configured.emit(step)
                count += 1
        self._clear_recorded_actions()
        self._set_status(f"✅ 已将 {count} 个录制步骤添加到任务", "#27ae60")

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

    # ── 步骤手动添加 ────────────────────────────────
    def _on_step_type_changed(self):
        step_type = self.step_type_combo.currentData()
        show_value = step_type in (
            StepType.INPUT, StepType.SELECT,
            StepType.WAIT, StepType.SCROLL, StepType.WAIT_ELEMENT
        )
        self.value_label.setVisible(show_value)
        self.value_input.setVisible(show_value)
        self.var_hint.setVisible(step_type == StepType.INPUT)

        if step_type == StepType.INPUT:
            self.value_label.setText("输入内容：")
            self.value_input.setPlaceholderText("支持 [TODAY]、[TODAY-1] 等占位符")
        elif step_type == StepType.SELECT:
            self.value_label.setText("选择选项：")
            self.value_input.setPlaceholderText("下拉框的选项文字或值")
        elif step_type == StepType.WAIT:
            self.value_label.setText("等待秒数：")
            self.value_input.setPlaceholderText("例如：3")
        elif step_type == StepType.SCROLL:
            self.value_label.setText("滚动方向：")
            self.value_input.setPlaceholderText("bottom / top / 像素数")

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

        step = Step(
            step_type=step_type,
            description=description,
            selector=selector,
            selector_type="css",
            value=value,
            timeout=120,
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
        super().closeEvent(event)
