#!/usr/bin/env python3
"""Estimate BPM/phase with bounded-memory spectral flux and FFT autocorrelation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np


def estimate(x, sr=22050, minimum=60, maximum=180):
    hop, win = 128, 2048
    if len(x) < sr * 4 or not np.isfinite(x).all() or np.max(np.abs(x)) < 1e-6:
        raise ValueError('Need at least four seconds of audible, finite audio')
    frames = np.lib.stride_tricks.sliding_window_view(x, win)[::hop]
    chunks, previous = [], None
    for start in range(0, len(frames), 512):
        spectrum = np.log1p(np.abs(np.fft.rfft(frames[start:start+512] * np.hanning(win), axis=1)))
        block = spectrum if previous is None else np.vstack([previous, spectrum])
        chunks.append(np.maximum(0, np.diff(block, axis=0)).sum(axis=1))
        previous = spectrum[-1:]
    flux = np.concatenate(chunks)
    n = min(64, len(flux))
    flux = np.maximum(flux - np.convolve(flux, np.ones(n)/n, 'same'), 0)
    if float(flux.sum()) < 1e-6:
        raise ValueError('No measurable beat onsets; use a manual BPM/offset')
    size = 1 << (2 * len(flux)-1).bit_length()
    transform = np.fft.rfft(flux, n=size)
    ac = np.fft.irfft(transform * transform.conj(), n=size)[:len(flux)]
    rate = sr/hop
    bpms = np.arange(minimum, maximum+.001, .05)
    scores = np.interp(rate*60/bpms, np.arange(len(ac)), ac)
    bpm = float(bpms[np.argmax(scores)])
    beat = 60/bpm
    def score(phase):
        idx = (np.arange(phase, len(flux)/rate, beat)*rate).astype(int)
        return flux[idx[idx<len(flux)]].sum()
    phase = max(np.arange(0, beat, .005), key=score)
    # Flux compares adjacent STFT frames; report the approximate window-centre time.
    phase = float((phase + (win/2+hop)/sr) % beat)
    return {'bpm': round(bpm, 3), 'half_time_bpm': round(bpm/2, 3), 'beat_seconds': round(beat, 6),
            'beat_at': round(phase, 6), 'status': 'estimate; audition for half/double-time and phase'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio')
    p.add_argument('--from', dest='start', type=float, default=0)
    p.add_argument('--to', dest='end', type=float)
    p.add_argument('--min-bpm', type=float, default=60)
    p.add_argument('--max-bpm', type=float, default=180)
    p.add_argument('--ffmpeg', default=os.environ.get('FFMPEG_PATH', 'ffmpeg'))
    p.add_argument('--json')
    a = p.parse_args()
    try:
        length = (a.end-a.start) if a.end is not None else 60
        if a.start < 0 or not 4 <= length <= 300 or not 20 <= a.min_bpm < a.max_bpm <= 400:
            raise ValueError('Choose a 4..300 second segment and 20 <= min-bpm < max-bpm <= 400')
        data = subprocess.run([a.ffmpeg,'-v','error','-ss',str(a.start),'-i',a.audio,'-t',str(length),
            '-ac','1','-ar','22050','-f','f32le','-'], capture_output=True, check=True)
        result = estimate(np.frombuffer(data.stdout, dtype='<f4'), minimum=a.min_bpm, maximum=a.max_bpm)
        result['beat_at'] = round(result['beat_at']+a.start, 6)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if a.json:
            path=Path(a.json); path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    except (ValueError, OSError, subprocess.CalledProcessError) as e:
        if isinstance(e, subprocess.CalledProcessError):
            p.exit(1, 'ERROR: FFmpeg failed: '+e.stderr.decode(errors='replace')[:1000]+'\n')
        p.exit(1, f'ERROR: {e}\n')


if __name__ == '__main__':
    main()
