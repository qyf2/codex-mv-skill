#!/usr/bin/env python3
"""Real browser/FFmpeg smoke test. Writes only into a new destination directory."""
import argparse
import importlib.util
import json
import math
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT/'skills'/'song-mv'


def execute(args, cwd, env):
    print('RUN', ' '.join(map(str,args)), flush=True)
    subprocess.run(list(map(str,args)), cwd=cwd, env=env, check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dest', required=True)
    p.add_argument('--node', default='node')
    p.add_argument('--ffmpeg', default=os.environ.get('FFMPEG_PATH','ffmpeg'))
    p.add_argument('--npm-cache')
    a=p.parse_args()
    dest=Path(a.dest).resolve()
    execute([sys.executable,SKILL/'scripts/new_project.py',dest,'--duration=4'],ROOT,os.environ)
    # All fixture audio and lyrics are original synthetic test data.
    sr=22050; data=[]
    for i in range(sr*4):
        t=i/sr; beat=t%.5; note=[261.63,329.63,392,523.25][int(t)%4]
        value=.17*math.sin(2*math.pi*note*t)*math.exp(-beat*7)
        value+=.08*math.sin(2*math.pi*880*t)*math.exp(-beat*80)
        data.append(struct.pack('<h',int(max(-1,min(1,value))*32767)))
    with wave.open(str(dest/'assets/song.wav'),'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(b''.join(data))
    (dest/'assets/song.lrc').write_text('[00:00.250]<00:00.250>风把<00:00.750>纸船<00:01.250>轻轻推远<00:01.850>\n[00:02.000]<00:02.000>一盏灯<00:02.600>等我们<00:03.100>回家<00:03.650>\n[00:03.750]\n',encoding='utf-8')
    (dest/'src/config.js').write_text('const PROJECT = '+json.dumps({'duration':4,'bpm':120,'offset':0,'fps':12,'audio':'assets/song.wav'})+';\n',encoding='utf-8')
    env=os.environ.copy(); env['FFMPEG_PATH']=str(Path(a.ffmpeg).resolve()) if Path(a.ffmpeg).exists() else a.ffmpeg
    npm=shutil.which('npm.cmd' if sys.platform=='win32' else 'npm')
    if not npm: p.exit(1,'npm not found\n')
    npm_path=Path(npm).resolve()
    npm_cli=npm_path.parent/'node_modules/npm/bin/npm-cli.js'
    if npm_cli.is_file():
        install=[a.node,npm_cli,'ci','--no-audit','--no-fund']
    elif npm_path.suffix == '.js':
        install=[a.node,npm_path,'ci','--no-audit','--no-fund']
    else:
        install=[npm,'ci','--no-audit','--no-fund']
    if a.npm_cache: install += ['--cache', str(Path(a.npm_cache).resolve())]
    execute(install,dest,env)
    execute([sys.executable,SKILL/'scripts/lrc_to_lyrics.py','assets/song.lrc','--duration=4'],dest,env)
    execute([a.node,'doctor.mjs'],dest,env)
    execute([a.node,ROOT/'tests/e2e_checks.mjs',dest],dest,env)
    execute([a.ffmpeg,'-v','error','-i','out/smoke.mp4','-f','null','-'],dest,env)
    # Verify actual decoded frame count/dimensions and actual audio, independent of the renderer's sidecar.
    frames=subprocess.run([a.ffmpeg,'-v','error','-i','out/smoke.mp4','-map','0:v:0','-pix_fmt','rgb24','-f','rawvideo','-'],cwd=dest,capture_output=True,check=True).stdout
    if len(frames) != 48*960*540*3: raise AssertionError(f'Unexpected decoded video bytes: {len(frames)}')
    audio=subprocess.run([a.ffmpeg,'-v','error','-i','out/smoke.mp4','-map','0:a:0','-ac','1','-ar','22050','-f','s16le','-'],cwd=dest,capture_output=True,check=True).stdout
    if not 3.9 <= len(audio)/2/22050 <= 4.2: raise AssertionError('Wrong decoded audio duration')
    if max(abs(v[0]) for v in struct.iter_unpack('<h',audio)) < 100: raise AssertionError('Silent output audio')
    execute([a.ffmpeg,'-y','-v','error','-ss','1','-i','out/smoke.mp4','-frames:v','1','out/check/encoded.png'],dest,env)
    technical=subprocess.run([a.ffmpeg,'-hide_banner','-i','out/smoke.mp4','-f','null','-'],cwd=dest,capture_output=True,check=True)
    info=technical.stderr.decode(errors='replace')
    print(info)
    if not re.search(r'Video: h264.*yuv420p\(',info): raise AssertionError('Expected standard limited-range yuv420p H.264')
    (dest/'out/e2e-result.json').write_text(json.dumps({'status':'passed','frames':48,'width':960,'height':540,'fps':12,'duration':4,'audio':'AAC, decoded non-silent','checks':['real WebGL2 rendering','Chinese enhanced lyrics','out-of-order repeat frame equality','resumption','missing frame refusal','encoder error propagation','no browser needed for encode','source/font cache invalidation','full video/audio decode']},indent=2)+'\n',encoding='utf-8')
    print('E2E PASSED:',dest/'out/smoke.mp4')


if __name__=='__main__': main()
