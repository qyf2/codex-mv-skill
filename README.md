# Codex Song MV Skill

从歌曲、LRC 和故事方向到手绘歌词 MV 的完整 Codex skill。沿用参考仓库的 p5.js + p5.brush 水彩引擎，补齐 Codex 工作流、跨平台初始化、歌词导入、依赖检查、可靠续渲与编码。

不需要 Claude、付费生成接口或 API key。画面由代码绘制。**这是动画制作 skill，不提供歌曲音源、作曲或真人视频生成。**

## 快速安装

下载/克隆本仓库。Python 3.10+ 下，在仓库目录执行：

```powershell
# 安装到你实际制作 MV 的项目中，只对该项目生效
python scripts/install.py --dest "D:\你的MV项目\.agents\skills"
```

macOS/Linux：

```bash
python3 scripts/install.py --dest "/path/to/your-project/.agents/skills"
```

如需个人全局使用，明确指定 `--dest "~/.agents/skills"`；已有同名 skill 时默认拒绝覆盖，
`--replace` 会先移出扫描目录保存备份。也可直接把 `skills/song-mv` 整个文件夹复制到目标 `.agents/skills/`。
当前官方文档使用 `.agents/skills` 作为本地发现路径；不需要改 `config.toml` 或 Claude 配置。
Codex 如未发现新增 skill，重启或开启新聊天。[官方安装位置说明](https://learn.chatgpt.com/docs/build-skills)

## 使用

在安装目标项目打开 Codex，输入：

```text
使用 $song-mv，把我的 song.wav 和 song.lrc 做成 15 秒的水彩手绘 MV。
故事是小纸船离开小镇后找到回家的灯，画幅 16:9，歌词高亮，保留音轨。
直接完成分镜、预览审片和本地成片，交付可编辑工程。
```

也可要求无歌词 MV，或用自己的角色替换上游示范角色。
普通 LRC 提供行时间，行内高亮是近似；增强 LRC 可使用真实词级时间戳。不会凭空声称精确逐字对齐。

## 依赖和首次运行

- Python 3.10+。
- **Node.js >=22.12**，推荐当前 LTS。
- Chrome / Chromium / Edge，WebGL2 可用。
- FFmpeg（H.264/AAC）；推荐同时安装 ffprobe。
- NumPy，仅自动检测 BPM 时需要。

Windows 可从 [Python](https://www.python.org/downloads/)、[Node.js](https://nodejs.org/en/download)、
[FFmpeg 下载页](https://ffmpeg.org/download.html)安装对应工具；浏览器可使用已有 Chrome/Edge。
安装后重新打开终端，确认 `python --version`、`node --version`、`ffmpeg -version`。
macOS 有 Homebrew 时可 `brew install python node ffmpeg`，另装 Chrome；
Debian/Ubuntu 可从系统包管理器装 Python/FFmpeg/Chromium，但 Node 包版本必须再核实为 >=22.12。

```powershell
python -m pip install -r skills/song-mv/requirements.txt
python skills/song-mv/scripts/new_project.py "projects/my-mv" --duration=15
Set-Location -LiteralPath "projects/my-mv"
npm.cmd ci
node doctor.mjs
node render.mjs --sheet=0.2,1,2 --out=out/check/first.jpg
```

上述命令先验证可运行 starter；新故事仍需由 Codex 按分镜实现。
后续 LRC 导入、音轨裁切、画面审查和成片导出详见 [SKILL.md](skills/song-mv/SKILL.md) 与
[运行指南](skills/song-mv/references/runtime.md)。
画布为 1920×1080，支持不同导出尺寸；竖屏需要重新构图和调整引擎，当前测试覆盖 16:9。
渲染期间无需在线字体；中文缺字时安装系统 CJK 字体或配置有许可的本地字体。

## 验证与演示

[测试报告](TEST_REPORT.md)说明实际验证范围。[demo/smoke.mp4](demo/smoke.mp4) 是合成音轨和原创示例歌词的技术冒烟样片，
用于验证工程、中文歌词与音轨导出；不是完整商业歌曲或最终艺术品质示范。

开发者可复现：

```text
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/runtime.test.mjs
python tests/e2e.py --dest "test-results/new-mv-project"
```

第三条需 Node、npm、浏览器、FFmpeg 均已可用，且目标目录应不存在。
FFmpeg 不在 PATH 时可加 `--ffmpeg=绝对路径`，Node 可加 `--node=绝对路径`。
正式长 MV 的渲染时间取决于场景复杂度、时长、GPU、帧率，先渲染少量帧估算。

## 上传到你自己的 GitHub

见 [完整上传步骤](UPLOAD.zh-CN.md)，提供网页上传、Git 命令和上传后的安装方式。
上传的是解压后整个仓库的内容，不只是 SKILL.md，也不是只上传 ZIP 文件。

## 来源与许可

本项目依据 [Joker-chichi/claude-mv-skill](https://github.com/Joker-chichi/claude-mv-skill)
的 `2ccf0c6ad31f27bb67e4a81e045e912f0a7d3e23` 版本适配。
保留原作者 tuzhechen2005、John Heibel 的 MIT 许可与归属；Clawd 仅作为上游示范角色保留。
详细变更、兼容范围和技术来源见 [ATTRIBUTION.md](ATTRIBUTION.md)。
