# Magic Closet: choosing Formal on the Pick tab must pick formal items, not casual ones.
# Run: ~/.cosmic/whop/venv/bin/python tests/magic_closet_occasion.py  (serves public/ on a local port)
import http.server, threading, functools, pathlib, sys
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).resolve().parent.parent / "public"
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/magic-closet/"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, channel="chrome")
    pg = b.new_page()
    pg.on("dialog", lambda d: d.dismiss())
    pg.goto(url)
    pg.evaluate("""async () => {
      const base = { color:'black', seasons:['spring','summer','fall','winter'], addedAt:Date.now(), lastWorn:null, wornCount:0 };
      for (const [id, type, formal] of [['f1','top','formal'],['f2','bottom','formal'],['f3','shoes','formal'],
                                         ['c1','top','casual'],['c2','bottom','casual'],['c3','shoes','casual']])
        await dbPut('items', { ...base, id, name: formal + ' ' + type, type, formal });
    }""")
    pg.evaluate("setTab('pick')")
    pg.locator("#pick-formal .tag-chip", has_text="Formal").first.click()
    assert pg.evaluate("state.pick.formal") == "formal", pg.evaluate("state.pick.formal")
    assert pg.evaluate("state.selected.formal") is None, "Pick row wrote to the Add form"
    names = set()
    for _ in range(5):
        pg.evaluate("pickOutfit()")
        pg.wait_for_timeout(150)
        names |= set(pg.locator("body").inner_text().split("\n"))
    picked = [n for n in names if n.strip() in ("formal top","formal bottom","formal shoes","casual top","casual bottom","casual shoes")]
    assert picked and all(n.startswith("formal") for n in picked), picked
    b.close()
print("ok: Formal pick returns only formal items")
