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
    candidates = [
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


CHROME_NOT_FOUND_MSG = (
    "未检测到 Google Chrome。请先安装 Chrome 浏览器后重试："
    "https://www.google.cn/chrome/"
)

def get_cache_dir(debug: bool = False, task_id: Optional[str] = None) -> str:
    """按任务隔离的浏览器用户数据目录。

    多任务并发时必须隔离，否则 Chromium 会因 user-data-dir 锁冲突而失败。
    路径形如 browser_cache/{task_id}/  或  browser_cache_debug/{task_id}/
    未传 task_id 时回退到根目录（向后兼容，不应在并发场景使用）。
    """
    name = "browser_cache_debug" if debug else "browser_cache"
    base = os.path.join(get_app_root(), name)
    cache_dir = os.path.join(base, task_id) if task_id else base
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def migrate_legacy_cache_if_needed(task_ids: list) -> None:
    """v1.1.4 升级一次性迁移：把老的 browser_cache/Default/ 等
    Chromium 配置目录搬到第一个任务的子目录下，保留登录态。
    搬完原目录加 `_legacy_<时间戳>` 后缀备份不删。
    """
    import time as _time
    if not task_ids:
        return
    for name in ("browser_cache", "browser_cache_debug"):
        legacy_dir = os.path.join(get_app_root(), name)
        if not os.path.isdir(legacy_dir):
            continue
        # 老格式特征：根目录下直接含有 Chromium 的 Default/ 或 Local State
        has_default = os.path.isdir(os.path.join(legacy_dir, "Default"))
        has_local_state = os.path.isfile(os.path.join(legacy_dir, "Local State"))
        if not (has_default or has_local_state):
            continue
        first_task_id = task_ids[0]
        target_dir = os.path.join(legacy_dir, first_task_id)
        if os.path.exists(target_dir):
            continue  # 已经迁移过
        try:
            os.makedirs(target_dir, exist_ok=True)
            for entry in os.listdir(legacy_dir):
                # 已经是 task_id 子目录的就别动
                if entry in task_ids:
                    continue
                src = os.path.join(legacy_dir, entry)
                dst = os.path.join(target_dir, entry)
                if not os.path.exists(dst):
                    os.rename(src, dst)
            # 备份标记
            backup_marker = os.path.join(
                legacy_dir, f"_migrated_to_{first_task_id}_{int(_time.time())}.txt"
            )
            with open(backup_marker, "w", encoding="utf-8") as f:
                f.write(f"Migrated legacy cache to subdir: {first_task_id}\n")
        except Exception:
            pass

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
        # headless 必须最先设置，避免 DrissionPage 内部初始化逻辑在后续重置显示侧 flag
        if self.debug_mode:
            options.headless(False)
        else:
            options.headless(True)

        # 两种模式都使用相同窗口尺寸，确保元素坐标、响应式布局一致
        options.set_argument('--window-size=1280,800')
        if self.debug_mode:
            options.set_argument('--window-position=50,50')
            self._log("  🖥️ 调试模式：浏览器窗口已打开，您可以实时观察执行过程")
        else:
            options.set_argument('--disable-gpu')
            options.set_argument('--force-device-scale-factor=1')

        options.no_imgs(False)
        options.mute(True)

        cache_dir = get_cache_dir(debug=self.debug_mode, task_id=self.task.task_id)
        options.set_user_data_path(cache_dir)
        self._log(f"  💾 使用持久化缓存：{cache_dir}")

        download_dir = get_download_dir(self.task.save_dir_override)
        options.set_download_path(download_dir)
        options.set_argument('--disable-popup-blocking')
        options.set_argument('--disable-notifications')
        # 隐藏自动化特征
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--exclude-switches=enable-automation')
        options.set_argument('--disable-infobars')

        import platform as _platform
        if _platform.system() != 'Windows':
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-dev-shm-usage')

        chromium_path = get_chromium_path()
        if not chromium_path:
            raise TaskExecutionError(CHROME_NOT_FOUND_MSG)
        options.set_browser_path(chromium_path)

        self._log(f"任务【{self.task.name}】正在启动浏览器...")
        self._page = ChromiumPage(options)
        self._page.set.download_path(download_dir)
        self._page.set.auto_handle_alert(True)
        # 注入反检测脚本：在每个页面加载前执行，抹除自动化特征
        # Page.addScriptToEvaluateOnNewDocument 注册的脚本比页面JS更早运行
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
                if self._stop_flag:
                    raise TaskExecutionError("任务被手动停止")
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
            url_before = ""
            try:
                url_before = self._page.url or ""
            except Exception:
                pass
            # 提前快照：若此点击触发下载，可用文件监控兜底
            interceptor = DownloadInterceptor(download_dir, self.task.name)
            interceptor.snapshot_before()
            self._do_click(element)
            time.sleep(0.8)
            # URL 变化 → 页面跳转
            try:
                url_after = self._page.url or ""
                if url_after != url_before:
                    self._wait_for_page_load(timeout)
                    return  # 跳转后不检测下载
            except Exception:
                pass
            # URL 未变 → 检测是否触发了下载（2 秒窗口，不阻塞正常点击太久）
            # DrissionPage 超时时返回 False 而非抛异常，需先判断真值
            mission = None
            try:
                m = self._page.wait.download_begin(timeout=2)
                if m:
                    mission = m
            except Exception:
                pass
            if mission is not None:
                self._log("  📥 检测到文件下载（建议将此步骤改为「⬇️ 点击下载」类型以确保每次验证）", "warning")
                self._finish_download_mission(mission, timeout)
            else:
                quick_file = interceptor.wait_for_new_file(timeout=1)
                if quick_file:
                    self._log("  📥 文件监控检测到下载（建议改为「⬇️ 点击下载」类型）", "warning")
                    self._save_downloaded_file(quick_file)
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
        # 分段查找：每 5 秒检查一次停止标志，避免单次 120 秒等待无法响应停止
        chunk = 5
        deadline = time.time() + timeout
        while True:
            if self._stop_flag:
                raise TaskExecutionError("任务被手动停止")
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(f"等待元素超过{timeout}秒：{selector}")
            t = min(chunk, remaining)
            try:
                if selector_type == "xpath":
                    element = self._page.ele(f'xpath:{selector}', timeout=t)
                elif selector_type == "text":
                    element = self._page.ele(f'text:{selector}', timeout=t)
                else:
                    css_selector = selector if selector.startswith('css:') else f'css:{selector}'
                    element = self._page.ele(css_selector, timeout=t)
                if element is not None:
                    return element
            except Exception as e:
                if self._stop_flag:
                    raise TaskExecutionError("任务被手动停止")
                if time.time() >= deadline:
                    raise TimeoutError(f"等待元素超过{timeout}秒：{selector}")
                if "timeout" not in str(e).lower():
                    raise

    def _wait_for_page_load(self, timeout: int = 120) -> None:
        # 等待 DOM 加载完成
        try:
            self._page.wait.doc_loaded(timeout=timeout)
        except Exception:
            pass
        # SPA 框架（React/Vue）在 readyState=complete 后 JS 可能还未渲染
        # 检测策略：body 子元素 > 1 AND DOM 元素总数稳定（连续两次相同）
        # 最多等 15 秒，每 0.5 秒检查一次
        deadline = time.time() + 15
        elapsed_checks = 0
        last_dom_count = -1
        stable_count = 0
        while time.time() < deadline:
            if self._stop_flag:
                break
            try:
                ready = self._page.run_js("return document.readyState")
                count = self._page.run_js(
                    "return document.body ? document.body.children.length : 0"
                )
                dom_total = self._page.run_js(
                    "return document.querySelectorAll('*').length"
                )
                url = self._page.url or ""
                elapsed_checks += 1
                if elapsed_checks == 1 or elapsed_checks % 4 == 0:
                    self._log(
                        f"    [页面检测] readyState={ready} body子元素={count} DOM总数={dom_total} url={url[:60]}",
                        "info"
                    )
                if isinstance(count, int) and count > 1:
                    if dom_total == last_dom_count:
                        stable_count += 1
                        if stable_count >= 2:  # 连续 1 秒 DOM 稳定则认为渲染完成
                            break
                    else:
                        stable_count = 0
                    last_dom_count = dom_total
            except Exception:
                break
            time.sleep(0.5)

    def _do_click(self, element) -> None:
        """三层点击降级：actions.click → element.click → JS this.click()"""
        clicked = False
        try:
            try:
                element.scroll.to_see()
                time.sleep(0.2)
            except Exception:
                pass
            self._page.actions.click(element)
            clicked = True
            self._log("    ✅ actions.click 成功", "info")
        except Exception as e1:
            self._log(f"    ℹ️ actions.click 失败({type(e1).__name__})，尝试 element.click", "info")
            try:
                element.click()
                clicked = True
                self._log("    ✅ element.click 成功", "info")
            except Exception as e2:
                self._log(f"    ℹ️ element.click 失败({type(e2).__name__})，使用 JS click", "info")
        if not clicked:
            element.run_js("this.click()")
            self._log("    ✅ JS this.click() 兜底执行", "info")

    def _save_downloaded_file(self, downloaded_path: str) -> None:
        """将下载的文件移动到任务保存目录并记录"""
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

    def _finish_download_mission(self, mission, timeout: int) -> None:
        """等待 DrissionPage 下载任务完成并保存文件"""
        self._log("  📥 检测到下载开始，等待写入完成...")
        try:
            result = mission.wait(timeout=timeout)
            if result:
                self._save_downloaded_file(str(result))
                return
        except Exception as e:
            self._log(f"  ⚠️ 原生下载等待异常({type(e).__name__})，改用文件监控", "warning")
        raise TaskExecutionError("下载任务等待失败，将由文件监控接管")

    def _handle_download_click(self, step: Step, selector: str,
                                download_dir: str, timeout: int) -> None:
        if not selector:
            raise TaskExecutionError("下载步骤缺少目标元素选择器")
        element = self._find_element(selector, step.selector_type, timeout)
        # 提前快照，作为文件监控兜底的基准
        interceptor = DownloadInterceptor(download_dir, self.task.name)
        interceptor.snapshot_before()
        # 三层点击，与普通 CLICK 步骤一致
        self._do_click(element)
        self._log("  ⏳ 已点击下载按钮，等待文件保存...")
        # 方案一：DrissionPage 原生下载事件（更准确，能拿到精确路径）
        # DrissionPage 超时返回 False，需先判断真值再使用
        mission = None
        try:
            m = self._page.wait.download_begin(timeout=30)
            if m:
                mission = m
        except Exception as e:
            self._log(f"  ℹ️ 原生下载API未响应({type(e).__name__})，改用文件监控", "info")
        if mission is not None:
            try:
                self._finish_download_mission(mission, timeout)
                return
            except TaskExecutionError:
                pass  # _finish_download_mission 内部已 fallthrough
        # 方案二：文件系统监控兜底（基于点击前的快照）
        downloaded_path = interceptor.wait_for_new_file(timeout=timeout)
        if downloaded_path:
            self._save_downloaded_file(downloaded_path)
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
        from core import concurrency
        # 等待并发槽位（超出上限时排队，UI 上任务会停留在 running 前的 queued 状态）
        if status_callback:
            status_callback(task.task_id, "queued")
        concurrency.acquire()
        try:
            success = engine.execute()
        finally:
            concurrency.release()
        if completion_callback:
            completion_callback(task.task_id, success)

    thread = threading.Thread(
        target=_run, daemon=True, name=f"task_{task.task_id}"
    )
    thread.start()
    return TaskThreadWrapper(thread, engine)