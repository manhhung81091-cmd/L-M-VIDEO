#!/usr/bin/env python3
"""Tự tổng hợp nhạc nền piano nhẹ (không lời, tự sáng tác bằng code => không vướng bản quyền).

    python3 nhac.py --out nhac.wav --dur 43.5 [--warm-from 28]

Vòng hợp âm C – G/B – Am – F, ~70 BPM, rải hợp âm + pad mềm.
Từ giây --warm-from trở đi thêm bè trầm cho ấm hơn (cảnh mẹ ôm con).
"""
import argparse
import wave

import numpy as np

SR = 48000
BPM = 70
BEAT = 60 / BPM


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def piano(freq, dur, vel=0.5):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 400))
    tone = sum(a * np.sin(2 * np.pi * freq * k * t) * np.exp(-t * (k - 1) * 0.9)
               for k, a in ((1, 1.0), (2, 0.42), (3, 0.18), (4, 0.08), (5, 0.04)))
    return vel * env * tone


def pad(freqs, dur):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.8).clip(0)
    sig = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) for f in freqs)
    return 0.05 * env * sig / len(freqs)


# (gốc trầm, nốt rải) theo MIDI
CHORDS = [
    (48, [60, 64, 67, 72]),   # C
    (47, [59, 62, 67, 71]),   # G/B
    (45, [57, 60, 64, 69]),   # Am
    (41, [57, 60, 65, 69]),   # F
]
MELODY = [76, None, 74, None, 72, None, 71, 72, 74, None, None, None,
          72, None, 71, None, 69, None, 67, 69, 72, None, None, None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--warm-from", type=float, default=1e9)
    ap.add_argument("--bpm", type=float, default=BPM)
    args = ap.parse_args()
    beat = 60 / args.bpm

    n = int((args.dur + 4) * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    bar = 4 * beat
    t0, ci, mi = 0.0, 0, 0
    rng = np.random.default_rng(7)
    while t0 < args.dur + 1:
        root, notes = CHORDS[ci % 4]
        i0 = int(t0 * SR)
        # pad
        p = pad([midi_hz(x) for x in notes[:3]], bar + 0.6)
        L[i0:i0 + len(p)] += p[: n - i0]
        R[i0:i0 + len(p)] += p[: n - i0]
        # bass
        bvel = 0.32 if t0 >= args.warm_from else 0.2
        b = piano(midi_hz(root), 3.5, bvel)
        L[i0:i0 + len(b)] += b[: n - i0]
        R[i0:i0 + len(b)] += b[: n - i0]
        if t0 >= args.warm_from:
            b2 = piano(midi_hz(root + 7), 3.0, 0.12)
            j = int((t0 + 2 * beat) * SR)
            L[j:j + len(b2)] += b2[: max(0, n - j)]
            R[j:j + len(b2)] += b2[: max(0, n - j)]
        # rải 8 nốt móc đơn
        order = [0, 1, 2, 3, 2, 1, 2, 1]
        for k, o in enumerate(order):
            ts = t0 + k * beat / 2 + rng.uniform(-0.008, 0.008)
            s = piano(midi_hz(notes[o]), 2.5, 0.16 + 0.03 * (k % 4 == 0))
            j = int(ts * SR)
            pan = 0.35 + 0.3 * (o / 3)
            L[j:j + len(s)] += (1 - pan) * s[: max(0, n - j)]
            R[j:j + len(s)] += pan * s[: max(0, n - j)]
        # giai điệu thưa (từ ô nhịp 3)
        if ci >= 2:
            for k in range(4):
                m = MELODY[mi % len(MELODY)]
                mi += 1
                if m:
                    s = piano(midi_hz(m), 2.8, 0.22)
                    j = int((t0 + k * beat) * SR)
                    L[j:j + len(s)] += 0.55 * s[: max(0, n - j)]
                    R[j:j + len(s)] += 0.45 * s[: max(0, n - j)]
        t0 += bar
        ci += 1

    # reverb đơn giản (comb + trễ chéo)
    for d, g in ((0.031, 0.35), (0.047, 0.3), (0.071, 0.25), (0.113, 0.2), (0.167, 0.15)):
        k = int(d * SR)
        L[k:] += g * R[:-k]
        R[k:] += g * L[:-k]
    out = np.stack([L, R], 1)[: int(args.dur * SR)]
    out /= np.abs(out).max() / 0.7
    with wave.open(args.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    main()
