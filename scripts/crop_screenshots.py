#!/usr/bin/env python3
"""Crop the Tableau Public screenshots to just the dashboard and save them."""
from pathlib import Path

from PIL import Image

SRC = Path("/var/folders/gh/5rb02z5d39db6lzvd15v9sg00000gn/T/claude-chrome-screenshots-8pkWPi")
OUT = Path(__file__).resolve().parent.parent / "screenshots"
OUT.mkdir(exist_ok=True)

jobs = {
    "screenshot-1789849327016-1.jpg": "dashboard_overview.png",
    "screenshot-1789849327015-0.jpg": "dashboard_filtered_ireland.png",
}
for src, dst in jobs.items():
    im = Image.open(SRC / src)
    w, h = im.size
    # keep from the sheet tabs down, and only the dashboard width (left 53%)
    box = (0, int(h * 0.165), int(w * 0.53), h)
    im.crop(box).save(OUT / dst)
    print(dst, im.crop(box).size)
