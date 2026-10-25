"""Drive a throwaway Vivaldi profile over the Chrome DevTools Protocol.

Vivaldi's UI is itself a web page (`window.html`), so theme state, computed colours and
screenshots of the real browser chrome are all reachable through CDP.
"""
import base64
import itertools
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

VIVALDI = "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"


class CDPError(RuntimeError):
    pass


class Session:
    """One CDP websocket (a page target or the browser endpoint)."""

    def __init__(self, ws_url: str):
        self._conn = connect(ws_url, max_size=None, open_timeout=20)
        self.ws = self._conn.__enter__()
        self.ids = itertools.count(1)

    def send(self, method: str, params: dict | None = None, timeout: float = 60) -> dict:
        msg_id = next(self.ids)
        self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        deadline = time.monotonic() + timeout
        while True:
            msg = json.loads(self.ws.recv(timeout=max(0.1, deadline - time.monotonic())))
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise CDPError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def evaluate(self, expression: str, timeout: float = 60):
        r = self.send("Runtime.evaluate", {"expression": expression, "awaitPromise": True,
                                           "returnByValue": True}, timeout)
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            raise CDPError(d.get("exception", {}).get("description") or d.get("text"))
        return r["result"].get("value")

    def close(self):
        self._conn.__exit__(None, None, None)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Vivaldi:
    """Context manager: launches Vivaldi with a temp profile, removes it on exit."""

    def __init__(self, width: int = 1600, height: int = 1000):
        self.size = (width, height)

    # --- lifecycle -------------------------------------------------------------------------
    def __enter__(self):
        self.profile = Path(tempfile.mkdtemp(prefix="vivaldidark-"))
        self.port = _free_port()
        self.proc = subprocess.Popen(
            [VIVALDI, f"--user-data-dir={self.profile}", f"--remote-debugging-port={self.port}",
             "--no-first-run", "--no-default-browser-check", f"--window-size={self.size[0]},{self.size[1]}",
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.ui = Session(self._wait_target(lambda t: t["url"].endswith("/window.html")))
        self._wait_js("!!document.querySelector('#browser .tab-strip')", 30)
        self.browser = Session(self._json("/json/version")["webSocketDebuggerUrl"])
        self._leave_welcome()
        return self

    def _leave_welcome(self) -> None:
        """A fresh profile opens the welcome flow with the tab bar hidden; replace it with a Start Page tab."""
        self.set_pref("vivaldi.startup.has_seen_welcome_page", True)
        self.ui.evaluate("""new Promise(r => chrome.tabs.query({}, ts => chrome.tabs.create(
            {url: 'vivaldi://startpage', active: true}, () => chrome.tabs.remove(ts.map(t => t.id), r))))""")
        self._wait_js("document.querySelectorAll('.tab-position .tab').length === 1", 15)

    def __exit__(self, *exc):
        for s in (getattr(self, "ui", None), getattr(self, "browser", None)):
            if s:
                s.close()
        self.proc.terminate()
        try:
            self.proc.wait(10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)

    def _json(self, path: str):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as r:
            return json.load(r)

    def targets(self) -> list[dict]:
        return self._json("/json")

    def _wait_target(self, pred, timeout: float = 30) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                for t in self.targets():
                    if pred(t):
                        return t["webSocketDebuggerUrl"]
            except OSError:
                pass
            time.sleep(0.3)
        raise TimeoutError("Vivaldi target did not appear")

    def _wait_js(self, predicate: str, timeout: float = 10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.ui.evaluate(f"!!({predicate})"):
                return
            time.sleep(0.2)
        raise TimeoutError(f"timed out waiting for: {predicate}")

    # --- prefs & themes --------------------------------------------------------------------
    def pref(self, path: str):
        return self.ui.evaluate(f"vivaldi.prefs.get({json.dumps(path)}).then(r => r.value)")

    def set_pref(self, path: str, value) -> None:
        self.ui.evaluate(f"vivaldi.prefs.set({{path: {json.dumps(path)}, value: {json.dumps(value)}}})")

    def install_theme(self, zip_path: Path) -> str:
        """Import like a gallery download, then install and activate it (replacing any same-id theme)."""
        data = base64.b64encode(Path(zip_path).read_bytes()).decode()
        res = self.ui.evaluate(
            f"vivaldi.themePrivate.import({{dataBlob: Uint8Array.from(atob('{data}'), c => c.charCodeAt(0)).buffer}})")
        if res.get("error"):
            raise CDPError(f"theme import failed: {res['error']}")
        tid = res["themeID"]
        theme = next(t for t in self.pref("vivaldi.themes.preview") if t["id"] == tid)
        users = [t for t in self.pref("vivaldi.themes.user") if t["id"] != tid] + [theme]
        self.set_pref("vivaldi.themes.user", users)
        self.set_pref("vivaldi.themes.preview", [])
        # Both schedule slots, so a light OS appearance cannot swap our theme out.
        self.set_pref("vivaldi.theme.schedule.o_s", {"dark": tid, "light": tid})
        self.set_pref("vivaldi.themes.current", tid)
        self._wait_js(f"document.getElementById('browser').classList.contains('theme-id-{tid}')", 15)
        time.sleep(0.8)  # let the background image decode and paint
        return tid

    def export_current_settings(self) -> dict:
        """The theme object Vivaldi's Export writes (themePrivate.export drops `defaultBackground`)."""
        cur = self.pref("vivaldi.themes.current")
        theme = next(t for t in self.pref("vivaldi.themes.user") if t["id"] == cur)
        theme.pop("defaultBackground", None)
        return theme

    # --- tabs & window ---------------------------------------------------------------------
    def open_tabs(self, urls: list[str]) -> None:
        for u in urls:
            self.ui.evaluate(f"new Promise(r => chrome.tabs.create({{url: {json.dumps(u)}, active: false}}, r))")
        self._wait_js(f"document.querySelectorAll('.tab-position .tab').length >= {len(urls) + 1}", 15)

    def run_ui(self, js: str):
        return self.ui.evaluate(js)

    def measure(self) -> dict:
        return self.ui.evaluate("""(() => {
          const b = document.getElementById('browser');
          const rect = el => { const r = el.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; };
          const tabs = [...document.querySelectorAll('.tab-position .tab')].map(t => {
            const title = t.querySelector('.title') || t;
            const range = document.createRange(); range.selectNodeContents(title);  // exact text bounds
            return {active: t.classList.contains('active'), color: getComputedStyle(title).color, rect: rect(range)};
          });
          const url = document.querySelector('.UrlBar-UrlField, .UrlField input, input.url');
          const icons = [...document.querySelectorAll('.toolbar .button-toolbar button[name]')].map(btn => ({
            button: btn.getAttribute('name'), color: getComputedStyle(btn).color}));
          return {classes: [...b.classList], tabs, url_color: url ? getComputedStyle(url).color : null, icons};
        })()""")

    def screenshot(self, path: Path) -> Path:
        data = self.ui.send("Page.captureScreenshot", {"format": "png"})["data"]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(base64.b64decode(data))
        return Path(path)

    def set_window(self, width: int, height: int) -> None:
        target = next(t for t in self.targets() if t["url"].endswith("/window.html"))
        win = self.browser.send("Browser.getWindowForTarget", {"targetId": target["id"]})["windowId"]
        self.browser.send("Browser.setWindowBounds", {"windowId": win, "bounds": {"windowState": "normal"}})
        self.browser.send("Browser.setWindowBounds",
                          {"windowId": win, "bounds": {"left": 0, "top": 0, "width": width, "height": height}})
        time.sleep(0.6)

    def startpage_busy_rect(self) -> list[float]:
        """Union (x, y, w, h) of the Start Page navigation, search box, speed dials and widgets."""
        self._wait_js("!!document.querySelector('.SpeedDialView-Head')", 15)
        return self.ui.evaluate("""(() => {
          const els = document.querySelectorAll('.startpage-navigation, .SpeedDialView-Head, .SpeedDial, .dashboard-widget');
          const rs = [...els].map(e => e.getBoundingClientRect()).filter(r => r.width && r.height);
          const x0 = Math.min(...rs.map(r => r.x)), y0 = Math.min(...rs.map(r => r.y));
          const x1 = Math.max(...rs.map(r => r.right)), y1 = Math.max(...rs.map(r => r.bottom));
          return [x0, y0, x1 - x0, y1 - y0];
        })()""")

    # --- settings ---------------------------------------------------------------------------
    def replaceable_buttons(self) -> list[str]:
        """Button ids listed in Settings > Themes > Editor > Icons, in Vivaldi's order, de-duplicated."""
        self.ui.evaluate("new Promise(r => chrome.tabs.create({url: 'vivaldi://settings/themes/', active: true}, r))")
        self._wait_js("[...document.querySelectorAll('.vivaldi-settings .TabbedView-Tab')]"
                      ".some(e => e.innerText.trim() === 'Editor')", 15)
        return self.ui.evaluate("""(async () => {
          const wait = ms => new Promise(r => setTimeout(r, ms));
          const tab = name => [...document.querySelectorAll('.vivaldi-settings .TabbedView-Tab')]
            .find(e => e.innerText.trim() === name);
          tab('Editor').click(); await wait(500);
          tab('Icons').click(); await wait(800);
          const opts = [...document.querySelectorAll('.Button-Selector select option:not([disabled])')];
          return [...new Set(opts.map(o => o.value))];
        })()""")
