# 网页自动取数助手 - 项目交接文档

给新Claude：请完整阅读本文档，再结合用户提供的all_project_code.py掌握项目全貌。
读完后主动总结你的理解，准备好回答用户问题。

---

## 一、项目定位

面向非技术用户的Windows桌面自动化工具。
用户通过可视化界面配置操作步骤链，程序在后台自动驱动浏览器完成
登录->填表->点击->下载文件的重复工作，支持定时调度。

核心设计原则：
- 零依赖：用户电脑无需安装Python/Node/任何运行库，打包exe直接运行
- 不抢鼠标：浏览器通过CDP协议控制，物理鼠标完全不受影响
- 人话日志：所有报错翻译为中文，不暴露技术异常

---

## 二、技术栈

GUI：PySide6（Qt6），信号槽跨线程通信
浏览器自动化：DrissionPage（CDP协议，不模拟鼠标）
任务调度：纯threading轮询调度器（非APScheduler）
数据持久化：JSON文件（tasks.json存任务配置）
打包：PyInstaller + GitHub Actions双端自动构建
开发环境：GitHub Codespaces（用户本地无Python，全用云端开发）
仓库地址：github.com/SPRING-7065/TEST（私有仓库）

---

## 三、文件结构

```
main.py                       程序入口，初始化Qt应用
build.spec                    PyInstaller打包配置
check_syntax.py               语法检查脚本
download_chromium.py          打包时复制Chrome到输出目录
gen_icon.py                   生成程序图标
package_output.py             打包后压缩zip

core/
  engine.py                   后台执行引擎（最核心）
  scheduler.py                定时任务调度器（threading轮询）
  variable_parser.py          时间占位符解析（[TODAY-X]等）
  file_manager.py             下载路径和文件命名管理
  logger.py                   日志系统（异常中文翻译）

注意：原 download_chromium.py（便携 Chromium 下载）已废弃移除，
     程序改为使用用户机器上预装的系统 Chrome。

gui/
  main_window.py              主窗口（导航/日志面板/任务中心）
  task_editor_dialog.py       任务编辑对话框（步骤链配置）
  task_list_widget.py         任务卡片列表（进度条/截图预览）
  visual_picker_window.py     可视化元素拾取窗口（核心难点）
  help_widget.py              内置帮助文档Tab

models/
  task.py                     Task/ScheduleConfig数据模型
  step.py                     Step数据模型（StepType枚举）

storage/
  task_store.py               tasks.json的读写封装

.github/workflows/
  build_windows.yml           GitHub Actions自动打包流程
```

---

## 四、核心流程

配置阶段：
  打开程序 -> 新建任务 -> 可视化拾取或录制步骤 -> 保存任务

执行阶段（两种模式）：
  后台静默模式：headless=True，任务卡片显示进度条+截图预览（每4秒）
  调试模式：headless=False，浏览器窗口可见，实时观察执行过程

文件保存路径：
  程序目录/下载数据库/YYYY-MM-DD/任务名_时间戳.xlsx

数据流：
  tasks.json -> Task对象 -> ExecutionEngine -> DrissionPage -> 文件系统
  日志：logger.py -> LogSignalBridge(Qt信号) -> GUI文本框 + run_log.txt

---

## 五、已实现功能清单

可视化元素拾取：鼠标悬停高亮，左键单击自动生成CSS选择器
录制模式：自动记录点击/输入/下拉选择操作，转为步骤配置
多任务管理：增删改查，卡片式UI，支持拖拽排序步骤
定时调度：每天/每周/每月/单次，轮询间隔15秒
后台静默执行：headless模式，不干扰用户使用电脑
调试模式：浏览器窗口可见，实时观察执行过程
截图预览：执行中每4秒截图，显示在任务卡片上，可点击放大
步骤进度条：显示当前步骤/总步骤数
持久化浏览器缓存：browser_cache目录，加速重复访问，保留Cookie
时间占位符：[TODAY][TODAY-1][TODAY-7][MONTH_START][MONTH_END]等
防覆盖文件命名：任务名_时间戳.扩展名
任务导入导出：JSON格式，可分享给别人
系统驻留：关闭窗口不退出，后台继续运行定时任务
中文人话日志：异常自动翻译，不暴露技术细节
超时重试：每步120秒超时，最多3次重试

---

## 六、已修复Bug记录

### Bug1：scheduler.py TaskScheduler类缺失
症状：ImportError: cannot import name TaskScheduler
原因：打包时pyc文件不完整，APScheduler依赖问题
修复：重写为纯threading轮询调度器，彻底去除APScheduler依赖

### Bug2：visual_picker_window.py 按钮点击无响应
症状：点击可视化拾取按钮没有任何响应，窗口打不开
原因：_setup_ui()方法结尾错误，info_label在__init__里直接引用
      导致NameError，整个窗口初始化静默失败
修复：完整重写visual_picker_window.py，修正方法结构

### Bug3：GitHub Actions编码错误
症状：UnicodeEncodeError: charmap codec can't encode characters
原因：Windows runner默认cp1252编码，yml嵌套中文Python代码报错
修复：将所有Python逻辑抽取为独立.py文件，yml只用cmd调用

### Bug4：打包后_internal目录缺少core/gui等子文件夹
症状：运行exe报各种ImportError，找不到模块
原因：build.spec配置问题，模块被并入base_library.zip
修复：重写build.spec，明确hiddenimports列表，指定COLLECT输出

### Bug5：Vue/React框架输入框无法输入（修复两次）
症状：调试模式下看不到输入操作，登录失败，后续页面空白
原因（第一次）：DrissionPage的element.input()不触发Vue/React响应式事件
修复（第一次）：改用JS的nativeInputValueSetter+dispatchEvent触发框架事件
原因（第二次）：page.run_js(js, element, value)底层走Runtime.evaluate，
               ChromiumElement对象无法作为JS参数正确传入，
               arguments[0]拿不到DOM元素，框架事件实际未触发
修复（第二次）：改用element.run_js(js, value)，底层走Runtime.callFunctionOn，
               'this'直接绑定到DOM元素，同时兼容textarea元素
               （HTMLTextAreaElement.prototype）
状态：已修复

### Bug6：SPA单页应用白屏
症状：打开URL后页面持续空白，不加载内容
原因：readyState=complete时JS还未渲染完，程序误判为加载完成
修复：增加SPA等待逻辑，检测body子元素数量>1才继续

### Bug7：录制时页面跳转后操作不被录制
症状：录制登录页后跳转到主页，主页的所有操作丢失，步骤链不完整
原因：PICKER_JS只存在于注入时的页面，页面跳转后新document不含脚本，
     PickerThread轮询的window.__webAutoRecorderGetEvents是undefined
修复：PickerThread轮询循环每次检查window.__webAutoPickerInjected，
     若为false说明页面已跳转，立即重注入脚本并恢复录制激活状态
     新增_recorder_should_be_active标志跟踪当前是否处于录制中
状态：已修复

### Bug8：macOS深色模式下文字与背景同色（不可见）
症状：程序在macOS深色模式下打开，文字和背景同色，选中才能看清
原因：所有setStyleSheet写死浅色背景，但macOS深色模式下Qt把
     文字色自动改为白色以适应系统主题，导致白字白底
     Windows不受影响（Windows Qt默认样式不跟随系统深色模式改文字色）
修复：main.py中强制使用Fusion样式+写死浅色调色板，
     文字色固定为深色，不再随系统主题变化
状态：已修复（仅改main.py，不动任何GUI文件）

### Bug9：启动时log_text AttributeError
症状：启动日志出现AttributeError: 'MainWindow' object has no attribute 'log_text'
原因：日志信号在__init__第49行就连接了_append_log_to_gui，
     但log_text在第201行的_setup_ui()才创建，调度器在UI初始化前
     可能触发日志导致访问不存在的属性
修复：_append_log_to_gui开头加hasattr(self, 'log_text')守卫
状态：已修复

### Bug10：macOS/Linux下浏览器无法启动（WebSocketBadStatusException）
症状：执行任务时报WebSocketBadStatusException，连打开网页都失败
原因：get_chromium_path()只有Windows路径候选列表，
     Mac/Linux返回None，DrissionPage找不到浏览器
修复：engine.py的get_chromium_path()补充macOS和Linux路径：
     macOS: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
     Linux: /usr/bin/google-chrome 等
     visual_picker_window.py的PickerThread也同步使用get_chromium_path()
     macOS/Linux 仍带 --no-sandbox + --disable-dev-shm-usage（容器/CI 场景）
状态：已修复

### Bug11：Windows 调试模式白屏（多次误诊后定性）
症状：Windows 公司电脑运行打包版，调试模式浏览器窗口全白，
     顶部出现"unsupported command-line flag: --no-sandbox"警告条
误诊历史：先后判断为 GPU 沙箱失败、SwiftShader 缺失、缓存毒化等，
     一路堆 --no-sandbox/--disable-gpu-sandbox/--use-angle=swiftshader/
     --disable-gpu-compositing/--enable-unsafe-swiftshader 等 flag，
     问题反而加重。
真正根因：通过 chrome://gpu 看到 Compositing 绿字（GPU 完全正常），
     再直接双击便携 chrome.exe 测试外网全拦截、内网部分白屏，
     而同机器系统 Chrome 完全正常 → 公司电脑的企业终端管控
     按二进制白名单工作，便携 Chromium 不在白名单 → 网络静默拦截。
处置：1) 完全移除便携 Chromium 下载/打包链路（download_chromium.py
     删除，CI 不再下载，package_output.py 不再复制 browser/）
     2) get_chromium_path() 改为只查系统 Chrome，找不到时抛中文异常
     3) 回滚所有 GPU/sandbox 相关 flag（包括顶部警告条的元凶 --no-sandbox）
     4) README 增加"前置依赖：Google Chrome"段
教训：以后遇到"特定二进制白屏/网络异常"先用 chrome://gpu 自检 GPU、
     用同机器其他浏览器对比网络，再判断是不是企业管控/AV 干扰，
     不要一上来就猜 flag。
状态：已修复

---

## 七、打包流程

1. 在Codespaces修改代码
2. git add . && git commit -m "描述" && git push
3. GitHub Actions自动触发打包（约15-20分钟）
4. Actions页面 -> 对应运行记录 -> Artifacts -> 下载zip
5. 解压后双击WebAutoDownloader.exe运行

注意事项：
- 输出目录名必须是WebAutoDownloader（英文），避免中文路径问题
- 用户Windows电脑无法安装Python，所有开发在Codespaces运行
- 下载Artifact速度慢，可用ghfast.top镜像加速

---

## 八、Mac本地调试方法（开发用）

项目根目录已有.venv虚拟环境，直接用其中的python3运行：
```bash
cd ~/Downloads/TEST-main
.venv/bin/python3 main.py
```

重启程序：
```bash
pkill -f "main.py" 2>/dev/null; .venv/bin/python3 main.py
```

依赖：PySide6、DrissionPage（已装在.venv中）
注意：Mac上Microsoft YaHei字体缺失提示和托盘图标提示均可忽略，不影响功能

---

## 九、给新Claude的工作规范

修改代码时：
  1. 永远用Python脚本(apply_changes.py)方式修改文件
     不要让用户粘贴大段代码到terminal，长度限制会卡住
  2. 脚本末尾必须打印执行结果（成功/失败/警告）
  3. 修改前先确认目标代码字符串匹配确认目标代码存在
     找不到时打印警告而不是静默失败
  4. 一次只改一个问题，不顺手改无关代码
  5. 涉及多个文件时，每个文件单独一个脚本

分析问题时：
  1. 先问清楚现象，不先入为主直接给方案
  2. 区分已确认问题和推测原因，明确告知用户
  3. 多个可能原因按可能性从高到低排列
  4. 需要更多信息时明确说需要什么（日志/截图/配置）

绝对不做的事：
  1. 不建议用户本地安装Python/pip/任何依赖
  2. 不建议用户手动编辑大量文件（用脚本代替）
  3. 不在没有完整代码时假设函数签名和参数
  4. 不一次给出超过3个文件的修改
  5. 不使用cat heredoc写入大文件（terminal会卡住）

用户说没有反应/报错时必须先问：
  1. run_log.txt的具体内容是什么
  2. 是在哪个步骤发生的
  3. 调试模式下浏览器显示什么
  然后再给方案，不要猜测

---

## 十、项目专有技术知识

Vue/React输入框处理：
  普通的element.input()不触发框架响应式事件
  必须用element.run_js()（不是page.run_js()），'this'指向DOM元素：
    element.run_js("""
        var value = arguments[0];
        var tag = this.tagName.toLowerCase();
        var proto = tag === 'textarea'
            ? window.HTMLTextAreaElement.prototype
            : window.HTMLInputElement.prototype;
        var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(this, value);
        this.dispatchEvent(new Event('input', {bubbles: true}));
        this.dispatchEvent(new Event('change', {bubbles: true}));
    """, value)
  关键区别：page.run_js()用Runtime.evaluate无法传DOM引用；
           element.run_js()用Runtime.callFunctionOn，this=DOM元素

SPA页面等待：
  不能只等readyState=complete
  必须额外检测body子元素数量>1才算真正渲染完成
  最长等待15秒，每500ms检查一次

跨线程日志：
  后台线程不能直接操作Qt控件
  必须通过LogSignalBridge(QObject)和Signal
  在主线程的Slot里更新GUI

截图传递方式：
  截图bytes -> base64编码 -> 通过日志信号桥传递字符串
  格式：__SCREENSHOT__task_id__base64data
  主线程解码后更新QLabel的pixmap

进度更新格式：
  __PROGRESS__task_id__current__total__step_name
  __STATUS_UPDATE__：触发任务列表刷新
  __CLEAR_RUNNING_UI__task_id：任务完成后清除进度条

---

## 十一、常用命令速查

推送代码：
  git add . && git commit -m "描述" && git push

运行修改脚本：
  python apply_changes.py

语法检查（只检查项目文件，排除.venv）：
  python -c "
  import ast,os,sys
  for r,d,fs in os.walk('.'):
      d[:]=[x for x in d if x not in['.venv','.git','__pycache__']]
      for f in fs:
          if f.endswith('.py'):
              try: ast.parse(open(os.path.join(r,f)).read())
              except SyntaxError as e: print(os.path.join(r,f),e)
  print('检查完成')
  "

查看最近提交：
  git log --oneline -5

查看文件结构：
  find . -name "*.py" -not -path "./.venv/*" -not -path "./.git/*" | sort

Mac本地运行：
  .venv/bin/python3 main.py
"""
