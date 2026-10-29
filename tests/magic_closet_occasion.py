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

    # Rainy prefers rain-ready shoes and outer layers, and an accessory joins the outfit.
    pg.evaluate("""async () => {
      const base = { color:'black', seasons:['fall','spring'], formal:'casual', addedAt:Date.now(), lastWorn:null, wornCount:0 };
      for (const [id, name, type, rainOk] of [['r1','boots','shoes',true],['r2','suede loafers','shoes',false],
                                               ['r3','rain shell','outer',true],['r4','wool coat','outer',false],
                                               ['r5','watch','accessory',false]])
        await dbPut('items', { ...base, id, name, type, rainOk });
    }""")
    pg.locator("#pick-weather .tag-chip", has_text="Cool").click()
    pg.locator("#pick-rain .tag-chip", has_text="Raining").click()
    pg.locator("#pick-formal .tag-chip", has_text="Casual").first.click()
    seen = set()
    for _ in range(15):
        pg.evaluate("pickOutfit()"); pg.wait_for_timeout(120)
        seen |= set(pg.inner_text("#outfit-grid").split("\n"))
    assert "boots" in seen and "rain shell" in seen, seen
    assert "suede loafers" not in seen and "wool coat" not in seen, seen
    assert "watch" in seen, seen

    # A dress on a cold day still gets a coat, and rain does not drop the temperature's clothes.
    pg.evaluate("""async () => {
      const base = { color:'black', formal:'smart-casual', addedAt:Date.now(), lastWorn:null, wornCount:0 };
      await dbPut('items', { ...base, id:'d1', name:'wool dress', type:'dress', seasons:['winter'] });
      await dbPut('items', { ...base, id:'d2', name:'parka', type:'outer', seasons:['winter'], rainOk:false });
      await dbPut('items', { ...base, id:'d3', name:'winter boots', type:'shoes', seasons:['winter'], rainOk:true });
    }""")
    pg.locator("#pick-weather .tag-chip", has_text="Cold").click()
    pg.locator("#pick-formal .tag-chip", has_text="Smart-casual").click()
    dress_seen = False
    for _ in range(60):
        pg.evaluate("pickOutfit()"); pg.wait_for_timeout(60)
        grid = pg.inner_text("#outfit-grid")
        if "wool dress" in grid:
            dress_seen = True
            assert "parka" in grid, grid
    assert dress_seen, "the dress never came up in 60 cold picks"

    # A dress that is the only complete outfit gets picked every time.
    pg.evaluate("""async () => { for (const it of await dbGetAll('items')) await dbDelete('items', it.id); }""")
    pg.evaluate("""async () => {
      const base = { color:'black', formal:'casual', seasons:['summer','spring'], addedAt:Date.now(), lastWorn:null, wornCount:0 };
      await dbPut('items', { ...base, id:'s1', name:'sun dress', type:'dress' });
      await dbPut('items', { ...base, id:'s2', name:'sandals', type:'shoes' });
    }""")
    pg.locator("#pick-weather .tag-chip", has_text="Warm").click()
    pg.locator("#pick-rain .tag-chip", has_text="Dry").click()
    pg.locator("#pick-formal .tag-chip", has_text="Casual").first.click()
    for _ in range(20):
        pg.evaluate("pickOutfit()"); pg.wait_for_timeout(60)
        assert "sun dress" in pg.inner_text("#outfit-grid"), "a lone dress was skipped"

    # Logging twice for the same outfit counts once.
    pg.evaluate("pickOutfit()"); pg.wait_for_timeout(100)
    pg.evaluate("Promise.all([logOutfit(), logOutfit()])"); pg.wait_for_timeout(300)
    counts = pg.evaluate("dbGetAll('items').then(xs => xs.filter(x => x.wornCount).map(x => x.wornCount))")
    assert counts and max(counts) == 1, counts

    # A closet with no bottoms for the occasion says so.
    pg.locator("#pick-rain .tag-chip", has_text="Dry").click()
    pg.locator("#pick-formal .tag-chip", has_text="Business").click()
    pg.evaluate("pickOutfit()"); pg.wait_for_timeout(150)
    note = pg.inner_text("#outfit-note")
    assert "top" in note and "bottom" in note, note
    b.close()
print("ok: occasion, rain, accessories, dress with a coat, single wear log, missing-pieces note")
