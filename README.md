# 墨墨背单词 · Windows 手柄触觉反馈

为 Windows Chrome 版墨墨背单词添加**手柄按键短震动反馈**的小工具。专门针对使用手柄背单词、希望每次按键都有触觉确认的场景。

> 这是个人实验项目，与墨墨背单词、盖世小鸡均无官方关联。

## 当前版本

`v0.1.0`：保留已在实际 Windows + Python 3.12 环境中成功启动、由使用者报告可用的 Python 源码。整理为 GitHub 项目，加入可选的 Windows EXE 构建流程。本仓库包的自动构建流程尚未在 Windows CI 中验证。

## 功能

- 通过 Windows XInput 读取手柄按键，并控制左右震动马达。
- 检测到**新按下**的按键时发送一次短震动，长按不会在每轮轮询中重复触发。
- 支持 A/B/X/Y、方向键、肩键等 XInput 按钮；LT/RT 通过阈值触发。
- 图形界面可启停、调整时长（50 到 300 毫秒，默认 **120 ms**）。按键反馈与测试震动均固定为 **100% 最大强度**，左右马达指令值均为 **65535**。
- 可设为仅在 Chrome 前台且窗口标题包含“墨墨 / maimemo / 背单词”时生效，或所有 Chrome 前台标签页生效。
- 无浏览器插件，无网络请求，不读取墨墨账户数据，不修改手柄固件，不改映射。

## 环境要求

- Windows 10/11
- Python 3.12（其他 Python 3 版本可能可用，但未验证）
- 系统可通过 **XInput** 识别并控制的手柄
- 使用墨墨背单词的 Google Chrome

运行本工具**无需安装任何第三方 Python 包**。Tkinter、ctypes 均随通常的 Windows Python 安装提供。

## 运行源码（推荐）

下载或克隆仓库，在 PowerShell 中进入项目目录，执行：

```powershell
py -3 .\maimemo_controller_haptics.py
```

打开后先点击 **「测试震动 0.5 秒」**，确认手柄实际振动。再打开 Chrome 的墨墨学习页面，切回 Chrome，按一下 A 键。

如果界面提示 `等待指定 Chrome 页面`，检查窗口标题是否包含 `墨墨`、`maimemo` 或 `背单词`。可以临时把生效范围切换为 **「所有 Chrome 标签页」** 用于排查。该筛选基于 **Chrome 进程名和前台窗口标题**，不能保证精确识别当前 URL。

### 无法震动时

1. 先按工具上的测试震动按钮，看工具是否能检测 XInput 手柄并驱动马达。
2. 如显示未检测到 XInput，说明当前连接方式可能未暴露该接口。Chrome Gamepad API 能识别手柄，并不能保证 Windows XInput 可用。
3. 检查 Chrome 是否处于前台，以及窗口标题是否符合上述关键词。
4. 不要为了使用这个工具关闭 Windows 智能应用控制（Smart App Control）或 Defender。

## 生成 Windows EXE（可选）

**EXE 打包依赖 PyInstaller，仅构建阶段需要；运行源码不需要它。** 在 Windows PowerShell 中进入仓库根目录：

```powershell
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name MaimemoHaptics .\maimemo_controller_haptics.py
```

输出位于 `dist/MaimemoHaptics.exe`。

仓库也提供 `.github/workflows/build-windows.yml`，推送到 `main` / `master` 分支或在 Actions 中手动运行后，可在构建任务的 Artifacts 下载打包结果。**上传源码不会自动生成已签名、可信任的 EXE。** 未签名的独立 EXE 仍可能被 Windows 智能应用控制拦截。若已经能通过 Python 正常运行，优先使用源码版本。

PyInstaller 需要在**目标操作系统上构建**，不能直接从 Linux 环境交叉编译 Windows EXE。参见 [PyInstaller 文档](https://pyinstaller.org/en/stable/operating-mode.html)。

## 隐私与安全

- 无外部通信、账号登录或遥测功能。
- 仅查询当前前台窗口的进程名/标题以判断是否生效；程序不保存窗口标题。
- 不调用网页脚本、不读取页面文本和背单词记录。
- 无管理员权限要求，不安装常驻服务。
- 使用前可以直接审阅 `maimemo_controller_haptics.py`，便于确认实际行为。

## 已知限制

- 仅适用于 Windows。蓝牙手柄如果未向 Windows 提供 XInput，可能无法使用。
- 当 Chrome 窗口标题不含对应关键词时，“墨墨标签页”模式不会启动；标题匹配有误判可能。
- 当应用失去焦点或窗口标题变动时，界面状态有约 0.3 秒更新间隔；这是窗口标题判定的轮询逻辑。
- 震动最大值是 **XInput 最大指令强度**，实际震感还受手柄本身档位和马达限制。
- 当前是个人使用与功能验证版本，尚未提供签名安装包。

## 权限说明

本仓库尚未添加开源许可证。公开仓库不等于自动授予他人复制、分发、修改许可。若准备开放复用，请先选择并添加合适的 LICENSE 文件。
