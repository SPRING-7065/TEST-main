"""
后台执行引擎（核心）
支持：正常无头模式、调试可见模式、截图预览、持久化缓存
"""
import os
import sys
import time
import datetime
import threading
import base64
from typing import List, Optional, Callable

from models.task import Task
from models.step import Step, StepType
from core.variable_parser import parse_variables
from core.file_manager import get_full_save_path, get_download_dir
from core import logger

def get_app_root() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_chromium_path() -> Optional[str]:
    base = get_app_root()
    candidates = [
        # 打包内置浏览器（Windows）
        os.path.join(base, "browser", "chrome.exe"),
        os.path.join(base, "browser", "chromium.exe"),
        os.path.join(base, "browser", "chrome-win", "chrome.exe"),
        # Windows 系统 Chrome
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def get_cache_dir() -> str:
    cache_dir = os.path.join(get_app_root(), "browser_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

class TaskExecutionError(Exception):
    pass

class DownloadInterceptor:
    def __init__(self, watch_dir: str, task_name: str):
        self.watch_dir = watch_dir
        self.task_name = task_name
        self.downloaded_file: Optional[str] = None
        self._before_files: set = set()

    def snapshot_before(self):
        if os.path.exists(self.watch_dir):
            self._before_files = set(os.listdir(self.watch_dir))
        else:
            self._before_files = set()

    def wait_for_new_file(self, timeout: int = 120) -> Optional[str]:
        start = time.time()
        while time.time() - start < timeout:
            if os.path.exists(self.watch_dir):
                current_files = set(os.listdir(self.watch_dir))
                new_files = current_files - self._before_files
                real_files = [f for f in new_files
                              if not f.endswith(('.crdownload', '.tmp', '.part'))]
                if real_files:
                    file_path = os.path.join(self.watch_dir, real_files[0])
                    time.sleep(1)
                    self.downloaded_file = file_path
                    return file_path
            time.sleep(0.5)
        return None

class ExecutionEngine:
    def __init__(self, task: Task,
                 log_callback: Optional[Callable] = None,
                 status_callback: Optional[Callable] = None,
                 screenshot_callback: Optional[Callable] = None,
                 progress_callback: Optional[Callable] = None,
                 debug_mode: bool = False):
        self.task = task
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.screenshot_callback = screenshot_callback
        self.progress_callback = progress_callback
        self.debug_mode = debug_mode
        self._page = None
        self._stop_flag = False
        self._downloaded_files: List[str] = []
        self._step_start_time: float = 0
        self._screenshot_timer: Optional[threading.Timer] = None

    def stop(self):
        self._stop_flag = True
        self._cancel_screenshot_timer()

    def _log(self, message: str, level: str = "info"):
        if level == "info":
            logger.log_info(message)
        elif level == "success":
            logger.log_success(message)
        elif level == "warning":
            logger.log_warning(message)
        elif level == "error":
            logger.log_error(message)

    def _update_status(self, status: str):
        if self.status_callback:
            self.status_callback(self.task.task_id, status)

    def _update_progress(self, current: int, total: int, step_name: str):
        if self.progress_callback:
            self.progress_callback(current, total, step_name)

    def _take_screenshot(self):
        if not self.screenshot_callback or not self._page:
            return
        try:
            img_bytes = self._page.get_screenshot(as_bytes=True)
            if img_bytes:
                self.screenshot_callback(img_bytes)
        except Exception:
            pass

    def _start_screenshot_timer(self, interval: float = 4.0):
        self._cancel_screenshot_timer()
        if not self.screenshot_callback:
            return
        def _loop():
            self._take_screenshot()
            if not self._stop_flag and self._page:
                self._start_screenshot_timer(interval)
        self._screenshot_timer = threading.Timer(interval, _loop)
        self._screenshot_timer.daemon = True
        self._screenshot_timer.start()

    def _cancel_screenshot_timer(self):
        if self._screenshot_timer:
            self._screenshot_timer.cancel()
            self._screenshot_timer = None

    def execute(self) -> bool:
        mode_str = "调试模式（浏览器可见）" if self.debug_mode else "后台静默模式"
        self._log(f"任务【{self.task.name}】开始执行（{mode_str}）...")
        self._update_status("running")

        for attempt in range(1, self.task.max_retries + 1):
            if self._stop_flag:
                self._log(f"任务【{self.task.name}】已被手动停止", "warning")
                self._update_status("stopped")
                return False
            if attempt > 1:
                self._log(f"任务【{self.task.name}】正在进行第 {attempt} 次重试...")
                time.sleep(3)
            try:
                result = self._execute_once()
                if result:
                    self._update_status("success")
                    return True
            except Exception as e:
                friendly_msg = logger.translate_exception(e)
                if attempt < self.task.max_retries:
                    self._log(
                        f"任务【{self.task.name}】第{attempt}次执行遇到问题：{friendly_msg}，"
                        f"稍后将自动重试（{attempt}/{self.task.max_retries}）",
                        "warning"
                    )
                else:
                    self._log(
                        f"任务【{self.task.name}】执行失败。原因：{friendly_msg}，"
                        f"重试{self.task.max_retries}次依然失败。",
                        "error"
                    )
            finally:
                self._cancel_screenshot_timer()
                self._cleanup_browser()

        self._update_status("failed")
        return False

    def _execute_once(self) -> bool:
        from DrissionPage import ChromiumPage, ChromiumOptions

        options = ChromiumOptions()
        if self.debug_mode:
            options.headless(False)
            options.set_argument('--window-size=1280,800')
            options.set_argument('--window-position=50,50')
            self._log("  🖥️ 调试模式：浏览器窗口已打开，您可以实时观察执行过程")
        else:
            options.headless(True)

        options.no_imgs(False)
        options.mute(True)

        cache_dir = get_cache_dir()
        options.set_user_data_path(cache_dir)
        self._log(f"  💾 使用持久化缓存：{cache_dir}")

        download_dir = get_download_dir(self.task.save_dir_override)
        options.set_download_path(download_dir)
        options.set_argument('--disable-popup-blocking')
        options.set_argument('--disable-notifications')
        # --no-sandbox仅在非Windows环境下需要
        import platform as _platform
        if _platform.system() != 'Windows':
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-dev-shm-usage')

        chromium_path = get_chromium_path()
        if chromium_path:
            options.set_browser_path(chromium_path)

        self._log(f"任务【{self.task.name}】正在启动浏览器...")
        self._page = ChromiumPage(options)
        self._page.set.download_path(download_dir)
        self._page.set.auto_handle_alert(True)

        total_steps = len(self.task.steps)
        self._log(f"任务【{self.task.name}】浏览器就绪，共 {total_steps} 个步骤，开始执行...")

        if self.screenshot_callback:
            self._start_screenshot_timer(interval=4.0)

        for i, step in enumerate(self.task.steps, 1):
            if self._stop_flag:
                raise TaskExecutionError("任务被手动停止")

            step_name = step.get_display_name()
            self._step_start_time = time.time()
            self._update_progress(i, total_steps, step_name)

            try:
                current_url = self._page.url
                url_hint = f" | 页面：{current_url[:60]}" if current_url else ""
            except Exception:
                url_hint = ""

            self._log(f"  → [{i}/{total_steps}] {step_name}{url_hint}")

            try:
                self._execute_step(step, download_dir)
                elapsed = time.time() - self._step_start_time
                self._log(f"  ✓ 步骤 {i} 完成（耗时 {elapsed:.1f}s）")
                if self.screenshot_callback:
                    self._take_screenshot()
            except Exception as e:
                elapsed = time.time() - self._step_start_time
                if step.optional:
                    self._log(
                        f"  ⚠️ 步骤 {i} 失败（可选步骤，跳过）耗时{elapsed:.1f}s："
                        f"{logger.translate_exception(e)}",
                        "warning"
                    )
                    continue
                raise

        if self._downloaded_files:
            for f in self._downloaded_files:
                self._log(
                    f"任务【{self.task.name}】已无声执行完毕！文件安稳保存在：{f}",
                    "success"
                )
        else:
            self._log(f"任务【{self.task.name}】所有步骤执行完毕！", "success")

        return True

    def _execute_step(self, step: Step, download_dir: str) -> None:
        value = parse_variables(step.value)
        selector = step.selector
        timeout = step.timeout
        step_type = step.step_type

        if step_type == StepType.OPEN_URL:
            url = value or selector
            if not url:
                raise TaskExecutionError("打开网址步骤缺少URL")
            self._page.get(url, timeout=timeout)
            self._wait_for_page_load(timeout)
        elif step_type == StepType.CLICK:
            element = self._find_element(selector, step.selector_type, timeout)
            element.click()
            time.sleep(0.5)
        elif step_type == StepType.INPUT:
            element = self._find_element(selector, step.selector_type, timeout)
            # 先尝试原生clear+input
            element.clear()
            time.sleep(0.2)

            # 对Vue/React等框架，普通input()不触发框架事件
            # 使用element.run_js()：底层走Runtime.callFunctionOn，
            # 'this'直接绑定到DOM元素，避免page.run_js()无法正确
            # 传递ChromiumElement引用的问题；同时兼容textarea元素
            try:
                element.click()
                time.sleep(0.1)
                element.run_js("""
                    var value = arguments[0];
                    var tag = this.tagName.toLowerCase();
                    var proto = tag === 'textarea'
                        ? window.HTMLTextAreaElement.prototype
                        : window.HTMLInputElement.prototype;
                    var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
                    setter.call(this, value);
                    this.dispatchEvent(new Event('input', { bubbles: true }));
                    this.dispatchEvent(new Event('change', { bubbles: true }));
                """, value)
                time.sleep(0.2)
                # 验证是否输入成功（element.run_js的this即为元素本身）
                actual = element.run_js("return this.value")
                if actual != value:
                    # JS方式失败，回退到逐字符输入
                    element.clear()
                    element.input(value, clear=True)
                    self._log(f"    ℹ️ 使用逐字符输入模式", "info")
                else:
                    self._log(f"    ✅ 框架事件触发成功，值已设置", "info")
            except Exception as input_e:
                # 最终回退：直接用DrissionPage的input
                self._log(f"    ⚠️ JS输入失败({input_e})，使用默认输入", "warning")
                element.clear()
                element.input(value)
            time.sleep(0.3)
        elif step_type == StepType.CLEAR_INPUT:
            element = self._find_element(selector, step.selector_type, timeout)
            element.clear()
        elif step_type == StepType.SELECT:
            element = self._find_element(selector, step.selector_type, timeout)
            try:
                element.select.by_text(value)
            except Exception:
                try:
                    element.select.by_value(value)
                except Exception:
                    element.select.by_index(int(value) if value.isdigit() else 0)
        elif step_type == StepType.WAIT:
            wait_seconds = float(value) if value else 2.0
            wait_seconds = min(wait_seconds, 60)
            time.sleep(wait_seconds)
        elif step_type == StepType.WAIT_ELEMENT:
            self._find_element(selector, step.selector_type, timeout)
        elif step_type == StepType.SCROLL:
            if value.lower() == "bottom":
                self._page.scroll.to_bottom()
            elif value.lower() == "top":
                self._page.scroll.to_top()
            else:
                try:
                    self._page.scroll.down(int(value))
                except ValueError:
                    self._page.scroll.down(300)
        elif step_type == StepType.DOWNLOAD_CLICK:
            self._handle_download_click(step, selector, download_dir, timeout)
        else:
            self._log(f"  ⚠️ 未知步骤类型：{step_type}，已跳过", "warning")

    def _find_element(self, selector: str, selector_type: str, timeout: int):
        if not selector:
            raise TaskExecutionError("选择器不能为空")
        try:
            if selector_type == "xpath":
                element = self._page.ele(f'xpath:{selector}', timeout=timeout)
            elif selector_type == "text":
                element = self._page.ele(f'text:{selector}', timeout=timeout)
            else:
                # 必须加 css: 前缀，否则 DrissionPage 会把纯单词（如 'i'、'div'）
                # 当成文字内容搜索而非 CSS 标签选择器，导致超时
                css_selector = selector if selector.startswith('css:') else f'css:{selector}'
                element = self._page.ele(css_selector, timeout=timeout)
            if element is None:
                raise TaskExecutionError(f"找不到元素：{selector}")
            return element
        except Exception as e:
            if "timeout" in str(e).lower():
                raise TimeoutError(f"等待元素超过{timeout}秒：{selector}")
            raise

    def _wait_for_page_load(self, timeout: int = 120) -> None:
        try:
            self._page.wait.load_start(timeout=timeout)
        except Exception:
            pass

    def _handle_download_click(self, step: Step, selector: str,
                                download_dir: str, timeout: int) -> None:
        interceptor = DownloadInterceptor(download_dir, self.task.name)
        interceptor.snapshot_before()
        if selector:
            element = self._find_element(selector, step.selector_type, timeout)
            element.click()
        else:
            raise TaskExecutionError("下载步骤缺少目标元素选择器")
        self._log("  ⏳ 已点击下载按钮，等待文件保存...")
        downloaded_path = interceptor.wait_for_new_file(timeout=timeout)
        if downloaded_path:
            import shutil
            original_name = os.path.basename(downloaded_path)
            new_path = get_full_save_path(
                task_name=self.task.name,
                original_filename=original_name,
                custom_dir=self.task.save_dir_override
            )
            try:
                shutil.move(downloaded_path, new_path)
                self._downloaded_files.append(new_path)
                self._log(f"  ✅ 文件已保存：{new_path}")
            except Exception:
                self._downloaded_files.append(downloaded_path)
                self._log(f"  ✅ 文件已保存：{downloaded_path}")
        else:
            raise TaskExecutionError(f"等待文件下载超过{timeout}秒，文件未能成功保存")

    def _cleanup_browser(self) -> None:
        try:
            if self._page:
                self._page.quit()
                self._page = None
        except Exception:
            pass

class TaskThreadWrapper:
    def __init__(self, thread: threading.Thread, engine: ExecutionEngine):
        self._thread = thread
        self._engine = engine

    def start(self):
        self._thread.start()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def stop(self):
        self._engine.stop()

    def join(self, timeout: Optional[float] = None):
        self._thread.join(timeout)

    @property
    def name(self) -> str:
        return self._thread.name

def run_task_in_thread(
        task: Task,
        log_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None,
        completion_callback: Optional[Callable] = None,
        screenshot_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        debug_mode: bool = False) -> TaskThreadWrapper:

    engine = ExecutionEngine(
        task=task,
        log_callback=log_callback,
        status_callback=status_callback,
        screenshot_callback=screenshot_callback,
        progress_callback=progress_callback,
        debug_mode=debug_mode,
    )

    def _run():
        success = engine.execute()
        if completion_callback:
            completion_callback(task.task_id, success)

    thread = threading.Thread(
        target=_run, daemon=True, name=f"task_{task.task_id}"
    )
    thread.start()
    return TaskThreadWrapper(thread, engine)