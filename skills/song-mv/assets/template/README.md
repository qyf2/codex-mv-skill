# Codex MV project

This is a standalone generated project. Run commands from this directory.

```text
npm ci
node doctor.mjs
node render.mjs --sheet=0.2,1,2 --out=out/check/first.jpg
node render.mjs --frames --workers=2
node render.mjs --encode --out=out/video.mp4
```

Requires Node.js >=22.12, Chrome/Chromium/Edge with WebGL2 and FFmpeg.
Set CHROME_PATH or FFMPEG_PATH when the tools are not found automatically.
Use `node render.mjs --help` for the supported command interface.

Edit `src/config.js` for duration, BPM, beat offset, fps and audio.
Read `ANIMATION_GUIDE.md` for the drawing/character API. `src/scenes/demo.js` is an optional upstream example;
new projects normally load `src/scenes/main.js` instead. Do not load both shot lists.
The studio already loads `src/lyrics.js` and `src/karaoke.js`. Use the installed skill's
`scripts/lrc_to_lyrics.py` to populate lyrics; use its `references/` for music timing and visual review.
Frames and MP4 outputs go under `out/`, which is excluded from source control.

There are no network fonts by default. Configure a licensed local font in `local-fonts.css` if needed.
Clawd is the optional upstream sample character. The engine is derived from John Heibel's
ClaudeAnimationBase and retains its MIT license in `LICENSE`.
