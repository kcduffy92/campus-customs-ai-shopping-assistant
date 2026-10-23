"""Crop the chat panel out of desktop screenshots (headless Edge, no image library needed).

    python tests/crop_shots.py SRC.jpg DEST.jpg [x y w h]
Default region is the chat panel in a 1280x800 desktop screenshot.
"""
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cdp import Page  # noqa: E402

IMG = Path(__file__).resolve().parents[1] / "output" / "app_check_images"


def crop(page: Page, src: str, dest: str, x=846, y=140, w=420, h=580):
    page.viewport(1280, 800)
    page.goto((IMG / src).resolve().as_uri(), 0.4)
    page.js("document.body.style.margin = '0'; const i = document.querySelector('img'); i.style.cssText = 'position:absolute;left:0;top:0;margin:0'; 1")
    time.sleep(0.2)
    data = page.send("Page.captureScreenshot", format="jpeg", quality=88, clip={"x": x, "y": y, "width": w, "height": h, "scale": 1})["data"]
    (IMG / dest).write_bytes(base64.b64decode(data))


if __name__ == "__main__":
    p = Page.connect()
    args = sys.argv[1:]
    crop(p, args[0], args[1], *map(int, args[2:6])) if len(args) > 2 else crop(p, args[0], args[1])
