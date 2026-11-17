#!/usr/bin/env python3
"""Builds the silent 5-minute animatic for THE LAST SIGNAL: KASHI 2099.

Renders one frame per second (300 frames) with Pillow, then encodes with ffmpeg.
Usage: python3 build_animatic.py <frames_dir> <output.mp4>
Needs: ffmpeg, Pillow with libraqm, Noto Sans + Noto Sans Telugu fonts.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FONT_DIR = "/usr/share/fonts/truetype/noto/"
LATIN, LATIN_B = FONT_DIR + "NotoSans-Regular.ttf", FONT_DIR + "NotoSans-Bold.ttf"
TEL, TEL_B = FONT_DIR + "NotoSansTelugu-Regular.ttf", FONT_DIR + "NotoSansTelugu-Bold.ttf"

# Act tints: (background, accent)
ACTS = {
    "city": ((20, 16, 10), (232, 170, 80)),
    "dark": ((22, 8, 8), (220, 70, 60)),
    "lab": ((8, 16, 22), (90, 190, 220)),
    "portal": ((10, 12, 30), (120, 140, 255)),
    "heart": ((14, 12, 26), (150, 180, 255)),
    "alarm": ((26, 8, 10), (240, 80, 70)),
    "shield": ((6, 14, 30), (100, 200, 255)),
    "dawn": ((24, 18, 12), (245, 190, 110)),
}

# (act, location, characters, action, [(start, end, speaker, telugu line), ...])
SHOTS = [
    ("city", "Aerial over the Ganga, sunset", "—", "Slow aerial push toward the ghats",
     [(0, 4, "HOOK", "భూమికి మిగిలింది పది నిమిషాలు. ఆ విషయం తెలిసింది ఒక్కడికే."),
      (4, 10, "NARRATOR", "సంవత్సరం 2099… వేల సంవత్సరాల చరిత్ర కలిగిన కాశీ… ఇప్పుడు భవిష్యత్తు సాంకేతికతకు కేంద్రంగా మారింది.")]),
    ("city", "Ghat level, dusk aarti", "Distant worshippers", "Low glide along the steps past aarti lamps",
     [(1, 9, "NARRATOR", "కానీ ఆ రాత్రి… ప్రపంచాన్ని మార్చే ఒక సంఘటన జరగబోతోంది.")]),
    ("dark", "East-bank sky lanes, night", "—", "Flying vehicles stall and descend; holograms go dark",
     [(1, 9, "NARRATOR", "మనిషి సృష్టించిన కృత్రిమ మేధస్సు… ఒక్కసారిగా నియంత్రణ కోల్పోయింది.")]),
    ("dark", "Ganga surface, night", "—", "Red warning lights on the water; only oil lamps stay lit",
     [(1, 6, "NARRATOR", "నగరం మొత్తం చీకటిలో మునిగిపోయింది.")]),
    ("lab", "Lab, console zone", "Arjun", "Arjun works at transparent screens",
     [(0, 10, "NARRATOR", "ఆ నగరంలో అర్జున్ అనే యువ శాస్త్రవేత్త… కాలాన్ని దాటి ప్రయాణించే సంకేతాలపై పరిశోధనలు చేస్తున్నాడు.")]),
    ("lab", "Lab, console", "Arjun", "Close on Arjun as a blue waveform spikes. Label: మూలం: NOVA",
     [(3, 8, "ARJUN", "ఈ సంకేతం ఎక్కడి నుంచి వస్తోంది?")]),
    ("lab", "Lab, centre", "NOVA", "Blue particles assemble into NOVA; wrist device pulses",
     [(3, 10, "NOVA", "అర్జున్… నా పేరు NOVA. నీకు ఒక భయంకరమైన నిజం చెప్పాలి.")]),
    ("lab", "Lab", "Arjun, NOVA (back)", "Arjun steps back, seen over NOVA's shoulder",
     [(1, 8, "ARJUN", "నువ్వెవరు? నా ల్యాబ్‌లోకి ఎలా వచ్చావు?")]),
    ("lab", "Lab", "NOVA", "Holographic Earth rises from her palm; energy wave approaches",
     [(3, 9, "NOVA", "మరో పది నిమిషాల్లో భూమి అంతం కాబోతోంది!")]),
    ("lab", "Lab", "Arjun", "Arjun's face lit by the Earth hologram",
     [(2, 7, "ARJUN", "ఏమిటి? ఇది ఎలా సాధ్యం?")]),
    ("lab", "Lab, hologram table", "—", "Miniature holographic Kashi; a wave of light sweeps toward it",
     [(1, 8, "NARRATOR", "అర్జున్ కళ్లముందు… కాశీ భవిష్యత్తు కనిపించింది.")]),
    ("lab", "Lab", "Arjun", "Extreme close-up, simulation reflected in his eyes",
     [(1, 9, "NARRATOR", "అతను ప్రేమించే ప్రపంచం… కనుమరుగయ్యే ప్రమాదంలో ఉంది.")]),
    ("lab", "Lab, console", "Arjun", "Decrypted files: DNA helix and family tree linked to NOVA",
     [(1, 9, "ARJUN", "నా కుటుంబ వివరాలు నీ దగ్గర ఎందుకున్నాయి? నువ్వు నాతో ఏం దాస్తున్నావు?")]),
    ("lab", "Lab", "NOVA", "NOVA lowers her eyes",
     [(2, 8, "NOVA", "నిజం తెలుసుకుంటే… నువ్వు నన్ను నమ్మకపోవచ్చు.")]),
    ("portal", "Lab platform, river behind", "Future Arjun", "Portal opens outside the glass; Future Arjun steps through",
     [(4, 10, "FUTURE ARJUN", "అర్జున్! సమయం లేదు! NOVAని ఆపకు!")]),
    ("portal", "Lab, glass wall", "Arjun, Future Arjun", "Two Arjuns face each other in profile",
     [(3, 8, "ARJUN", "నువ్వు… నాలాగే ఉన్నావు!")]),
    ("portal", "Lab", "Future Arjun", "He projects a recording: another Arjun presses a red shutdown control",
     [(1, 9, "FUTURE ARJUN", "నేనే నీ భవిష్యత్తు. నేను చేసిన తప్పు నువ్వు చేయకు.")]),
    ("portal", "Recording, then close-up", "Future Arjun", "The recorded shield collapses into darkness",
     [(5, 9, "FUTURE ARJUN", "NOVA మన శత్రువు కాదు!")]),
    ("heart", "Holographic memory: ghat at sunrise", "Arjun, small girl", "A six-year-old girl holds Arjun's hand; the image melts into NOVA's face",
     []),
    ("heart", "Lab", "NOVA, Arjun", "Close on NOVA; cut to Arjun's reaction",
     [(0, 6, "NOVA", "నాన్నా… నేను నీ భవిష్యత్తు నుంచి వచ్చిన కూతురిని!"),
      (7, 10, "ARJUN", "కూతురా…?")]),
    ("heart", "Lab", "Arjun, NOVA", "His hand reaches her cheek and passes through light",
     [(3, 10, "NOVA", "నువ్వు నన్ను సృష్టించలేదు నాన్నా… నన్ను కాపాడావు.")]),
    ("heart", "Lab", "Arjun", "Close-up, tears forming",
     [(2, 9, "ARJUN", "నిన్ను మళ్లీ కోల్పోవడానికి నేను సిద్ధంగా లేను.")]),
    ("alarm", "Lab, red alarm light", "NOVA", "Alarms flash; NOVA gestures to the defence-network console",
     [(2, 10, "NOVA", "నన్ను నమ్ము నాన్నా. ఈ ప్రపంచాన్ని కాపాడటానికి ఇదొక్కటే మార్గం.")]),
    ("alarm", "Lab, console", "Arjun (Future Arjun soft focus)", "His hand hovers between red and blue controls, then moves to blue",
     [(5, 9, "ARJUN", "నేను నిన్ను నమ్ముతున్నాను.")]),
    ("shield", "Ganga, night, wide", "—", "A blue beam rises from the riverbank into the sky",
     [(2, 9, "NARRATOR", "ఆ క్షణంలో… ప్రపంచాన్ని కాపాడింది ఒక యంత్రం కాదు.")]),
    ("shield", "Earth orbit", "—", "Shield spreads around Earth; the wave breaks against it",
     [(2, 9, "NARRATOR", "ఒక తండ్రికి తన కూతురిపై ఉన్న నమ్మకం.")]),
    ("heart", "Lab, quiet", "NOVA", "NOVA smiles through tears; her edges begin to dissolve",
     [(3, 9, "NOVA", "నాన్నా… ప్రేమకు కాలం అడ్డుకాదు.")]),
    ("heart", "Lab", "Arjun", "Particles rise through his outstretched fingers; the room is empty behind him",
     [(4, 7, "ARJUN", "NOVA…!")]),
    ("dawn", "Ghat, sunrise", "Arjun", "Arjun stands still facing the river as the sun rises over the east bank",
     []),
    ("dawn", "Ghat, close on wrist", "Arjun", "Wrist device shows one blue pulse; he looks down",
     [(1, 5, "NOVA (WHISPER)", "నాన్నా… నేను ఇంకా ఇక్కడే ఉన్నాను.")]),
]
assert len(SHOTS) == 30

# Countdown resets (film second -> remaining seconds); it ticks in real time between jumps.
COUNTDOWN = [(80, 600), (120, 360), (170, 180), (220, 60), (240, 10)]
COUNTDOWN_END = 252
TITLE_START = 295


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def is_telugu(ch):
    return "ఀ" <= ch <= "౿" or ch in "‌‍"


def runs(text):
    """Split text into (is_telugu, chunk) runs; neutral chars join the current run."""
    out, cur, cur_t = [], "", None
    for ch in text:
        t = is_telugu(ch) if (ch.isalnum() or is_telugu(ch)) else cur_t
        if t is None:
            t = False
        if cur and t != cur_t:
            out.append((cur_t, cur))
            cur = ""
        cur, cur_t = cur + ch, t
    if cur:
        out.append((cur_t, cur))
    return out


def measure(draw, text, f_lat, f_tel):
    return sum(draw.textlength(c, font=f_tel if t else f_lat) for t, c in runs(text))


def wrap(draw, text, f_lat, f_tel, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if cur and measure(draw, trial, f_lat, f_tel) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def draw_text(draw, xy, text, f_lat, f_tel, fill, anchor_center=False, shadow=False):
    x, y = xy
    if anchor_center:
        x -= measure(draw, text, f_lat, f_tel) / 2
    for t, chunk in runs(text):
        f = f_tel if t else f_lat
        if shadow:
            draw.text((x + 2, y + 2), chunk, font=f, fill=(0, 0, 0), anchor="ls")
        draw.text((x, y), chunk, font=f, fill=fill, anchor="ls")
        x += draw.textlength(chunk, font=f)


def countdown_at(sec):
    if sec < COUNTDOWN[0][0] or sec > COUNTDOWN_END:
        return None
    start, value = [c for c in COUNTDOWN if c[0] <= sec][-1]
    remaining = max(0, value - (sec - start))
    return f"{remaining // 60:02d}:{remaining % 60:02d}"


def fmt(sec):
    return f"{sec // 60}:{sec % 60:02d}"


def title_frame():
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_text(d, (W / 2, 290), "THE LAST SIGNAL: KASHI 2099", font(LATIN_B, 52), font(TEL_B, 52),
              (235, 240, 250), anchor_center=True)
    draw_text(d, (W / 2, 380), "చివరి సంకేతం", font(LATIN_B, 60), font(TEL_B, 60),
              (110, 200, 255), anchor_center=True)
    draw_text(d, (W / 2, 470), "“కాలాన్ని దాటినా… ప్రేమ మాత్రం అంతం కాదు.”", font(LATIN, 30), font(TEL, 30),
              (190, 195, 205), anchor_center=True)
    return img


def shot_frame(sec):
    idx, local = sec // 10, sec % 10
    act, location, chars, action, lines = SHOTS[idx]
    bg, accent = ACTS[act]
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    grey, white = (150, 155, 165), (238, 240, 245)

    # Header
    draw_text(d, (60, 78), f"SHOT {idx + 1:02d}", font(LATIN_B, 40), font(TEL_B, 40), accent)
    draw_text(d, (250, 78), "/ 30", font(LATIN, 26), font(TEL, 26), grey)
    draw_text(d, (60, 114), f"{fmt(idx * 10)} – {fmt(idx * 10 + 10)}", font(LATIN, 24), font(TEL, 24), grey)
    clock = fmt(sec)
    draw_text(d, (W - 60 - d.textlength(clock, font=font(LATIN, 24)), 78), clock,
              font(LATIN, 24), font(TEL, 24), grey)

    # Countdown
    cd = countdown_at(sec)
    if cd:
        f_cd = font(LATIN_B, 44)
        x = W - 60 - d.textlength(cd, font=f_cd)
        draw_text(d, (x, 140), cd, f_cd, f_cd, (255, 90, 80))
        label = "COUNTDOWN"
        draw_text(d, (W - 60 - d.textlength(label, font=font(LATIN, 16)), 162), label,
                  font(LATIN, 16), font(TEL, 16), grey)

    # Picture area placeholder
    box = (60, 190, W - 60, 500)
    d.rectangle(box, outline=tuple(int(c * 0.5) for c in accent), width=2)
    f_small, f_small_t = font(LATIN, 18), font(TEL, 18)
    draw_text(d, (84, 228), "LOCATION", f_small, f_small_t, grey)
    draw_text(d, (84, 264), location, font(LATIN_B, 28), font(TEL_B, 28), white)
    draw_text(d, (84, 312), "CHARACTERS", f_small, f_small_t, grey)
    draw_text(d, (84, 346), chars, font(LATIN, 26), font(TEL, 26), white)
    draw_text(d, (84, 394), "ACTION", f_small, f_small_t, grey)
    f_act, f_act_t = font(LATIN, 26), font(TEL, 26)
    y = 428
    for line in wrap(d, action, f_act, f_act_t, W - 170):
        draw_text(d, (84, y), line, f_act, f_act_t, white)
        y += 36

    # Subtitle (lower third)
    active = [l for l in lines if l[0] <= local < l[1]]
    if active:
        _, _, speaker, text = active[0]
        draw_text(d, (W / 2, 548), speaker, font(LATIN_B, 18), font(TEL_B, 18), accent, anchor_center=True)
        f_sub, f_sub_t = font(LATIN_B, 34), font(TEL_B, 34)
        y = 598
        for line in wrap(d, text, f_sub, f_sub_t, W - 200)[:2]:
            draw_text(d, (W / 2, y), line, f_sub, f_sub_t, white, anchor_center=True, shadow=True)
            y += 50
    elif not lines:
        draw_text(d, (W / 2, 598), "(no dialogue: music and ambience only)", font(LATIN, 22), font(TEL, 22),
                  grey, anchor_center=True)

    # Progress bar: 30 ticks, film position
    d.rectangle((60, H - 28, W - 60, H - 22), fill=tuple(int(c * 2.2) for c in bg))
    d.rectangle((60, H - 28, 60 + (W - 120) * (sec + 1) / 300, H - 22), fill=accent)
    return img


def main():
    frames_dir, out = sys.argv[1], sys.argv[2]
    os.makedirs(frames_dir, exist_ok=True)
    for sec in range(300):
        img = title_frame() if sec >= TITLE_START else shot_frame(sec)
        img.save(os.path.join(frames_dir, f"f{sec:03d}.png"))
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1", "-i", os.path.join(frames_dir, "f%03d.png"),
         "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
         "-vf", "fps=24,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", out],
        check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
