"""Render the SVG as a looping GIF for README image viewers.

Requires Pillow and rsvg-convert. Run: python3 scripts/render-banner.py
"""

from copy import deepcopy
from io import BytesIO
from math import cos, pi
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "{http://www.w3.org/2000/svg}"
FPS = 10
DURATION = 12


def pulse(time, period, phase=0):
    return (1 - cos(2 * pi * (time / period + phase))) / 2


def render_frames():
    source = ET.parse(ROOT / "assets/pixel-universe.svg").getroot()
    # Apply animation poses explicitly: raster renderers do not run SVG CSS.
    for style in source.findall(f"{SVG_NS}style"):
        source.remove(style)

    for frame_number in range(FPS * DURATION):
        frame = deepcopy(source)
        time = frame_number / FPS
        layers = {node.get("class"): node for node in frame.iter() if node.get("class")}
        for index, star in enumerate(layers["stars"]):
            brightness = 1 - .75 * pulse(time, 4 if index % 2 else 6, index / 7)
            star.set("opacity", f"{brightness:.3f}")
        layers["sparkles"].set("opacity", f"{1 - .65 * pulse(time, 4):.3f}")
        layers["planet"].set(
            "transform", f"translate({-6 * pulse(time, 6):.2f} {12 * pulse(time, 6):.2f})"
        )
        # Whole-pixel steps retain the character's pixel art style.
        lift = 4 * round(4 * pulse(time, 3))
        layers["astronaut-motion"].set("transform", f"translate(0 {-lift})")
        layers["beacon"].set("opacity", f"{1 - .65 * pulse(time, 3):.3f}")
        meteor_progress = (time - 8.4) / 1.2
        if 0 <= meteor_progress <= 1:
            layers["meteor"].set("opacity", f"{.9 * (1 - abs(2 * meteor_progress - 1)):.3f}")
            layers["meteor"].set(
                "transform", f"translate({-180 * meteor_progress:.2f} {72 * meteor_progress:.2f})"
            )
        else:
            layers["meteor"].set("opacity", "0")

        png = subprocess.run(
            ["rsvg-convert"], input=ET.tostring(frame), capture_output=True, check=True
        ).stdout
        yield Image.open(BytesIO(png)).convert("RGB")


def main():
    frames = list(render_frames())
    # One shared palette prevents color flicker between animation frames.
    palette = frames[0].quantize(colors=128)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    output = ROOT / "assets/pixel-universe.gif"
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=1000 // FPS,
        loop=0,
        optimize=True,
        disposal=1,
    )
    print(f"Rendered {len(frames)} frames: {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
