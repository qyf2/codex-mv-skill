#!/usr/bin/env python3
"""Make a source ZIP with no installed dependencies, caches or private work files."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','node_modules','out','__pycache__','.venv','.npm-cache','.agents','projects','test-results'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True)
    a=p.parse_args(); out=Path(a.out).resolve()
    if out.is_relative_to(ROOT): p.exit(1,'Place the ZIP outside the repository root\n')
    out.parent.mkdir(parents=True,exist_ok=True)
    files=sorted(f for f in ROOT.rglob('*') if f.is_file() and not any(part in EXCLUDED for part in f.relative_to(ROOT).parts) and not f.name.endswith('.pyc') and not f.name.startswith('.env'))
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in files: z.write(f, str(Path('codex-mv-skill')/f.relative_to(ROOT)))
    with zipfile.ZipFile(out) as z:
        if z.testzip(): raise RuntimeError('ZIP integrity check failed')
        assert 'codex-mv-skill/skills/song-mv/SKILL.md' in z.namelist()
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_suffix('.zip.sha256').write_text(digest+'  '+out.name+'\n',encoding='ascii')
    print(f'{len(files)} files, {out.stat().st_size} bytes, SHA256 {digest}')


if __name__=='__main__': main()
