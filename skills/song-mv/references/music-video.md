# 音乐、歌词与分镜时间

## 一个时间原点

歌曲时间 `songTime`，选段起点 `clipStart`，镜头/歌词时间 `t = songTime - clipStart`。
先探测音频真实时长，再选片段；不要把 LRC 文件最后一行当成歌曲终点。

```text
ffprobe -v error -show_entries format=duration -of json song.wav
python "<SKILL>/scripts/beat_grid.py" song.wav --from=0 --to=30 --json=beat-grid.json
ffmpeg -y -ss 60 -i song.wav -t 15 -af "afade=t=out:st=13:d=2" -c:a aac assets/clip.m4a
python "<SKILL>/scripts/lrc_to_lyrics.py" song.lrc --clip-start=60 --duration=15
```

Windows 若 FFmpeg 不在 PATH，节拍脚本支持 `--ffmpeg=绝对路径` 或环境变量 `FFMPEG_PATH`。
命令里的 60、15、13 仅为示意，应替换成实际片段值。
配置：`const PROJECT = {duration:15,bpm:120,offset:0,fps:24,audio:'assets/clip.m4a'};`。
`offset` 是片段里的节拍相位，需根据测得的 `beat_at` 换算到片段时间。

节拍脚本默认分析最多前 60 秒；指定区间最多 300 秒，FFT 自相关和分块 STFT 避免长歌二次复杂度。
输出 BPM 和 half-time 候选；自动检测对弱节奏、切分、变速、长静音没有保证。
试听并用画面打拍检查至少几处；必要时手动输入 BPM/offset，变速歌曲使用分段时间表。
别把检测到的相位未经验证当成精确强拍。

## LRC 导入

转换脚本只用 Python 标准库，输出：

- `src/lyrics.js`：浏览器可直接加载的 `window.MV_LYRICS` 数据。
- `assets/lyrics.json`：可审查的同一时间轴。

支持 UTF-8/BOM、UTF-16 BOM、GB18030（或 `--encoding=`）；多时间标签、重复时间的双语行、
毫秒、文件内的 `[offset:+N]`、选段跨行和空行清屏。
遵循常见 LRC 约定：正 offset 令歌词提前，`adjusted = stamp - offset/1000`。
多种播放器的 offset 约定可能不同，交付前必须用歌声抽查；需要时在源副本里修正，不动原件。

基本 LRC：

```text
[00:00.50]风吹过纸上的山
[00:02.50]灯光等着我们回家
[00:05.00]
```

只有行起点来自文件；行内高亮按本行到下一行时长线性插值，属于近似视觉效果。
增强 LRC：

```text
[00:00.50]<00:00.50>风<00:00.90>吹过<00:01.40>纸上的山<00:02.20>
[00:02.50]<00:02.50>灯光<00:03.10>等着<00:03.60>我们回家<00:04.70>
[00:05.00]
```

`<mm:ss.xxx>` 是每个文本单元的绝对歌曲起点，下一标记是该单元结束；末尾空文本标记可指定最后词的结束。
导入后 `opts.words` 保存这些时间。增强歌词同时带重复行标签时会报错，需先展开成独立行，避免猜测词时间。
最后一行若没有明确清屏时间，会保持到片段末尾；检查是否需要在 LRC 添加空时间行。
双语同时间行会用 ` · ` 合并并采用行级近似；需要精确双语词高亮应单独设计双行 overlay。

## 视觉叙事

按乐句安排镜头，不把每个字都画成一个事件。主歌建立关系、副歌让同一意象升级、桥段改变视角、
尾声回到开头的构图并带来情绪变化。高潮动作放在有时间依据的重拍/重词上，给反应留时间。
人物和关键道具避开默认字幕区域 y=975..1070，重要表情尽量在 y<940。
长句会自动缩小以容纳 1660px 安全宽度；如果缩得难读，应合理分行而不是无限减小字体。

歌词不要求额外生成服务。要精确对齐、换歌词或转写时，先发现当前真实可用的工具，不能写死不存在的工具名或声称已有结果。
