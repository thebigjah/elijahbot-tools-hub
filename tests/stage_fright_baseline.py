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

tmp = pathlib.Path(tempfile.mkdtemp())
def wav(path, amp):
    with wave.open(str(path), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000)
        w.writeframes(b"".join(struct.pack("<h", int(amp * math.sin(2 * math.pi * 160 * i / 48000))) for i in range(48000 * 30)))
    return path
tone, silence = wav(tmp / "tone.wav", 9000), wav(tmp / "silence.wav", 0)

def capture(pg, words=None):
    pg.click("#rec-btn")
    pg.wait_for_function("document.getElementById('rec-btn').classList.contains('recording')", timeout=10000)
    if words: pg.evaluate(f"transcript = {json.dumps(words)}")
    pg.wait_for_function("document.getElementById('mode-indicator').textContent !== 'analyzing' && !document.getElementById('rec-btn').classList.contains('recording')", timeout=40000)
    pg.wait_for_timeout(500)

def browser(p, audio):
    b = p.chromium.launch(headless=True, channel="chrome", args=[
        "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
        f"--use-file-for-fake-audio-capture={audio}", "--autoplay-policy=no-user-gesture-required"])
    pg = b.new_context(permissions=["microphone"]).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_timeout(800)
    return b, pg, errs

def stored(pg):
    return json.loads(pg.evaluate("localStorage.getItem('stage-fright-v0') || '{}'"))

with sync_playwright() as p:
    b, pg, errs = browser(p, silence)
    capture(pg)
    assert not stored(pg).get("baseline"), "a silent take became the baseline"
    assert "nearly silent" in pg.inner_text("#status"), pg.inner_text("#status")
    assert "analyzing" not in pg.inner_text("#scope-readout").lower()
    b.close()
    print("ok: silent take refused, readout reset")

    b, pg, errs = browser(p, tone)
    capture(pg)  # sound but no words, as when recognition fails
    base = stored(pg)["baseline"]
    assert base["noTranscript"] and "no words" in pg.inner_text("#status"), pg.inner_text("#status")
    print(f"ok: wordless take saved a pitch and volume baseline (volCV {base['volCV']:.2f}, pitch {base['pitchMedian']:.0f} Hz)")
    assert base["volCV"] < 0.5, f"steady tone read as unsteady volume (CV {base['volCV']:.2f})"
    assert 150 <= base["pitchMedian"] <= 170, base["pitchMedian"]

    capture(pg, " ".join(["steady"] * 40))
    grid = pg.inner_text("#metric-grid")
    assert "100% below" not in pg.inner_text("#diagnoses"), "word rate compared against a baseline with no words"
    assert not errs, errs
    b.close()
print("ok: later take compares pitch and volume without a false word-rate alert")
