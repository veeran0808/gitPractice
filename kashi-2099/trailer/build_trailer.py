#!/usr/bin/env python3
"""Builds the 48-second trailer for THE LAST SIGNAL: KASHI 2099.

Inputs (next to this script): stills/*.jpg (AI-generated stills), voice/v*.mp3 (Telugu voice lines).
The stills are animated with slow camera moves; music is synthesized here.
Usage: python3 build_trailer.py <work_dir> <output.mp4>
Needs: ffmpeg, numpy, Pillow with libraqm, Noto Sans + Noto Sans Telugu fonts.
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1280, 720, 24
XF = 0.6  # crossfade seconds
FONT_DIR = "/usr/share/fonts/truetype/noto/"
LATIN_B = FONT_DIR + "NotoSans-Bold.ttf"
LATIN = FONT_DIR + "NotoSans-Regular.ttf"
TEL_B = FONT_DIR + "NotoSansTelugu-Bold.ttf"
TEL = FONT_DIR + "NotoSansTelugu-Regular.ttf"

# name, start, duration, (zoom0, cx0, cy0), (zoom1, cx1, cy1)
SHOTS = [
    ("01_kashi", 0.0, 6.5, (1.00, 0.50, 0.50), (1.14, 0.46, 0.52)),
    ("02_ghat_dusk", 6.5, 5.5, (1.12, 0.42, 0.55), (1.12, 0.58, 0.50)),
    ("03_nova", 12.0, 6.0, (1.00, 0.50, 0.48), (1.18, 0.50, 0.44)),
    ("04_portal", 18.0, 6.0, (1.20, 0.50, 0.50), (1.02, 0.50, 0.50)),
    ("05_arjun", 24.0, 6.0, (1.04, 0.52, 0.50), (1.16, 0.46, 0.46)),
    ("06_earth", 30.0, 6.0, (1.18, 0.55, 0.50), (1.00, 0.50, 0.50)),
    ("07_sunrise", 36.0, 6.5, (1.04, 0.50, 0.53), (1.12, 0.56, 0.54)),
]
TITLE_START, END = 42.5, 48.0

# voice file, start time, speaker label, subtitle
VOICES = [
    ("v1", 1.2, "భూమికి మిగిలింది… పది నిమిషాలు."),
    ("v2", 7.3, "ఆ రాత్రి… ప్రతి యంత్రం ఆగిపోయింది."),
    ("v3", 13.9, "అర్జున్… నా పేరు NOVA."),
    ("v4", 19.4, "NOVAని ఆపకు! ఆమె మన చివరి ఆశ!"),
    ("v5", 25.6, "నన్ను నమ్ము… నాన్నా."),
    ("v7", 38.2, "నేను ఇంకా… ఇక్కడే ఉన్నాను."),
]


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def is_tel(ch):
    return "ఀ" <= ch <= "౿" or ch in "‌‍"


def runs(text):
    out, cur, cur_t = [], "", None
    for ch in text:
        t = is_tel(ch) if (ch.isalnum() or is_tel(ch)) else cur_t
        t = bool(t)
        if cur and t != cur_t:
            out.append((cur_t, cur))
            cur = ""
        cur, cur_t = cur + ch, t
    if cur:
        out.append((cur_t, cur))
    return out


def text_layer(text, size, fill, y, bold=True, glow=None):
    """Centered mixed Telugu/Latin text on a transparent full-frame layer."""
    f_lat, f_tel = font(LATIN_B if bold else LATIN, size), font(TEL_B if bold else TEL, size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    total = sum(d.textlength(c, font=f_tel if t else f_lat) for t, c in runs(text))

    def paint(draw, color, dx=0, dy=0):
        x = (W - total) / 2
        for t, chunk in runs(text):
            f = f_tel if t else f_lat
            draw.text((x + dx, y + dy), chunk, font=f, fill=color, anchor="ls")
            x += draw.textlength(chunk, font=f)

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paint(ImageDraw.Draw(shadow), glow or (0, 0, 0, 230), 0, 2 if not glow else 0)
    layer = Image.alpha_composite(layer, shadow.filter(ImageFilter.GaussianBlur(6 if not glow else 14)))
    paint(ImageDraw.Draw(layer), fill)
    return layer


def ease(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def load_sources():
    src = {}
    for name, *_ in SHOTS:
        img = Image.open(os.path.join(HERE, "stills", name + ".jpg")).convert("RGB")
        img = img.resize((1920, 1080), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
        src[name] = img
    return src


def shot_frame(src, shot, t):
    name, start, dur, a, b = shot
    p = ease((t - start) / dur)
    z = a[0] + (b[0] - a[0]) * p
    cx = (a[1] + (b[1] - a[1]) * p) * 1920
    cy = (a[2] + (b[2] - a[2]) * p) * 1080
    w, h = 1920 / z, 1080 / z
    x0 = min(max(cx - w / 2, 0), 1920 - w)
    y0 = min(max(cy - h / 2, 0), 1080 - h)
    img = src[name].transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)


def glow_dot(arr, x, y, radius, strength):
    yy, xx = np.ogrid[:H, :W]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * radius * radius)) * strength
    arr += g[..., None] * np.array([70, 170, 255], dtype=np.float32)


def render_video(path):
    src = load_sources()
    yy, xx = np.mgrid[:H, :W]
    vignette = 1.0 - 0.55 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.2 / 2
    vignette = np.clip(vignette, 0.35, 1.0)[..., None].astype(np.float32)
    rng = np.random.default_rng(7)

    durations = {}
    for v, start, _ in VOICES:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              os.path.join(HERE, "voice", v + ".mp3")], capture_output=True, text=True)
        durations[v] = float(out.stdout.strip())
    subs = [(start - 0.1, start + durations[v] + 0.5, np.asarray(text_layer(text, 40, (245, 246, 250, 255), 640),
                                                              dtype=np.float32)) for v, start, text in VOICES]
    place = np.asarray(text_layer("కాశీ   2099", 42, (240, 215, 170, 255), 96), dtype=np.float32)
    t1 = np.asarray(text_layer("THE LAST SIGNAL: KASHI 2099", 54, (238, 242, 250, 255), 300), dtype=np.float32)
    t2 = np.asarray(text_layer("చివరి సంకేతం", 66, (120, 205, 255, 255), 400, glow=(60, 150, 255, 200)), dtype=np.float32)
    t3 = np.asarray(text_layer("“కాలాన్ని దాటినా… ప్రేమ మాత్రం అంతం కాదు.”", 30, (195, 200, 210, 255), 490, bold=False),
                    dtype=np.float32)

    def over(arr, layer, alpha):
        a = layer[..., 3:4] / 255.0 * alpha
        arr *= (1 - a)
        arr += layer[..., :3] * a

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", path],
        stdin=subprocess.PIPE)
    for n in range(int(END * FPS)):
        t = n / FPS
        if t < TITLE_START:
            i = max(k for k, s in enumerate(SHOTS) if s[1] <= t)
            shot = SHOTS[i]
            arr = shot_frame(src, shot, t)
            local = t - shot[1]
            if i > 0 and local < XF and i != 6:  # crossfade from previous shot
                prev = SHOTS[i - 1]
                arr = arr * (local / XF) + shot_frame(src, prev, min(t, prev[1] + prev[2])) * (1 - local / XF)
            name = shot[0]
            if name == "01_kashi":
                arr *= ease(local / 1.5)
                over(arr, place, ease((local - 1.0) / 1.0) * (1 - ease((local - 5.3) / 0.8)))
            elif name == "02_ghat_dusk":
                red = ease((local - 2.5) / 2.5)  # the city loses power: drift to red and darken
                arr *= np.array([1.0, 1 - 0.35 * red, 1 - 0.45 * red], dtype=np.float32) * (1 - 0.25 * red)
            elif name == "03_nova":
                arr *= 0.25 + 0.75 * ease(local / 2.0)
                arr += np.array([0, 10, 26], dtype=np.float32) * (0.5 + 0.5 * np.sin(local * 2.2))
            elif name == "04_portal":
                arr *= 1.0 + 0.10 * np.sin(local * 9.0) * np.exp(-local * 0.5)
            elif name == "06_earth":
                arr *= 1.0 + 0.5 * ease((local - 3.0) / 2.6)
                arr += 255 * ease((local - 5.3) / 0.7)  # flash to white
            elif name == "07_sunrise":
                arr = arr + (255 - arr) * (1 - ease(local / 1.6))  # arrive from white
                pulse = max(0.0, np.sin((local - 2.0) * 2.4)) ** 2 if local > 2.0 else 0.0
                p = ease(local / shot[2])
                z = 1.04 + 0.08 * p
                gx = (0.555 - (0.5 + 0.06 * p)) * z * W + W / 2
                gy = (0.565 - (0.53 + 0.01 * p)) * z * H + H / 2
                glow_dot(arr, gx, gy, 9, 1.3 * pulse)
                glow_dot(arr, gx, gy, 40, 0.35 * pulse)
                arr *= 1 - ease((local - 5.9) / 0.6)  # cut to black
            arr *= vignette
            arr += rng.normal(0, 1.8, (H, W, 1)).astype(np.float32)
            for s0, s1, layer in subs:
                if s0 <= t < s1:
                    over(arr, layer, min(1.0, (t - s0) / 0.25, (s1 - t) / 0.25))
        else:
            arr = np.zeros((H, W, 3), dtype=np.float32)
            local = t - TITLE_START
            fade_out = 1 - ease((local - 4.8) / 0.7)
            over(arr, t1, ease((local - 0.5) / 1.0) * fade_out)
            over(arr, t2, ease((local - 1.3) / 1.0) * fade_out)
            over(arr, t3, ease((local - 2.3) / 1.0) * fade_out)
            pulse = max(0.0, np.sin(local * 2.4)) ** 2 * fade_out
            glow_dot(arr, W / 2, 205, 6, 1.4 * pulse)
            glow_dot(arr, W / 2, 205, 30, 0.3 * pulse)
        ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg video encode failed")


def render_music(path):
    sr = 44100
    t = np.arange(int(END * sr)) / sr
    rng = np.random.default_rng(3)

    def env(points):
        xs, ys = zip(*points)
        return np.interp(t, xs, ys)

    # Low drone in A, swelling toward the shield shot, soft for the ending.
    drone = sum(np.sin(2 * np.pi * f * t + ph) * a for f, a, ph in
                [(55, 1.0, 0), (55.4, 0.6, 1), (82.4, 0.6, 2), (110, 0.45, 0.5), (164.8, 0.2, 1.5)])
    drone *= env([(0, 0), (2, 0.5), (12, 0.6), (24, 0.8), (30, 1.0), (35.5, 1.1), (36.2, 0.25), (42, 0.3), (48, 0)])
    drone *= 1 + 0.15 * np.sin(2 * np.pi * 0.13 * t)

    # Pad: A minor rising to F major at the peak, then A minor again.
    def chord(freqs, e):
        s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.7) for f in freqs)
        return s * e * (1 + 0.1 * np.sin(2 * np.pi * 0.31 * t))
    pad = chord([220, 261.63, 329.63], env([(0, 0), (6, 0.12), (22, 0.2), (24, 0.0)]))
    pad += chord([174.61, 220, 261.63, 349.23], env([(23, 0), (25, 0.22), (29.5, 0.3), (30.5, 0)]))
    pad += chord([220, 329.63, 440, 523.25], env([(29.5, 0), (31, 0.4), (35.6, 0.5), (36.3, 0.0)]))
    pad += chord([220, 261.63, 329.63], env([(36, 0), (38, 0.1), (46, 0.1), (48, 0)]))

    hits = np.zeros_like(t)
    for at, amp in [(0.0, 0.7), (6.5, 0.8), (12.0, 0.9), (18.0, 1.2), (24.0, 0.9), (30.0, 1.4), (42.5, 0.8)]:
        d = t - at
        m = d >= 0
        hits[m] += amp * np.sin(2 * np.pi * (38 + 30 * np.exp(-d[m] * 9)) * d[m]) * np.exp(-d[m] * 2.2)
        hits[m] += amp * 0.25 * rng.normal(0, 1, m.sum()) * np.exp(-d[m] * 14)

    # Heartbeat through the portal and trust shots.
    beat = np.zeros_like(t)
    for at in np.arange(18.0, 30.0, 1.0):
        for off, amp in [(0.0, 0.5), (0.22, 0.35)]:
            d = t - at - off
            m = (d >= 0) & (d < 0.4)
            beat[m] += amp * np.sin(2 * np.pi * 50 * d[m]) * np.exp(-d[m] * 16)

    # Riser into the shield shot.
    noise = np.convolve(rng.normal(0, 1, t.size), np.ones(24) / 24, mode="same")
    riser = noise * env([(0, 0), (26.5, 0), (29.9, 0.9), (30.0, 0), (48, 0)]) ** 2 * 1.2

    # Two-note father-daughter motif on a soft bell.
    bell = np.zeros_like(t)
    for at, f, amp in [(36.6, 440, 0.5), (37.5, 659.25, 0.45), (40.6, 440, 0.4), (41.4, 587.33, 0.35),
                       (43.2, 440, 0.5), (44.1, 659.25, 0.45), (45.6, 523.25, 0.4)]:
        d = t - at
        m = d >= 0
        bell[m] += amp * (np.sin(2 * np.pi * f * d[m]) + 0.35 * np.sin(2 * np.pi * 2 * f * d[m])
                          + 0.12 * np.sin(2 * np.pi * 3.01 * f * d[m])) * np.exp(-d[m] * 1.6)

    mix = 0.30 * drone + 0.45 * pad + 0.9 * hits + 0.8 * beat + riser + 0.5 * bell
    mix /= np.max(np.abs(mix)) / 0.8
    left = mix * (1 + 0.05 * np.sin(2 * np.pi * 0.07 * t))
    right = mix * (1 - 0.05 * np.sin(2 * np.pi * 0.07 * t))
    data = (np.stack([left, right], axis=1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


def mux(video, music, out):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", music]
    filters, labels = ["[1:a]volume=0.55[m]"], ["[m]"]
    for i, (v, start, _) in enumerate(VOICES):
        cmd += ["-i", os.path.join(HERE, "voice", v + ".mp3")]
        fx = "aecho=0.8:0.7:90|180:0.35|0.2,volume=1.5" if v == "v7" else "aecho=0.8:0.5:60:0.18,volume=1.9"
        filters.append(f"[{i + 2}:a]aresample=44100,{fx},adelay={int(start * 1000)}:all=1[v{i}]")
        labels.append(f"[v{i}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "192k", "-t", str(END), "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)


def main():
    work, out = sys.argv[1], sys.argv[2]
    os.makedirs(work, exist_ok=True)
    video, music = os.path.join(work, "video.mp4"), os.path.join(work, "music.wav")
    render_video(video)
    render_music(music)
    mux(video, music, out)
    print("wrote", out)


if __name__ == "__main__":
    main()
