"""
修复 Bug5（续）：Vue/React 框架输入框无法输入
根本原因：page.run_js(js, element, value) 底层走 Runtime.evaluate，
          ChromiumElement 对象无法作为 JS 参数正确传入，
          导致 arguments[0] 拿不到 DOM 元素，框架事件触发失败。
修复方法：改用 element.run_js()，底层走 Runtime.callFunctionOn，
          'this' 直接绑定到 DOM 元素，同时兼容 textarea 元素。
"""

import os
import sys

TARGET_FILE = os.path.join(os.path.dirname(__file__), "core", "engine.py")

OLD_BLOCK = '''        elif step_type == StepType.INPUT:
            element = self._find_element(selector, step.selector_type, timeout)
            # 先尝试原生clear+input
            element.clear()
            time.sleep(0.2)

            # 对Vue/React等框架，普通input()不触发框架事件
            # 改用：点击聚焦 → JS设置value → 触发input/change事件
            try:
                element.click()
                time.sleep(0.1)
                # 通过JS设置value并触发框架能识别的事件
                # 使用arguments[1]传递value参数，避免字符串转义问题
                self._page.run_js("""
                    var el = arguments[0];
                    var value = arguments[1];
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeInputValueSetter.call(el, value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """, element, value)
                time.sleep(0.2)
                # 验证是否输入成功
                actual = self._page.run_js(
                    "return arguments[0].value", element
                )
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
            time.sleep(0.3)'''

NEW_BLOCK = '''        elif step_type == StepType.INPUT:
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
            time.sleep(0.3)'''


def main():
    # 1. 读取目标文件
    if not os.path.exists(TARGET_FILE):
        print(f"[失败] 找不到目标文件: {TARGET_FILE}")
        sys.exit(1)

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. 确认旧代码存在
    if OLD_BLOCK not in content:
        if NEW_BLOCK in content:
            print("[警告] 目标代码块已是最新版本，无需修改")
        else:
            print("[失败] 找不到预期的代码块，可能文件已被修改，请检查 core/engine.py")
        sys.exit(1)

    # 3. 替换
    new_content = content.replace(OLD_BLOCK, NEW_BLOCK, 1)

    if new_content == content:
        print("[失败] 替换未生效，内容未发生变化")
        sys.exit(1)

    # 4. 写回
    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("[成功] core/engine.py 已更新")
    print("       修复内容：")
    print("         1. page.run_js(js, element, value) → element.run_js(js, value)")
    print("            'this' 直接指向 DOM 元素，框架事件可正确触发")
    print("         2. 验证读值改用 element.run_js('return this.value')")
    print("         3. 同时兼容 textarea 元素（HTMLTextAreaElement.prototype）")


if __name__ == "__main__":
    main()
