# Attribution and adaptation record

Reference repository: https://github.com/Joker-chichi/claude-mv-skill

Snapshot: `2ccf0c6ad31f27bb67e4a81e045e912f0a7d3e23` (2026-10-15).
The reference is a republished skill whose LICENSE credits tuzhechen2005 and John Heibel.
The root and installed skill LICENSE retain those notices. The engine's original John Heibel
MIT license is retained at `skills/song-mv/assets/template/LICENSE`.

Retained/adapted components: painting and character engine, demo scene, animation guide,
model-sheet loops, upstream xiaozhen storyboard/scene example, dependency lock.
No original commercial song audio, external font binaries or upstream promotional GIFs are bundled.

Codex adaptation: new SKILL.md and UI metadata, Python initializer/installer, basic/enhanced LRC
import, FFT beat analysis, environment doctor, reliable renderer and cache handling,
offline font setup, technical/visual verification instructions, tests and manual publishing guide.
The new code and documentation are also distributed under the included MIT terms.

Behavior changes: no Claude slash commands or hard-coded Claude installation paths;
no requirement to ask again for information or render authorization already supplied;
current local desktop execution is treated as local execution; no mandatory external apps.
Source changes create a new frame cache; encode reads configured audio, checks completeness,
reports subprocess failures and does not require launching a browser.

Primary technical references consulted on 2026-10-27:

- Codex skill discovery and packaging: https://learn.chatgpt.com/docs/build-skills
- Puppeteer requirements: https://pptr.dev/guides/system-requirements
- FFmpeg encoding/mapping: https://ffmpeg.org/ffmpeg.html
- LRC offset/line parser conventions: https://github.com/Clarkkkk/paroles
- GitHub repository creation: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
- GitHub upload: https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository

The bundled npm dependencies retain their own licenses in npm distributions. p5.js is LGPL-2.1;
p5.brush and Puppeteer have their own upstream notices. Dependencies are installed with npm ci,
not vendored or relicensed by the MIT notices on this adaptation.
