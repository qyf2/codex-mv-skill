#!/usr/bin/env python3
"""Install the bundled Codex skill into an explicitly chosen local skill directory."""
import argparse
import datetime
from pathlib import Path
import shutil


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dest', required=True, help='Parent skill directory, e.g. <project>/.agents/skills or ~/.agents/skills')
    p.add_argument('--replace', action='store_true', help='Back up an existing song-mv before replacement')
    a = p.parse_args()
    source = Path(__file__).resolve().parents[1] / 'skills' / 'song-mv'
    parent = Path(a.dest).expanduser().resolve()
    target = parent / 'song-mv'
    try:
        if target.is_relative_to(source) or source.is_relative_to(target):
            raise ValueError('Installation destination must be separate from the source skill')
        if target.is_symlink():
            raise ValueError(f'Target is a symlink; select a different destination: {target}')
        if target.exists():
            if not a.replace:
                raise ValueError(f'Already exists: {target}; --replace preserves a backup first')
            # Outside the scanned skill folder, so a backup does not create duplicate skill names.
            backup = parent.parent / 'skill-backups' / ('song-mv-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(backup))
            print(f'Backup: {backup}')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('node_modules','out','__pycache__'))
        print(f'Installed: {target}')
        print('Use $song-mv in Codex. If it does not appear, restart Codex or open a new chat.')
    except (OSError, ValueError) as e:
        p.exit(1, f'ERROR: {e}\n')


if __name__ == '__main__':
    main()
