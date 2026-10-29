# Stage Fright: a steady tone must read as steady volume (mic processing off), a silent or
# wordless first capture must not become the baseline, and the readout must not stick on "analyzing".
# Run: ~/.cosmic/whop/venv/bin/python tests/stage_fright_baseline.py   (takes about 50 s)
import http.server, threading, functools, pathlib, tempfile, wave, math, struct, json
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).resolve().parent.parent / "public"
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(root)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/stage-fright/"

tone = pathlib.Path(tempfile.mkdtemp()) / "tone.wav"
with wave.open(str(tone), "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000)
    w.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(2 * math.pi * 160 * i / 48000))) for i in range(48000 * 30)))

def capture(pg, words=None):
    pg.click("#rec-btn")
    pg.wait_for_function("document.getElementById('rec-btn').classList.contains('recording')", timeout=10000)
    if words: pg.evaluate(f"transcript = {json.dumps(words)}")
    pg.wait_for_function("document.getElementById('mode-indicator').textContent !== 'analyzing' && !document.getElementById('rec-btn').classList.contains('recording')", timeout=40000)
    pg.wait_for_timeout(500)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome", args=[
        "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
        f"--use-file-for-fake-audio-capture={tone}", "--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(permissions=["microphone"])
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_timeout(800)

    capture(pg)  # no words: refused
    store = json.loads(pg.evaluate("localStorage.getItem('stage-fright-v0') || '{}'"))
    assert not store.get("baseline"), "a wordless capture became the baseline"
    assert "Not saved as a baseline" in pg.inner_text("#status"), pg.inner_text("#status")
    assert "analyzing" not in pg.inner_text("#scope-readout").lower(), pg.inner_text("#scope-readout")
    print("ok: wordless capture refused, readout reset")

    capture(pg, " ".join(["steady"] * 40))
    base = json.loads(pg.evaluate("localStorage.getItem('stage-fright-v0')"))["baseline"]
    print(f"steady tone: volCV {base['volCV']:.2f}, pitch {base['pitchMedian']:.0f} Hz")
    assert base["volCV"] < 0.5, f"steady tone read as unsteady volume (CV {base['volCV']:.2f})"
    assert 150 <= base["pitchMedian"] <= 170, base["pitchMedian"]
    assert not errs, errs
    b.close()
print("ok: steady tone reads steady")
