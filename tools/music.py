#!/usr/bin/env python3
"""Синтез тимчасової музичної підкладки (м'яке інді/ембієнт, 84 BPM): пед, «електропіано»-арпеджіо,
легка перкусія з другої частини, реверберація. Для чорнових версій; у фінал — ліцензований трек.

  python3 tools/music.py OUT.wav DURATION_S [--seed N]
"""
import argparse
import wave

import numpy as np

SR = 44100


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_adsr(n, a, d, s, r, sr=SR):
    t = np.arange(n) / sr
    e = np.ones(n) * s
    na, nd, nr = int(a * sr), int(d * sr), int(r * sr)
    e[:na] = np.linspace(0, 1, max(1, na))[:len(e[:na])]
    e[na:na + nd] = np.linspace(1, s, max(1, nd))[:len(e[na:na + nd])]
    if nr > 0:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def pad_voice(freq, dur, amp):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):
        f = freq * 2 ** (det / 12)
        for h in range(1, 7):
            sig += np.sin(2 * np.pi * f * h * t + h) / (h ** 1.6)
    lfo = 1 + 0.08 * np.sin(2 * np.pi * 0.2 * t)
    return sig * env_adsr(n, 1.2, 0.5, 0.8, 1.4) * amp * lfo / 3


def ep_note(freq, dur, amp):
    """«Електропіано»: синус + дзвінкі гармоніки з різним затуханням."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.2)
           + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 4.5)
           + 0.18 * np.sin(2 * np.pi * freq * 3.01 * t) * np.exp(-t * 7)
           + 0.08 * np.sin(2 * np.pi * freq * 7.1 * t) * np.exp(-t * 18))
    att = np.minimum(1, t / 0.004)
    return sig * att * amp


def kick(amp):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 52 + 70 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * amp


def shaker(rng, amp):
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    x = np.diff(np.concatenate([[0], x]))  # грубий high-pass
    return x * np.exp(-t * 60) * amp


def reverb(x, rng, seconds=2.4, mix=0.32):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t * 3.0 / seconds * 2.2)
    ir[0] = 0
    # м'якше: згладжуємо ВЧ
    k = np.ones(8) / 8
    ir = np.convolve(ir, k, mode="same")
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return x * (1 - mix) + y * mix


def build(duration, seed=4):
    rng = np.random.default_rng(seed)
    bpm = 84
    beat = 60 / bpm
    bar = 4 * beat
    total = int((duration + 3) * SR)
    L = np.zeros(total)
    Rr = np.zeros(total)
    # D-dur: Dmaj9 – Bm7 – Gmaj7 – A6sus
    chords = [[50, 57, 61, 64, 66], [47, 54, 57, 62, 64], [43, 50, 54, 59, 62], [45, 52, 55, 59, 62]]
    bass = [38, 35, 31, 33]
    nbars = int(duration / bar) + 2

    def add(buf, sig, start, pan=0.0):
        i = int(start * SR)
        if i >= total:
            return
        sig = sig[:total - i]
        buf_l, buf_r = buf
        buf_l[i:i + len(sig)] += sig * (1 - max(0, pan))
        buf_r[i:i + len(sig)] += sig * (1 + min(0, pan))

    for b in range(nbars):
        ch = chords[b % 4]
        t0 = b * bar
        intensity = min(1.0, 0.45 + b * 0.06)
        for k, nn in enumerate(ch[1:]):
            add((L, Rr), pad_voice(midi(nn), bar + 1.2, 0.05), t0, pan=(k - 1.5) * 0.25)
        add((L, Rr), pad_voice(midi(bass[b % 4]), bar + 1.0, 0.09), t0)
        # арпеджіо з 2-го такту, вісімки, з паузами для «дихання»
        if b >= 1:
            pattern = [0, 2, 1, 3, 4, 3, 2, 1]
            notes = [n + 12 for n in ch]
            for e in range(8):
                if b < 3 and e % 2:
                    continue
                if rng.random() < 0.12:
                    continue
                nn = notes[pattern[e] % len(notes)]
                vel = (0.07 + 0.03 * rng.random()) * intensity
                add((L, Rr), ep_note(midi(nn), 2.2, vel), t0 + e * beat / 2 + rng.normal(0, 0.006),
                    pan=0.35 * np.sin(e))
        # мелодійні «дзвіночки» в кульмінації
        if b >= 5 and b % 2 == 1:
            for e, nn in enumerate([ch[-1] + 12, ch[-2] + 12, ch[-1] + 19]):
                add((L, Rr), ep_note(midi(nn), 2.5, 0.05), t0 + (1.5 + e) * beat, pan=-0.3 + 0.3 * e)
        # перкусія з 4-го такту
        if b >= 3:
            for q in (0, 2):
                add((L, Rr), kick(0.22 * intensity), t0 + q * beat)
            for s in range(16):
                if s % 2 == 1:
                    add((L, Rr), shaker(rng, 0.009 * intensity * (1.3 if s % 4 == 2 else 1)), t0 + s * beat / 4,
                        pan=0.4)
    L = reverb(L, rng)
    Rr = reverb(Rr, np.random.default_rng(seed + 1))
    st = np.stack([L, Rr], 1)[:int(duration * SR)]
    # м'яке затухання
    fo = int(2.5 * SR)
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    fi = int(0.4 * SR)
    st[:fi] *= np.linspace(0, 1, fi)[:, None]
    st = np.tanh(st * 1.4) / np.tanh(1.4)
    st /= np.max(np.abs(st)) / 0.89
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("duration", type=float)
    ap.add_argument("--seed", type=int, default=4)
    a = ap.parse_args()
    st = build(a.duration, a.seed)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(a.out, f"{a.duration:.1f}s")


if __name__ == "__main__":
    main()
