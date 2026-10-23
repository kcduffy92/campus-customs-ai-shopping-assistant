"""Tiny Chrome DevTools Protocol helper for Problem 11 screenshots (headless Microsoft Edge, no extra packages).

Start Edge once (it keeps running between steps):
    python tests/cdp.py launch
Then other scripts do:
    from cdp import Page
    page = Page.connect()
    page.viewport(1280, 800); page.goto("http://localhost:5173/"); page.shot("out.jpg")
"""
from __future__ import annotations

import base64
import itertools
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

PORT = 9223
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def launch() -> None:
    profile = Path(tempfile.gettempdir()) / "cc_app_check_edge"
    subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}",
                      "--no-first-run", "--disable-extensions", "--hide-scrollbars", "--window-size=1280,800", "about:blank"])
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1)
            print("edge ready")
            return
        except Exception:
            time.sleep(0.2)
    sys.exit("edge did not start")


class Page:
    def __init__(self, ws_url: str):
        self.ws = connect(ws_url, max_size=50_000_000, open_timeout=10, ping_interval=None, close_timeout=2)
        self.ids = itertools.count(1)
        self.send("Page.enable")
        self.send("Runtime.enable")

    @classmethod
    def connect(cls) -> "Page":
        tabs = [t for t in json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")) if t["type"] == "page"]
        return cls(tabs[0]["webSocketDebuggerUrl"])

    def send(self, method: str, **params):
        mid = next(self.ids)
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv(timeout=120))
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def js(self, expression: str, timeout_s: float = 90):
        """Evaluate JS (awaiting promises) and return its value."""
        r = self.send("Runtime.evaluate", expression=expression, awaitPromise=True, returnByValue=True, timeout=int(timeout_s * 1000))
        if "exceptionDetails" in r:
            raise RuntimeError(r["exceptionDetails"].get("exception", {}).get("description") or r["exceptionDetails"])
        return r["result"].get("value")

    def viewport(self, width: int, height: int, mobile: bool = False) -> None:
        self.send("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=2 if mobile else 1, mobile=mobile)
        self.send("Emulation.setTouchEmulationEnabled", enabled=mobile)

    def reduced_motion(self, on: bool) -> None:
        self.send("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "reduce" if on else "no-preference"}])

    def goto(self, url: str, settle_s: float = 1.2) -> None:
        self.send("Page.navigate", url=url)
        for _ in range(100):
            if self.js("document.readyState") == "complete":
                break
            time.sleep(0.1)
        time.sleep(settle_s)

    def shot(self, path: str | Path, quality: int = 82, full_page: bool = False) -> Path:
        params = {"format": "jpeg", "quality": quality}
        if full_page:
            m = self.send("Page.getLayoutMetrics")["cssContentSize"]
            params.update(captureBeyondViewport=True, clip={"x": 0, "y": 0, "width": m["width"], "height": m["height"], "scale": 1})
        data = self.send("Page.captureScreenshot", **params)["data"]
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(base64.b64decode(data))
        return p


if __name__ == "__main__":
    if sys.argv[1:] == ["launch"]:
        launch()
