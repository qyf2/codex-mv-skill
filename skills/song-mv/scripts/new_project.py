#!/usr/bin/env python3
"""Create a runnable MV project without Bash. Python 3.10+, no Python packages."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys


def create_project(destination, keep_demo=False, duration=8.0):
    source = Path(__file__).resolve().parents[1] / 'assets' / 'template'
    dest = Path(destination).expanduser().resolve()
    if dest.is_relative_to(source) or source.is_relative_to(dest):
        raise ValueError('Choose a project directory separate from the installed skill template')
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise ValueError(f'Refusing to overwrite a nonempty path: {dest}')
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('duration must be positive')
    shutil.copytree(source, dest, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('node_modules', 'out', '__pycache__'))
    (dest / 'assets').mkdir(exist_ok=True)
    if not keep_demo:
        html = (dest / 'studio.html').read_text(encoding='utf-8')
        (dest / 'studio.html').write_text(html.replace('src/scenes/demo.js', 'src/scenes/main.js'), encoding='utf-8')
        (dest / 'src' / 'config.js').write_text('const PROJECT = ' + json.dumps({
            'duration': duration, 'bpm': 120, 'offset': 0, 'fps': 24,
        }) + ';\n', encoding='utf-8')
        (dest / 'src' / 'scenes' / 'main.js').write_text('''// Replace this working starter with the storyboard's shots.
(() => {
  function opening(t, lt, dur) {
    camBegin(960 + Math.sin(t * .4) * 10, 540, 1.02);
    boilSeed('sky'); paint(rectPts(-200,-200,2320,1480), {wash: PAL.sky, ink:null});
    boilSeed('ground'); paint(ellPts(960,1210,1500,480), {wash:PAL.sap, ink:null});
    const mood = emotions(lt, [[0,'thinking'], [Math.min(2,dur*.3),'hopeful']]);
    clawd(960 + Math.sin(t)*18, 850, 32, mood);
    camEnd();
    if (lt < .4) iris(960,680,1500*easeOut(lt/.4));
    if (lt > dur-.5) iris(960,680,1500*(1-ease((lt-dur+.5)/.5)));
  }
  shots([[0,opening]]);
})();
''', encoding='utf-8')
    return dest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination')
    p.add_argument('--keep-demo', action='store_true')
    p.add_argument('--duration', type=float, default=8)
    p.add_argument('--install', action='store_true', help='Run npm ci after copying')
    a = p.parse_args()
    try:
        dest = create_project(a.destination, a.keep_demo, a.duration)
        print(f'Project: {dest}')
        if a.install:
            npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
            if not npm:
                raise ValueError('npm not found. Install Node.js >=22.12, then run npm ci in the project.')
            subprocess.run([npm, 'ci', '--no-audit', '--no-fund'], cwd=dest, check=True)
        print('Next: cd to project, run npm ci, then node doctor.mjs and node render.mjs --sheet=0.2,1,2')
    except (ValueError, OSError, subprocess.CalledProcessError) as e:
        p.exit(1, f'ERROR: {e}\n')


if __name__ == '__main__':
    main()
