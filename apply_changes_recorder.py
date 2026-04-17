"""
修复录制阶段 Bug：页面跳转后 PICKER_JS 丢失，新页面操作无法被录制

根本原因：PICKER_JS 只存在于注入时的那个页面，用户点击链接跳转到新页面后，
          新页面是全新 document，脚本不复存在；PickerThread 轮询仍在运行，
          但 window.__webAutoRecorderGetEvents 是 undefined，
          导致新页面的所有 click/change 事件都捞不到。

修复方法：在 PickerThread 轮询循环里每次检查
          window.__webAutoPickerInjected，若为 false 说明页面已跳转，
          立即重注入脚本并恢复录制激活状态。
"""

import os
import sys

TARGET_FILE = os.path.join(os.path.dirname(__file__), "gui", "visual_picker_window.py")

# ── 改动 1：PickerThread.__init__ 增加状态标志 ──────────────────────────────
OLD_1 = """    def __init__(self, url: str = "about:blank"):
        super().__init__()
        self.url = url
        self._page = None
        self._stop = False
        self._last_picked = None"""

NEW_1 = """    def __init__(self, url: str = "about:blank"):
        super().__init__()
        self.url = url
        self._page = None
        self._stop = False
        self._last_picked = None
        self._recorder_should_be_active = False  # 跨页跳转时自动恢复录制状态"""

# ── 改动 2：PickerThread.run() 轮询循环加自动重注入逻辑 ─────────────────────
OLD_2 = """                    exit_req = self._page.run_js("return window.__pickerExitRequested || false;")
                    if exit_req:
                        self.picker_exited.emit()
                        break

                    picked = self._page.run_js("""

NEW_2 = """                    exit_req = self._page.run_js("return window.__pickerExitRequested || false;")
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

                    picked = self._page.run_js("""

# ── 改动 3：_toggle_record_mode 同步更新标志位 ──────────────────────────────
OLD_3 = """            try:
                self._picker_thread.run_js(
                    "window.__webAutoRecorderActive = true;"
                    "window.__webAutoPickerActive = false;"
                    "window.__pickerExitRequested = false;"
                    "window.__webAutoRecorderReset && window.__webAutoRecorderReset();"
                )
            except Exception:
                pass
            self._set_status(
                "🔴 录制中，您的浏览操作将自动转为步骤，完成后点击停止录制",
                "#d35400"
            )
        else:
            self._record_mode = False
            self.record_btn.setText("🎬 开始录制")
            self.record_btn.setStyleSheet("")
            try:
                self._picker_thread.run_js("window.__webAutoRecorderActive = false;")
            except Exception:
                pass"""

NEW_3 = """            try:
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
                pass"""


def apply(content, old, new, label):
    if old not in content:
        if new in content:
            print(f"  [跳过] {label}：已是最新版本")
            return content, False
        print(f"  [失败] {label}：找不到目标代码块，请检查文件")
        sys.exit(1)
    result = content.replace(old, new, 1)
    print(f"  [成功] {label}")
    return result, True


def main():
    if not os.path.exists(TARGET_FILE):
        print(f"[失败] 找不到目标文件: {TARGET_FILE}")
        sys.exit(1)

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    print("开始修改 gui/visual_picker_window.py ...")
    content, _ = apply(content, OLD_1, NEW_1, "PickerThread.__init__ 增加状态标志")
    content, _ = apply(content, OLD_2, NEW_2, "轮询循环加自动重注入逻辑")
    content, _ = apply(content, OLD_3, NEW_3, "_toggle_record_mode 同步标志位")

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print("\n[完成] gui/visual_picker_window.py 修复成功")
    print("  修复内容：")
    print("    1. PickerThread 新增 _recorder_should_be_active 标志")
    print("    2. 轮询循环每次检测脚本是否存在，跳转后自动重注入")
    print("    3. 开始/停止录制时同步更新标志，确保新页面能正确恢复录制状态")


if __name__ == "__main__":
    main()
