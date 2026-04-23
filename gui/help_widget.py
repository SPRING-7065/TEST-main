"""
使用帮助 Tab
内置图文说明，无需外部文档
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel,
    QFrame, QHBoxLayout, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class HelpWidget(QWidget):
    """使用帮助面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题
        header = QLabel("❓  使用帮助与快速上手指南")
        header.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#2c3e50; "
            "padding:16px 20px; background:white; "
            "border-bottom:2px solid #3498db;"
        )
        layout.addWidget(header)

        # 帮助内容标签页
        help_tabs = QTabWidget()
        help_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                font-size: 12px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background: #f0f2f5;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
                color: #2980b9;
            }
        """)

        help_tabs.addTab(self._build_quickstart_tab(), "🚀 快速上手")
        help_tabs.addTab(self._build_steps_tab(),      "🔧 步骤类型详解")
        help_tabs.addTab(self._build_variables_tab(),  "📅 时间变量说明")
        help_tabs.addTab(self._build_login_tab(),      "🔐 登录模板")
        help_tabs.addTab(self._build_pipeline_tab(),   "🔁 数据流转 (v1.3.0)")
        help_tabs.addTab(self._build_faq_tab(),        "❓ 常见问题")

        layout.addWidget(help_tabs, 1)

    # ─────────────────────────────────────────────
    # 各 Tab 内容
    # ─────────────────────────────────────────────

    def _build_quickstart_tab(self) -> QWidget:
        content = """
<div style="background:#fff3cd; padding:14px; border-radius:8px;
            border-left:5px solid #f0ad4e; margin:0 0 16px 0;">
<b style="font-size:14px; color:#856404;">🟢 前置依赖（必读）</b><br><br>
本程序<b>不再内置浏览器</b>，需要您的电脑已经安装 <b>Google Chrome</b>。
如果还没装，请到
<a href="https://www.google.cn/chrome/">https://www.google.cn/chrome/</a>
下载安装。<br><br>
<i>程序会自动调用系统已安装的 Chrome（标准安装路径），无需配置。</i>
</div>

<h2 style="color:#2980b9; margin-top:0;">🚀 5步快速上手</h2>

<div style="background:#eafaf1; padding:15px; border-radius:8px;
            border-left:5px solid #27ae60; margin:10px 0;">
<b style="font-size:14px;">① 新建任务</b><br><br>
点击主界面左上角的「➕ 新建任务」按钮，在弹出的对话框中填写
<b>任务名称</b>（例如：每日销售报表）和任务说明（可选）。
</div>

<div style="background:#eaf2ff; padding:15px; border-radius:8px;
            border-left:5px solid #3498db; margin:10px 0;">
<b style="font-size:14px;">② 配置操作步骤（核心）</b><br><br>
切换到「🔧 操作步骤」标签页，点击紫色的
<b>「🎯 可视化拾取（推荐）」</b>按钮。<br><br>
程序会同时弹出一个<b>真实浏览器窗口</b>和一个<b>配置面板</b>：<br>
&nbsp;&nbsp;1. 在配置面板的地址栏输入目标网页地址，点击「🚀 打开浏览器」<br>
&nbsp;&nbsp;2. 浏览器打开后，将鼠标移到网页上的目标元素（如输入框、按钮），
元素会<b>蓝色高亮</b>显示<br>
&nbsp;&nbsp;3. <b>左键单击</b>该元素，配置面板会自动填入该元素的定位信息<br>
&nbsp;&nbsp;4. 在配置面板选择步骤类型（点击/输入/下载等），填写步骤名称<br>
&nbsp;&nbsp;5. 点击「✅ 添加此步骤到任务」<br>
&nbsp;&nbsp;6. 重复以上操作，直到配置完所有步骤<br><br>
<i>💡 提示：页面跳转后如果高亮失效，点击「🔄 重新激活拾取」即可恢复</i>
</div>

<div style="background:#fef9e7; padding:15px; border-radius:8px;
            border-left:5px solid #f39c12; margin:10px 0;">
<b style="font-size:14px;">③ 配置定时计划（可选）</b><br><br>
切换到「⏰ 定时计划」标签页，勾选「启用定时自动执行」，
选择执行频率（每天/每周/每月）和具体时间。<br>
不配置定时计划也可以，手动点击「▶ 立即执行」随时触发。
</div>

<div style="background:#fdecea; padding:15px; border-radius:8px;
            border-left:5px solid #e74c3c; margin:10px 0;">
<b style="font-size:14px;">④ 保存任务</b><br><br>
点击对话框底部的「💾 保存任务」按钮，
任务会出现在主界面的任务列表中。
</div>

<div style="background:#f3e5f5; padding:15px; border-radius:8px;
            border-left:5px solid #8e44ad; margin:10px 0;">
<b style="font-size:14px;">⑤ 执行并查看结果</b><br><br>
点击任务卡片右侧的「▶ 立即执行」，程序会在<b>后台静默运行</b>
（不影响您使用电脑做其他事情）。<br>
切换到「📜 运行日志」标签页可以看到实时执行进度和结果。<br><br>
下载的文件保存在：<br>
<code style="background:#f0f0f0; padding:3px 6px; border-radius:3px;">
程序所在目录 / 下载数据库 / 今天日期 / 任务名_时间戳.xlsx
</code>
</div>

<h3 style="color:#2c3e50; margin-top:24px;">📋 典型场景：每天自动下载销售报表</h3>
<p>以「每天自动登录内网系统下载销售报表」为例，步骤链配置如下：</p>
<table border="1" cellpadding="8" cellspacing="0"
       style="border-collapse:collapse; width:100%; border-color:#e0e0e0; margin-top:8px;">
<tr style="background:#34495e; color:white;">
  <th style="width:40px;">序号</th>
  <th style="width:160px;">步骤类型</th>
  <th>配置内容</th>
</tr>
<tr style="background:#f8f9fa;">
  <td align="center">1</td>
  <td>🌐 打开网址</td>
  <td>https://内网地址/login</td>
</tr>
<tr>
  <td align="center">2</td>
  <td>⌨️ 输入文本</td>
  <td>点击用户名输入框 → 输入账号</td>
</tr>
<tr style="background:#f8f9fa;">
  <td align="center">3</td>
  <td>⌨️ 输入文本</td>
  <td>点击密码输入框 → 输入密码</td>
</tr>
<tr>
  <td align="center">4</td>
  <td>🖱️ 点击元素</td>
  <td>点击登录按钮</td>
</tr>
<tr style="background:#f8f9fa;">
  <td align="center">5</td>
  <td>⏱️ 等待秒数</td>
  <td>3（等待页面跳转完成）</td>
</tr>
<tr>
  <td align="center">6</td>
  <td>⌨️ 输入文本</td>
  <td>开始日期框 → 输入 <b>[TODAY-1]</b>（昨天）</td>
</tr>
<tr style="background:#f8f9fa;">
  <td align="center">7</td>
  <td>⌨️ 输入文本</td>
  <td>结束日期框 → 输入 <b>[TODAY]</b>（今天）</td>
</tr>
<tr>
  <td align="center">8</td>
  <td>🖱️ 点击元素</td>
  <td>点击查询按钮</td>
</tr>
<tr style="background:#f8f9fa;">
  <td align="center">9</td>
  <td>⏱️ 等待秒数</td>
  <td>5（等待数据加载完成）</td>
</tr>
<tr>
  <td align="center">10</td>
  <td>⬇️ 点击下载</td>
  <td>点击「导出Excel」按钮 → 文件自动保存</td>
</tr>
</table>
"""
        return self._make_scroll_tab(content)

    def _build_steps_tab(self) -> QWidget:
        content = """
<h2 style="color:#2980b9; margin-top:0;">🔧 步骤类型详细说明</h2>

<table border="1" cellpadding="10" cellspacing="0"
       style="border-collapse:collapse; width:100%; border-color:#ddd;">
<tr style="background:#2980b9; color:white;">
  <th style="width:150px;">步骤类型</th>
  <th style="width:200px;">用途</th>
  <th style="width:200px;">需要填写的内容</th>
  <th>使用示例</th>
</tr>
<tr style="background:#f8f9fa;">
  <td><b>🌐 打开网址</b></td>
  <td>让浏览器打开指定网页</td>
  <td>完整的网页地址（URL）</td>
  <td><code>https://www.example.com/login</code></td>
</tr>
<tr>
  <td><b>⌨️ 输入文本</b></td>
  <td>在输入框中输入内容（会先清空再输入）</td>
  <td>选择器（可视化拾取）+ 要输入的文字</td>
  <td>输入账号、密码、日期范围等</td>
</tr>
<tr style="background:#f8f9fa;">
  <td><b>🖱️ 点击元素</b></td>
  <td>点击按钮、链接、标签页等</td>
  <td>选择器（可视化拾取）</td>
  <td>点击登录按钮、查询按钮、Tab页</td>
</tr>
<tr>
  <td><b>⬇️ 点击下载</b></td>
  <td>点击下载按钮，程序自动拦截并保存文件</td>
  <td>选择器（可视化拾取）</td>
  <td>点击「导出Excel」「下载报表」按钮</td>
</tr>
<tr style="background:#f8f9fa;">
  <td><b>📋 下拉选择</b></td>
  <td>在下拉框（select元素）中选择选项</td>
  <td>选择器（可视化拾取）+ 选项文字</td>
  <td>选择地区「华东区」、类型「月报」</td>
</tr>
<tr>
  <td><b>⏱️ 等待秒数</b></td>
  <td>固定暂停等待，给页面加载时间</td>
  <td>等待的秒数（数字）</td>
  <td>填 <code>3</code> 表示等待3秒</td>
</tr>
<tr style="background:#f8f9fa;">
  <td><b>👁️ 等待元素出现</b></td>
  <td>智能等待，直到某元素出现才继续</td>
  <td>选择器（可视化拾取）</td>
  <td>等待「查询结果」表格出现后再下载</td>
</tr>
<tr>
  <td><b>📜 滚动页面</b></td>
  <td>滚动页面到指定位置</td>
  <td><code>bottom</code>=底部 / <code>top</code>=顶部 / 数字=像素</td>
  <td>填 <code>bottom</code> 滚动到页面底部</td>
</tr>
<tr style="background:#f8f9fa;">
  <td><b>🗑️ 清空输入框</b></td>
  <td>仅清空输入框内容，不输入新内容</td>
  <td>选择器（可视化拾取）</td>
  <td>清空日期输入框中的默认值</td>
</tr>
</table>

<h3 style="color:#2c3e50; margin-top:24px;">📌 关于「可选步骤」</h3>
<div style="background:#fef9e7; padding:12px; border-radius:6px; border-left:4px solid #f39c12;">
在手动编辑步骤时，可以勾选「<b>可选步骤（失败后不中断任务）</b>」。<br>
勾选后，如果该步骤执行失败（例如某个弹窗不一定每次都出现），
程序会记录警告但继续执行后续步骤，不会触发重试。<br>
适合用于：关闭广告弹窗、处理不确定是否出现的提示框等场景。
</div>

<h3 style="color:#2c3e50; margin-top:20px;">📌 关于CSS选择器</h3>
<div style="background:#eaf2ff; padding:12px; border-radius:6px; border-left:4px solid #3498db;">
CSS选择器是定位网页元素的"精确地址"。
<b>使用可视化拾取功能可以自动生成，无需手动编写。</b><br><br>
如果您想手动填写或微调，以下是常见格式参考：<br>
<table style="margin-top:8px; font-family:monospace;" cellpadding="5">
<tr><td><code>#loginBtn</code></td><td>→ 找ID为loginBtn的元素（最精确）</td></tr>
<tr><td><code>input[name="username"]</code></td><td>→ 找name属性为username的输入框</td></tr>
<tr><td><code>.btn-primary</code></td><td>→ 找class包含btn-primary的元素</td></tr>
<tr><td><code>button[type="submit"]</code></td><td>→ 找提交类型的按钮</td></tr>
<tr><td><code>input[placeholder="请输入账号"]</code></td><td>→ 通过提示文字定位</td></tr>
</table>
</div>
"""
        return self._make_scroll_tab(content)

    def _build_variables_tab(self) -> QWidget:
        content = """
<h2 style="color:#2980b9; margin-top:0;">📅 时间占位符使用说明</h2>

<p>在「⌨️ 输入文本」步骤的输入内容中，可以使用以下<b>时间占位符</b>。
程序执行时会自动替换为对应的日期，<b>无需每次手动修改日期</b>，
实现真正的全自动化。</p>

<table border="1" cellpadding="10" cellspacing="0"
       style="border-collapse:collapse; width:100%; border-color:#ddd;">
<tr style="background:#2980b9; color:white;">
  <th style="width:200px;">占位符</th>
  <th style="width:200px;">含义</th>
  <th>示例（假设今天是 2024-03-15）</th>
</tr>
<tr style="background:#f8f9fa;">
  <td><code style="font-size:14px; color:#8e44ad;">[TODAY]</code></td>
  <td>今天的日期</td>
  <td><b>2024-03-15</b></td>
</tr>
<tr>
  <td><code style="font-size:14px; color:#8e44ad;">[TODAY-1]</code></td>
  <td>昨天（往前推1天）</td>
  <td><b>2024-03-14</b></td>
</tr>
<tr style="background:#f8f9fa;">
  <td><code style="font-size:14px; color:#8e44ad;">[TODAY-7]</code></td>
  <td>7天前</td>
  <td><b>2024-03-08</b></td>
</tr>
<tr>
  <td><code style="font-size:14px; color:#8e44ad;">[TODAY-30]</code></td>
  <td>30天前（含周末，自然日）</td>
  <td><b>2024-02-14</b></td>
</tr>
<tr style="background:#f8f9fa;">
  <td><code style="font-size:14px; color:#8e44ad;">[TODAY+1]</code></td>
  <td>明天</td>
  <td><b>2024-03-16</b></td>
</tr>
<tr>
  <td><code style="font-size:14px; color:#8e44ad;">[YESTERDAY]</code></td>
  <td>昨天（同 [TODAY-1]）</td>
  <td><b>2024-03-14</b></td>
</tr>
<tr style="background:#f8f9fa;">
  <td><code style="font-size:14px; color:#8e44ad;">[MONTH_START]</code></td>
  <td>本月第一天</td>
  <td><b>2024-03-01</b></td>
</tr>
<tr>
  <td><code style="font-size:14px; color:#8e44ad;">[MONTH_END]</code></td>
  <td>本月最后一天</td>
  <td><b>2024-03-31</b></td>
</tr>
<tr style="background:#f8f9fa;">
  <td><code style="font-size:14px; color:#8e44ad;">[YEAR_START]</code></td>
  <td>今年第一天</td>
  <td><b>2024-01-01</b></td>
</tr>
<tr>
  <td><code style="font-size:14px; color:#8e44ad;">[NOW_TIMESTAMP]</code></td>
  <td>当前精确时间戳（用于文件命名）</td>
  <td><b>20240315_093022</b></td>
</tr>
</table>

<h3 style="color:#2c3e50; margin-top:24px;">💡 实际使用示例</h3>

<div style="background:#eafaf1; padding:14px; border-radius:8px;
            border-left:4px solid #27ae60; margin:10px 0;">
<b>场景一：查询昨天到今天的数据</b><br>
开始日期输入框 → 填写：<code style="color:#8e44ad;">[TODAY-1]</code><br>
结束日期输入框 → 填写：<code style="color:#8e44ad;">[TODAY]</code><br>
执行时自动替换为：<b>2024-03-14</b> 和 <b>2024-03-15</b>
</div>

<div style="background:#eaf2ff; padding:14px; border-radius:8px;
            border-left:4px solid #3498db; margin:10px 0;">
<b>场景二：查询本月全部数据</b><br>
开始日期输入框 → 填写：<code style="color:#8e44ad;">[MONTH_START]</code><br>
结束日期输入框 → 填写：<code style="color:#8e44ad;">[TODAY]</code><br>
每月1号执行时，自动替换为：<b>2024-03-01</b> 和 <b>2024-03-01</b>
</div>

<div style="background:#fef9e7; padding:14px; border-radius:8px;
            border-left:4px solid #f39c12; margin:10px 0;">
<b>场景三：网站要求 yyyy/MM/dd 格式</b><br>
在步骤配置的「日期格式」下拉框中选择 <b>yyyy/MM/dd</b>，<br>
则 <code style="color:#8e44ad;">[TODAY]</code> 会自动输出 <b>2024/03/15</b> 格式
</div>

<div style="background:#f3e5f5; padding:14px; border-radius:8px;
            border-left:4px solid #8e44ad; margin:10px 0;">
<b>场景四：网站要求带时分秒格式</b><br>
在步骤配置的「日期格式」下拉框中选择 <b>yyyy-MM-dd HH:mm:ss</b>，<br>
则 <code style="color:#8e44ad;">[TODAY-1]</code> 会自动输出 <b>2024-03-14 00:00:00</b>
</div>

<h3 style="color:#2c3e50; margin-top:24px;">📂 文件自动保存路径说明</h3>
<div style="background:#f8f9fa; padding:14px; border-radius:8px;
            border:1px solid #ddd; font-family:monospace; font-size:13px;">
程序所在目录/<br>
├── 网页自动取数助手.exe<br>
├── tasks.json &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;← 任务配置（自动生成）<br>
├── run_log.txt &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;← 运行日志（自动生成）<br>
└── 下载数据库/<br>
&nbsp;&nbsp;&nbsp;&nbsp;├── 2024-03-14/<br>
&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── 销售报表_20240314_090012.xlsx<br>
&nbsp;&nbsp;&nbsp;&nbsp;└── 2024-03-15/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;← 按执行日期自动创建<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── 销售报表_20240315_090008.xlsx &nbsp;← 任务名+时间戳防覆盖
</div>
"""
        return self._make_scroll_tab(content)

    def _build_login_tab(self) -> QWidget:
        content = """
<h2 style="color:#2980b9; margin-top:0;">🔐 登录模板（v1.2.0 新增）</h2>

<div style="background:#e8f8f5; padding:14px; border-radius:8px;
            border-left:5px solid #1abc9c; margin:10px 0;">
<b>什么是登录模板？</b><br><br>
OA / 内网系统的登录态通常 8-24 小时就过期，每次执行任务都要手动登录非常烦。
登录模板让你<b>录制一次完整的登录流程</b>（包括"OA 登录"按钮点击、跳转、表单填充），
任务执行时自动检测：<br>
&nbsp;&nbsp;• 已登录 → 直接执行业务步骤<br>
&nbsp;&nbsp;• 未登录 → 自动回放登录流程，再执行业务<br><br>
密码用 Windows Credential Manager / Mac Keychain 加密存储，<b>不进 JSON 文件、不进日志</b>。
</div>

<h3 style="color:#2c3e50; margin-top:24px;">📋 配置流程（5 步）</h3>

<div style="background:#eaf2ff; padding:15px; border-radius:8px;
            border-left:5px solid #3498db; margin:10px 0;">
<b>① 切到「🔐 登录」Tab，勾选「启用登录模板」</b>
</div>

<div style="background:#fef9e7; padding:15px; border-radius:8px;
            border-left:5px solid #f39c12; margin:10px 0;">
<b>② 点「📹 录制登录流程」</b><br><br>
浏览器自动打开并进入录制模式，请走一遍真实登录流程：<br>
&nbsp;&nbsp;• 如果你的 OA 需要先点"OA 登录 / SSO 登录"按钮 → 录制器会自动捕获<br>
&nbsp;&nbsp;• 点击跳转到登录页 → 录制器会自动捕获<br>
&nbsp;&nbsp;• 填用户名 → 真实输入即可（注意：录制器会捕获明文）<br>
&nbsp;&nbsp;• 填密码 → 真实输入即可<br>
&nbsp;&nbsp;• 点登录按钮 → 录制器会自动捕获<br><br>
<b>关键：</b>登录成功后回到控制面板：<br>
&nbsp;&nbsp;1. 在录制列表选中"输入用户名"那一步 → 点「🔑 替换为 ${username}」<br>
&nbsp;&nbsp;2. 在录制列表选中"输入密码"那一步 → 点「🔒 替换为 ${password}」<br>
&nbsp;&nbsp;3. 点「💾 保存为登录模板」回到编辑器
</div>

<div style="background:#f3e5f5; padding:15px; border-radius:8px;
            border-left:5px solid #8e44ad; margin:10px 0;">
<b>③ 点「🎯 拾取」选择「已登录标志元素」</b><br><br>
浏览器会再次打开。请<b>先手动登录</b>（任意账号），然后<b>点击一个登录后才会出现的元素</b>，
比如顶部右上角的"欢迎，张三"、用户头像、退出按钮等。<br><br>
任务执行时程序就靠这个元素判断"是否已经登录了"。
</div>

<div style="background:#fdecea; padding:15px; border-radius:8px;
            border-left:5px solid #e74c3c; margin:10px 0;">
<b>④ 填用户名密码，点「💾 保存凭据到密钥库」</b><br><br>
密码会通过系统密钥库（Windows: Credential Manager；Mac: Keychain）加密保存，
<b>不会写入 tasks.json</b>，也不会出现在任何日志中。<br><br>
保存成功后下方会显示 ✅ 提示。
</div>

<div style="background:#eafaf1; padding:15px; border-radius:8px;
            border-left:5px solid #27ae60; margin:10px 0;">
<b>⑤ 保存任务，立即执行验证</b><br><br>
首次执行：会看到"🔐 检测到未登录，开始回放登录模板"→ 登录成功<br>
后续执行：会看到"✅ 检测到已登录（cookie 复用），跳过登录模板"
</div>

<h3 style="color:#2c3e50; margin-top:24px;">🔒 安全说明</h3>
<ul style="color:#34495e; line-height:1.8;">
<li>密码不存在任务 JSON 里，分享任务文件时密码不会泄露给同事</li>
<li>密码不出现在运行日志中（占位符 <code>${password}</code> 替换发生在执行那一刻，立即销毁）</li>
<li>密钥库 per-user 绑定：把同一台电脑的程序拷给别人用，对方无法解出密码</li>
<li>删除任务时凭据自动清除</li>
</ul>

<h3 style="color:#2c3e50; margin-top:24px;">⚠️ 已知限制</h3>
<ul style="color:#34495e; line-height:1.8;">
<li><b>不支持图形验证码 / 动态短信码</b>：这是 SSO 系统本身的限制，无法自动化。
带验证码的 OA 可能要每天手动登一次（cookie 复用至少能撑 8-24 小时）</li>
<li><b>不支持人脸 / 指纹</b>：同上</li>
<li>选择器失效（页面改版）需要重新录制登录模板</li>
</ul>
"""
        return self._make_scroll_tab(content)

    def _build_pipeline_tab(self) -> QWidget:
        content = """
<h2 style="color:#2980b9; margin-top:0;">🔁 数据流转 + Excel/AI 集成（v1.3.0 新增）</h2>

<div style="background:#e8f8f5; padding:14px; border-radius:8px;
            border-left:5px solid #1abc9c; margin:10px 0;">
v1.3.0 把工具从"网页自动化"升级成"<b>步骤间能传数据</b>的小流水线"，
覆盖三类典型场景：<br>
&nbsp;&nbsp;• <b>每日简报</b>：抓 N 个网站 → 拼成文本 → 投喂 AI 总结<br>
&nbsp;&nbsp;• <b>跨系统搬运</b>：从 OA 下载文件 → 上传到 AI 站<br>
&nbsp;&nbsp;• <b>舆情监控</b>：抓评论 → AI 情感分析 → 追加到 Excel 归档<br><br>
导入 <b>samples/data_pipeline_demo.json</b> 可以看到两个示例任务。
</div>

<h3 style="color:#2c3e50; margin-top:24px;">📌 4 个新步骤类型</h3>

<div style="background:#eaf2ff; padding:15px; border-radius:8px;
            border-left:5px solid #3498db; margin:10px 0;">
<b>📤 上传文件 (UPLOAD_FILE)</b><br><br>
向页面上的 <code>&lt;input type="file"&gt;</code> 上传文件。<br><br>
关键能力：选择器对准 AI 站点的「📎 附件」按钮即可，
引擎会自动在按钮附近查找隐藏的 input[type=file]，
ChatGPT/Claude/Kimi 等都能这么过。<br><br>
文件路径支持变量：<code>${last_download}</code> 直接接续上一步下载的文件。
</div>

<div style="background:#fef9e7; padding:15px; border-radius:8px;
            border-left:5px solid #f39c12; margin:10px 0;">
<b>🔎 抽取元素到变量 (EXTRACT_DOM)</b><br><br>
把页面元素文字 / 属性抽出来，存成命名变量供后续步骤插值使用。<br><br>
&nbsp;&nbsp;• <b>变量名</b>：例如 <code>headlines</code>，后续用 <code>${headlines}</code> 引用<br>
&nbsp;&nbsp;• <b>属性</b>：默认 innerText；也可选 href / src / value / 自定义属性<br>
&nbsp;&nbsp;• <b>取全部并拼接</b>：勾选后会抓所有匹配元素（舆情、新闻列表场景），用分隔符拼成一段
</div>

<div style="background:#f3e5f5; padding:15px; border-radius:8px;
            border-left:5px solid #8e44ad; margin:10px 0;">
<b>📊 读取 Excel (READ_EXCEL)</b><br><br>
把 xlsx 文件的内容读成文本变量，喂给 AI 提示框。<br><br>
&nbsp;&nbsp;• <b>范围</b>：<code>all</code>=整表 / <code>A</code>=A列 / <code>3</code>=第3行 / <code>B2</code>=单元格 / <code>A1:C10</code>=区域<br>
&nbsp;&nbsp;• <b>格式</b>：Markdown 表格（AI 友好，推荐） / CSV / JSON<br><br>
也可以直接用 UPLOAD_FILE 把 xlsx 整文件投给 AI（Claude/Kimi/ChatGPT 都能解析 xlsx），
看你想让 AI 看"原文件"还是"已结构化的文本"。
</div>

<div style="background:#fdecea; padding:15px; border-radius:8px;
            border-left:5px solid #e74c3c; margin:10px 0;">
<b>📝 追加 Excel (APPEND_EXCEL)</b><br><br>
把变量插值后的列映射追加为新行（日志归档型）。<br><br>
&nbsp;&nbsp;• <b>列映射</b>：每行配置「列名 → 值模板」，值模板里可以用 <code>${变量}</code> 和 <code>[NOW]</code><br>
&nbsp;&nbsp;• <b>自动建表头</b>：文件/Sheet 不存在时按列映射顺序自动创建<br>
&nbsp;&nbsp;• <b>展开列表变量</b>：如果想把 EXTRACT_DOM 抓到的多元素分别写成多行，填变量名 + 分隔符，行内用 <code>${item}</code> 引用当前项
</div>

<h3 style="color:#2c3e50; margin-top:24px;">💡 自动追踪的下载变量</h3>

<div style="background:#eaf2ff; padding:15px; border-radius:8px;
            border-left:5px solid #3498db; margin:10px 0;">
任意 DOWNLOAD_CLICK 步骤完成后，引擎自动维护两类变量：<br><br>
&nbsp;&nbsp;• <code>${last_download}</code> — 最近一次下载文件的绝对路径<br>
&nbsp;&nbsp;• <code>${download_1}</code>、<code>${download_2}</code>… — 按下载顺序编号<br><br>
配合 UPLOAD_FILE 的 <code>${last_download}</code>，可以无缝完成"下载→上传"链路。
</div>

<h3 style="color:#2c3e50; margin-top:24px;">🔗 典型流水线示例</h3>

<div style="background:#f8f9fa; padding:15px; border-radius:8px;
            border:1px solid #dee2e6; margin:10px 0; font-family:Consolas,monospace;
            font-size:12px; color:#2c3e50;">
<b>每日简报：</b><br>
OPEN_URL（新闻站）<br>
&nbsp;&nbsp;→ EXTRACT_DOM（标题列表，concat_all=true，存到 ${headlines}）<br>
&nbsp;&nbsp;→ OPEN_URL（AI 站）<br>
&nbsp;&nbsp;→ INPUT（提示词 ${headlines} 请帮我总结）<br><br>
<b>跨系统搬运：</b><br>
OPEN_URL（OA 下载页）<br>
&nbsp;&nbsp;→ DOWNLOAD_CLICK（${last_download} 自动产生）<br>
&nbsp;&nbsp;→ OPEN_URL（AI 站）<br>
&nbsp;&nbsp;→ UPLOAD_FILE（${last_download}）<br>
&nbsp;&nbsp;→ INPUT（请总结这份文件）<br><br>
<b>舆情归档：</b><br>
OPEN_URL（评论页）<br>
&nbsp;&nbsp;→ EXTRACT_DOM（评论列表，存到 ${comments}）<br>
&nbsp;&nbsp;→ OPEN_URL（AI 站）→ INPUT（${comments} 请打分）<br>
&nbsp;&nbsp;→ EXTRACT_DOM（AI 回复，存到 ${ai_score}）<br>
&nbsp;&nbsp;→ APPEND_EXCEL（[NOW] / 来源 / ${comments} / ${ai_score}）
</div>
"""
        return self._make_scroll_tab(content)

    def _build_faq_tab(self) -> QWidget:
        content = """
<h2 style="color:#2980b9; margin-top:0;">❓ 常见问题解答</h2>

<div style="background:#fdecea; padding:15px; border-radius:8px;
            border-left:5px solid #e74c3c; margin:12px 0;">
<b style="font-size:14px;">Q：程序执行时会弹出浏览器窗口吗？会影响我用电脑吗？</b><br><br>
A：<b>完全不会影响！</b><br>
任务执行阶段使用完全隐藏的后台浏览器（无头模式），
不会出现任何窗口，不会移动您的鼠标，不会抢占键盘焦点。
您可以正常使用电脑看视频、打字、开会。<br><br>
<i>💡 只有在「配置步骤」时点击「可视化拾取」才会弹出可见浏览器，
那是专门为配置阶段设计的，配置完成后关闭即可。</i>
</div>

<div style="background:#eafaf1; padding:15px; border-radius:8px;
            border-left:5px solid #27ae60; margin:12px 0;">
<b style="font-size:14px;">Q：关闭程序窗口后，定时任务还会执行吗？</b><br><br>
A：点击窗口的「×」关闭按钮时，程序会<b>最小化到系统托盘</b>
（屏幕右下角时钟旁边的小图标区域），定时任务继续在后台运行。<br>
双击托盘图标可重新显示主窗口。<br><br>
只有在托盘图标上<b>右键 → 退出程序</b>，才会真正停止所有任务并退出。
</div>

<div style="background:#eaf2ff; padding:15px; border-radius:8px;
            border-left:5px solid #3498db; margin:12px 0;">
<b style="font-size:14px;">Q：可视化拾取时，页面跳转后高亮功能失效了怎么办？</b><br><br>
A：网页跳转（如点击登录后跳转到主页）后，之前注入的拾取脚本会失效，
高亮不再出现。<br>
解决方法：点击配置面板上的
<b>「🔄 重新激活拾取」</b>按钮即可重新激活高亮功能，
然后继续点击元素配置步骤。
</div>

<div style="background:#fef9e7; padding:15px; border-radius:8px;
            border-left:5px solid #f39c12; margin:12px 0;">
<b style="font-size:14px;">Q：任务执行失败，日志说"找不到指定的按钮或输入框"怎么办？</b><br><br>
A：这通常是因为网页结构发生了变化，导致之前配置的选择器失效。<br>
解决步骤：<br>
&nbsp;&nbsp;① 点击任务卡片的「✏️ 编辑」按钮<br>
&nbsp;&nbsp;② 切换到「🔧 操作步骤」标签页<br>
&nbsp;&nbsp;③ 双击失效的步骤，点击「重新拾取」<br>
&nbsp;&nbsp;④ 在浏览器中重新点击该元素<br>
&nbsp;&nbsp;⑤ 保存任务后重新执行
</div>

<div style="background:#f3e5f5; padding:15px; border-radius:8px;
            border-left:5px solid #8e44ad; margin:12px 0;">
<b style="font-size:14px;">Q：下载的文件在哪里？</b><br><br>
A：默认保存在<b>程序所在目录</b>的「下载数据库」文件夹中，
按日期自动分子文件夹，文件名包含任务名和时间戳。<br><br>
也可以在任务编辑界面的「高级设置 → 自定义保存目录」中指定其他路径。<br><br>
每次执行成功后，运行日志中会显示完整的文件保存路径，
点击「📂 打开日志文件」可查看历史记录。
</div>

<div style="background:#e8f8f5; padding:15px; border-radius:8px;
            border-left:5px solid #1abc9c; margin:12px 0;">
<b style="font-size:14px;">Q：网站有验证码怎么办？</b><br><br>
A：目前版本不支持自动识别验证码。建议以下方案：<br>
&nbsp;&nbsp;① <b>记住登录（Cookie方案）</b>：在浏览器中手动登录一次并勾选「记住我」，
之后自动化时直接跳过登录步骤，从目标页面开始配置<br>
&nbsp;&nbsp;② <b>内网系统</b>：很多内网系统不需要验证码，可直接配置账号密码步骤<br>
&nbsp;&nbsp;③ <b>IP白名单</b>：联系系统管理员将本机IP加入白名单，跳过验证码
</div>

<div style="background:#fdecea; padding:15px; border-radius:8px;
            border-left:5px solid #e74c3c; margin:12px 0;">
<b style="font-size:14px;">Q：任务一直超时失败，提示"等待超过120秒"怎么办？</b><br><br>
A：可以尝试以下方法：<br>
&nbsp;&nbsp;① 编辑任务 → 高级设置 → 将「每步超时时间」从120秒增大到180或300秒<br>
&nbsp;&nbsp;② 在关键步骤之间增加「⏱️ 等待秒数」步骤，给页面更多加载时间<br>
&nbsp;&nbsp;③ 检查网络是否正常，目标网站是否可以正常访问<br>
&nbsp;&nbsp;④ 查看「📜 运行日志」中的详细错误信息，确认是哪个步骤超时
</div>

<div style="background:#eaf2ff; padding:15px; border-radius:8px;
            border-left:5px solid #3498db; margin:12px 0;">
<b style="font-size:14px;">Q：如何让程序开机自动启动？</b><br><br>
A：右键点击程序的 .exe 文件 → 发送到 → 桌面快捷方式。<br>
然后按 <b>Win+R</b>，输入 <code>shell:startup</code> 回车，
将桌面快捷方式复制到打开的文件夹中即可。<br>
这样每次开机后程序会自动启动并在托盘运行，定时任务自动执行。
</div>

<div style="background:#fef9e7; padding:15px; border-radius:8px;
            border-left:5px solid #f39c12; margin:12px 0;">
<b style="font-size:14px;">Q：多个任务同时执行会不会冲突？</b><br><br>
A：每个任务使用<b>独立的浏览器用户配置目录</b>（<code>browser_cache/{任务ID}/</code>），
互不干扰，可以同时执行多个任务。但请注意：同一个任务同一时间只会运行一个实例，
如果上一次还没执行完，调度器不会重复触发。<br><br>
全局<b>并发上限</b>由「⚙️ 设置」Tab 控制，默认 2 个，详见下一条。
</div>

<div style="background:#eaf2ff; padding:15px; border-radius:8px;
            border-left:5px solid #3498db; margin:12px 0;">
<b style="font-size:14px;">Q：并发执行多少个任务比较合适？</b><br><br>
A：到「⚙️ 设置」Tab 调整「同时最多执行任务数」。每个任务约占
<b>300-500MB 内存 + 1 个 CPU 核心</b>。粗略对应关系：<br>
&nbsp;&nbsp;• <b>4-8GB 内存 / 老旧 CPU</b>：建议 1<br>
&nbsp;&nbsp;• <b>8-16GB / i5-i7</b>：默认 2 即可<br>
&nbsp;&nbsp;• <b>16GB / i7-7700 这一档</b>：3-4 是甜蜜点<br>
&nbsp;&nbsp;• <b>32GB+ / i9</b>：5+<br>
集成显卡（如 HD 630）超过 4 个浏览器并发可能出现渲染白屏，请适度降低。
</div>

<div style="background:#e8f8f5; padding:15px; border-radius:8px;
            border-left:5px solid #1abc9c; margin:12px 0;">
<b style="font-size:14px;">Q：登录态怎么保持？每次都要重新登录吗？</b><br><br>
A：当前版本每个任务的 cookie / localStorage 会持久化在
<code>browser_cache/{任务ID}/</code> 目录中，<b>同一个任务下次执行会复用登录态</b>，
不需要每次重新登录。<br><br>
但 OA / SSO 系统通常会有<b>会话过期</b>（一般 8-24 小时一次），
过期后还是要重新登录一次。<br><br>
<i>📌 下个版本（v1.2.0）将支持「登录模板」——录制一次登录流程后，
任务执行时自动检测登录状态、自动回放登录动作（密码用系统密钥库加密保存）。</i>
</div>

<div style="background:#fdecea; padding:15px; border-radius:8px;
            border-left:5px solid #e74c3c; margin:12px 0;">
<b style="font-size:14px;">Q：调试模式打开浏览器后是空白的（白屏），怎么办？</b><br><br>
A：本程序使用您系统已安装的 Chrome，正常情况下不会白屏。
如果遇到，多半是 <b>企业终端管控软件 / 杀毒软件</b> 拦截了浏览器进程的
某些子进程或网络访问，常见于公司发的电脑。<br><br>
<b>排查步骤：</b><br>
&nbsp;&nbsp;① 浏览器地址栏访问 <code>chrome://gpu</code>，
看 "Compositing" 一行：是绿字 → 渲染没问题；红字 → 显卡/驱动问题<br>
&nbsp;&nbsp;② 直接打开 Chrome 访问几个普通网站
（百度、example.com）和你的内网，看是否都能正常打开<br>
&nbsp;&nbsp;③ 如果访问外网被重定向到一个无 logo 的"您被禁止访问互联网"页，
基本就是公司管控，需要联系 IT 加入白名单<br>
&nbsp;&nbsp;④ 排除杀毒软件：临时关掉 360 / 火绒 / 腾讯电脑管家测试
</div>
"""
        return self._make_scroll_tab(content)

    # ─────────────────────────────────────────────
    # 工具方法
    # ─────────────────────────────────────────────
    def _make_scroll_tab(self, html_content: str) -> QWidget:
        """创建带滚动条的帮助内容页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: white; }
            QScrollBar:vertical {
                width: 8px;
                background: #f0f0f0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #bbb;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #999; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: white;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(28, 20, 28, 28)
        content_layout.setSpacing(0)

        label = QLabel(html_content)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                line-height: 1.6;
                color: #2c3e50;
                background: white;
            }
        """)
        label.setOpenExternalLinks(True)
        content_layout.addWidget(label)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return widget