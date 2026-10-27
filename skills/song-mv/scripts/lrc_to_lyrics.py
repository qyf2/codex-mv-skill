#!/usr/bin/env python3
"""Convert basic/enhanced LRC into JSON and a safe browser JS data file."""
import argparse
import json
import math
from pathlib import Path
import re

STAMP = r'(\d+):([0-5]\d(?:\.\d{1,3})?)'
LINE = re.compile(r'\[' + STAMP + r'\]')
WORD = re.compile(r'<' + STAMP + r'>')


def decode(path, encoding='auto'):
    raw = Path(path).read_bytes()
    if encoding != 'auto':
        return raw.decode(encoding)
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    for enc in ('utf-8-sig', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    raise ValueError('Cannot decode LRC. Specify --encoding.')


def stamp(m):
    return int(m[1]) * 60 + float(m[2])


def parse_lrc(text):
    """Positive LRC offset advances text: adjusted = timestamp - offset/1000."""
    offsets = re.findall(r'\[offset:([+-]?\d+)\]', text, re.I)
    shift = -int(offsets[-1]) / 1000 if offsets else 0
    entries = []
    for line in text.splitlines():
        tags = list(LINE.finditer(line))
        if not tags:
            if re.match(r'^\[\d', line.strip()):
                raise ValueError(f'Malformed timestamp: {line[:80]}')
            continue
        content = line[tags[-1].end():].strip()
        words = list(WORD.finditer(content))
        if '<' in content and re.search(r'<\d', content) and not words:
            raise ValueError('Malformed enhanced LRC timestamps')
        if words and len(tags) != 1:
            raise ValueError('Enhanced LRC with repeated line timestamps is ambiguous; expand it into separate lines.')
        units = []
        if words:
            if content[:words[0].start()].strip():
                raise ValueError('Enhanced LRC text must start with a word timestamp')
            for i, tag in enumerate(words):
                end = words[i+1].start() if i+1 < len(words) else len(content)
                units.append([stamp(tag) + shift, content[tag.end():end]])
            if any(units[i][0] > units[i+1][0] for i in range(len(units)-1)):
                raise ValueError('Word timestamps must be ordered')
            content = ''.join(u[1] for u in units)
        for tag in tags:
            entries.append({'start': stamp(tag) + shift, 'text': content, 'words': units})
    if not entries:
        raise ValueError('No valid LRC timestamps found')
    entries.sort(key=lambda r: r['start'])
    merged = []
    for e in entries:
        if merged and abs(e['start'] - merged[-1]['start']) < 1e-7:
            prev = merged[-1]
            if e['text'] != prev['text']:
                prev['text'] += ' · ' + e['text']
                prev['words'] = []  # bilingual duplicate lines use line timing
        else:
            merged.append(e)
    return merged


def convert(text, clip_start, duration):
    if not math.isfinite(clip_start) or clip_start < 0 or not math.isfinite(duration) or duration <= 0:
        raise ValueError('clip-start >= 0 and duration > 0 must be finite')
    entries = parse_lrc(text)
    rows = []
    for i, e in enumerate(entries):
        start = e['start'] - clip_start
        end = entries[i+1]['start'] - clip_start if i+1 < len(entries) else duration
        end = min(end, duration)
        if not e['text'] or end <= 0 or start >= duration or end <= start:
            continue
        opts = {'singStart': start, 'sing': end-start, 'timing': 'line'}
        if e['words']:
            opts['words'] = [[round(t-clip_start, 6), word] for t, word in e['words']]
            opts['timing'] = 'word'
        rows.append([round(max(0,start), 6), round(end, 6), e['text'], opts])
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('lrc')
    p.add_argument('--clip-start', type=float, default=0)
    p.add_argument('--duration', type=float, required=True)
    p.add_argument('--encoding', default='auto')
    p.add_argument('--out', default='src/lyrics.js')
    p.add_argument('--json', default='assets/lyrics.json')
    a = p.parse_args()
    try:
        rows = convert(decode(a.lrc, a.encoding), a.clip_start, a.duration)
        if not rows:
            raise ValueError('No visible lyric lines in this clip; check clip-start and duration')
        js = Path(a.out); js.parent.mkdir(parents=True, exist_ok=True)
        # JSON encoding, not string interpolation, prevents quotes/backticks in lyrics becoming code.
        js.write_text('window.MV_LYRICS = ' + json.dumps(rows, ensure_ascii=True) + ';\n', encoding='utf-8')
        out = Path(a.json); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{len(rows)} lines -> {js} and {out}')
        if any(r[3]['timing'] == 'line' for r in rows):
            print('Basic LRC: line starts are sourced; the highlight between starts is approximate, not word alignment.')
    except (ValueError, OSError, UnicodeError) as e:
        p.exit(1, f'ERROR: {e}\n')


if __name__ == '__main__':
    main()
