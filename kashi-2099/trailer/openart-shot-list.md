# Trailer shot list for OpenArt generation

The goal is to replace the seven stills in `stills/` with real image-to-video clips, keeping the same filenames but as `.mp4`. Each clip should be about 5–7 s, 16:9 and 720p or higher. `build_trailer.py` will then be switched from animating stills to cutting these clips. Voices, music, subtitles and timing all stay as they are.

**Budget rule:** OpenArt generations use paid account credits. Before generating anything, get the user's approval for the estimated credit cost: once for the reference images, and once per video clip. Do not batch-generate. Do not upgrade plans.

## Order of work
1. Generate the Arjun reference image (prompt C1 in `../01-foundation-and-shots-01-05.md`) and the NOVA reference (C3). Get the user's approval on both before going further.
2. Generate one still per shot with the reference attached, then run image-to-video using the motion prompt.
3. Save the clips as `stills/<name>.mp4` and rebuild the trailer.

Append this style line to every image prompt:
`photorealistic cinematic film still, shot on ARRI Alexa 65 with anamorphic lenses, natural skin texture, fine film grain, teal and amber color grade, volumetric light, high dynamic range, 16:9 aspect ratio`

| File | Trailer time | Image prompt | Motion prompt |
|---|---|---|---|
| 01_kashi | 0:00–0:06.5 | Aerial view of Varanasi at golden sunset from above the Ganga, crescent of ancient stone ghat steps and unaltered sandstone temples with shikhara spires on the west bank, wooden boats, slim futuristic glass towers only on the far east bank, small flying vehicles in orderly lanes high above the river | Slow aerial push toward the ghats; vehicles glide; water ripples; temples stay unchanged |
| 02_ghat_dusk | 0:06.5–0:12 | Eye-level view along the stone ghat steps of Varanasi at dusk during aarti, brass oil lamps with flames, floating leaf diyas, temple shikharas, thin blue holographic guide-lights high above the river | Slow sideways glide; then the blue guide-lights and distant tower lights go dark one by one, only the oil flames remain |
| 03_nova | 0:12–0:18 | Thousands of blue light particles forming the face and shoulders of a young Indian woman as a translucent blue hologram, glowing blue eyes, hair tied back, dim lab with sandstone walls (attach NOVA reference) | Particles settle into her face; she opens her eyes and looks at camera; slow push in; steady glow |
| 04_portal | 0:18–0:24 | Night, circular portal of swirling blue energy on a wet stone platform beside the Ganga, 45-year-old Indian man with grey-streaked hair and greying beard stepping out in a worn dark charcoal jacket (attach Arjun reference, aged) | He takes one step out of the portal; mist moves; camera steady |
| 05_arjun | 0:24–0:30 | Close two-shot, 30-year-old Indian man with trimmed black beard and tears in his brown eyes, dark charcoal high-collar jacket, reaching toward the cheek of a translucent blue hologram woman (attach both references) | His hand passes through her cheek, particles scatter from his fingers; a tear falls; camera still |
| 06_earth | 0:30–0:36 | Earth from orbit at night, a blue beam rising from northern India spreading into a glowing hexagonal shield around the planet, a vast wave of golden-white cosmic light approaching from the right | Shield spreads across the planet as the wave breaks against it; slow drift left |
| 07_sunrise | 0:36–0:42.5 | Man standing alone on the stone ghat steps of Varanasi at sunrise, seen from behind, dark charcoal jacket, a small blue light glowing on his left wrist, golden sun over the misty Ganga, wooden boats | A blue pulse on his wrist, twice; he lowers his head to look at it; camera still |
