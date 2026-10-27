# 运行与渲染

## 环境

- Python 3.10+（`python`，macOS/Linux 可能为 `python3`）。
- Node.js >=22.12，推荐当前 LTS；`node --version` 核实。Puppeteer 25 已不支持 Node 18。
- Chrome、Chromium 或 Edge，WebGL2 可用。不会自动下载浏览器。
- FFmpeg，支持 `libx264` 和 AAC；`ffprobe` 推荐用于交付检查。
- NumPy 仅供节拍分析：`python -m pip install -r "<SKILL>/requirements.txt"`。

依赖由 `package-lock.json` 固定：在生成的项目目录执行 `npm ci`，不要删除锁文件后任意升级。
PowerShell 如限制 `npm.ps1`，使用 `npm.cmd ci`，不必改变系统执行策略。
若 npm 的全局缓存不可写，可执行 `npm.cmd ci --cache .npm-cache`；缓存不进入 Git。

## Windows PowerShell

```powershell
python "C:\path\song-mv\scripts\new_project.py" "D:\MV Projects\song-one" --duration=15
Set-Location -LiteralPath "D:\MV Projects\song-one"
npm.cmd ci
node doctor.mjs
node render.mjs --sheet=0.2,1,2 --out=out/check/first.jpg
node render.mjs --frames --workers=2
node render.mjs --encode --out=out/video.mp4
```

`CHROME_PATH`/`FFMPEG_PATH` 是当前进程环境变量，不修改机器级设置：

```powershell
$env:CHROME_PATH = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
$env:FFMPEG_PATH = 'D:\tools\ffmpeg\bin\ffmpeg.exe'
node doctor.mjs
```

含空格的 `--key=value` 参数，把整个参数加引号，例如：
`node render.mjs --encode "--audio=assets/my song.wav" "--out=out/my mv.mp4"`。

## macOS / Linux

```bash
python3 "/path/to/song-mv/scripts/new_project.py" "/path/to/my-mv" --duration=15
cd "/path/to/my-mv"
npm ci
node doctor.mjs
node render.mjs --sheet=0.2,1,2 --out=out/check/first.jpg
node render.mjs --frames --workers=2
node render.mjs --encode --out=out/video.mp4
```

可用 `CHROME_PATH='/path/chrome' node doctor.mjs`。
容器中的 Chrome 如果因 sandbox 报错，优先使用有正常 sandbox 支持的环境；受信任本地模板在必要时可显式加 `--no-sandbox`。
默认不会关闭浏览器 sandbox。

## 渲染选项

`node render.mjs --help` 为准确的命令接口，所有值使用 `--key=value`。
工作画布固定为 1920×1080；`--width=960 --height=540` 是导出缩放，不能把故事画布自动改成竖屏。
需要竖屏时先重新构图并修改引擎 W/H、画布及字幕坐标，再实测；当前交付版本直接验证的是 16:9。

- `--clip`：续渲缓存后直接编码，不是仅预览。短片使用时可带 `--range=0:2`。
- `--frames`：多 worker、原子写帧、断点续渲，默认全部时长。
- `--range=1:2`：绝对时间，端点须落在帧边界；24fps 时整数秒自然满足。
  同范围编码需要 `--encode --range=1:2`；只渲染部分后不带 range 编码会因缺帧失败。
- `--fps=24`、`--width=1920 --height=1080`、`--workers=1`。
- `--loop=emotions` / `--loop=views` 可用于关键帧、序列、编码。
- `--soft-gl`：SwiftShader 软件 WebGL，慢但可在无 GPU 的机器上工作。
- `--gpu-angle=vulkan` 或 `--gpu-angle=gl-egl` 供 Linux 特定 GPU 排错。
- `--crop=x,y,w,h`：画面像素裁切，适用于 sheet/strip；不接受 JS 表达式。
- `--crf=18 --preset=medium`：编码质量与速度，预览可选 `--preset=ultrafast`。
- `--timeout=120000`：浏览器启动页面/协议操作毫秒超时。

不能把 `--fps` 或 `--soft-gl` 从渲染命令中去掉后直接编码；缓存按它们区分。
源码、歌词或素材改变后会产生新缓存目录，不再复用旧帧；旧目录可在确认无用后由用户清理。
`out/video.mp4.json` 记录预期成片参数，仍需实际媒体解码验证，不能将该旁车文件当作媒体验证结果。

## 字体与脱网运行

渲染本身不访问字体 CDN。优先使用系统楷体/中文字体；Linux 可安装发行版的 Noto CJK 字体。
要固定视觉表现，将有许可的字体放入 `assets/fonts/`，在 `local-fonts.css` 中配置 `@font-face`，
并将 `PROJECT.karaokeFont` 设为对应字体族。浏览器会等字体加载完成后开始绘制。
不要声称不同操作系统或 GPU 上的像素完全相同；在同一浏览器/引擎/字体下验证时间确定性。

## 常见故障

| 情况 | 处理 |
|---|---|
| Node 18/20 或 EBADENGINE | 安装 >=22.12，重新打开终端，重新 `npm ci` |
| Chrome 找不到 | `CHROME_PATH` 或 `--chrome=` 绝对路径 |
| WebGL2 不可用 | doctor 加 `--soft-gl`，渲染编码也保留同选项 |
| 等待 ready 超时 | 检查打印的页面错误、p5 文件、字体；先跑随附 demo |
| `Cannot redefine property` | 将场景 helper 放进 IIFE，避开 p5 全局名 |
| 音频找不到 | 相对路径以项目 cwd 为基准，`PROJECT.audio` 指向裁好的音频 |
| 编码缺帧 | 用相同参数补 `--frames`，核对 range；不删除检查机制 |
| 改场景后“缓存消失” | 新内容指纹会切换缓存，这是避免旧画面混入的预期行为 |
