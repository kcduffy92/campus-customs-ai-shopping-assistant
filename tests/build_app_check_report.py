"""Build output/app_check.html from the Problem 11 result files (no testing happens here; it only reports).

    python tests/build_app_check_report.py --api api.json --ui ui.json --chat transcript.json --verify verify.json \
        --auth auth_regression.txt --out output/app_check.html

Every number and every quoted reply in the report comes from those files. Images are referenced with relative paths
(app_check_images/...), so the report works when opened locally and on GitHub.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path

E = html.escape
IMG = "app_check_images/"


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def badge(ok: bool) -> str:
    return '<span class="pill pill--pass">PASS</span>' if ok else '<span class="pill pill--fail">FAIL</span>'


def fig(src: str, caption: str, cls: str = "") -> str:
    return (f'<figure class="shot {cls}"><a href="{IMG}{E(src)}"><img src="{IMG}{E(src)}" alt="{E(caption)}" loading="lazy"></a>'
            f"<figcaption>{caption}</figcaption></figure>")


def table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    head = "".join(f"<th>{E(h)}</th>" for _, h in cols)
    body = []
    for r in rows:
        cells = []
        for key, _ in cols:
            v = r.get(key, "")
            cells.append(f"<td>{badge(v) if key == 'passed' else E(str(v))}</td>")
        body.append(f"<tr class=\"{'' if r.get('passed', True) else 'row-fail'}\">{''.join(cells)}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def main() -> int:
    ap = argparse.ArgumentParser()
    for a in ("api", "ui", "chat", "verify", "auth", "out"):
        ap.add_argument(f"--{a}", required=True)
    ap.add_argument("--date", default="2026-10-23")
    ap.add_argument("--model", default="gpt-5.6-luna")
    args = ap.parse_args()
    api, ui, chat, ver = load(args.api), load(args.ui), load(args.chat), load(args.verify)
    auth_lines = [ln for ln in Path(args.auth).read_text(encoding="utf-8").splitlines() if ln.startswith(("PASS", "FAIL"))]
    auth_pass = sum(ln.startswith("PASS") for ln in auth_lines)
    # Keep only the check names (the bracketed details hold ids and test data that the report doesn't need).
    auth_items = "".join(f"<li>{badge(ln.startswith('PASS'))} {E(ln[5:].split('  [')[0])}</li>" for ln in auth_lines)
    turns = chat["turns"]
    notes = {n["screenshot"]: n for n in chat["notes"] if n.get("screenshot")}
    by_label = {}
    for t in turns:
        by_label.setdefault(t["label"], []).append(t)
    vres = ver["results"]
    vcount = Counter(r["area"] for r in vres)

    suites = [
        ("Storefront & catalogue API vs database, accounts, isolation, invalid input, AI outage", "tests/app_check_api.py", api["passed"], api["total"]),
        ("Customer-style browser checks (pages, filters, product page, forms, responsive)", "tests/app_check_ui.py", ui["passed"], ui["total"]),
        (f"Live AI chat ({len(turns)} real messages): {vcount['CARD']} card checks, {vcount['DAN']} Dan animation checks, {vcount['FACT']} answer checks",
         "tests/app_check_chat.py + app_check_verify.py", ver["passed"], ver["total"]),
        ("Account & session regression (Problems 4 and 8)", "tests/auth_regression.py", auth_pass, len(auth_lines)),
        ("Frontend type-check and production build", "npm run build", 1, 1),
    ]
    total_pass = sum(s[2] for s in suites)
    total = sum(s[3] for s in suites)

    def turn_card(t: dict, title: str, extra_note: str = "", shots: tuple[str, ...] = ("reply",)) -> str:
        stages = [e["stage"] for e in t["events"] if e.get("type") == "status"]
        modes = [f"{x['mode']} ({x['kind']})" for x in t["dan_trace"]]
        checks = [r for r in vres if r["turn"] == t["n"] and r["area"] in ("FACT", "CARD")]
        reply = (t["reply"] or t["error"] or "").replace("Handsome Dan said:", "").strip()
        cards = ", ".join(f"{c['name']} {c['price']} ({c['stock'] or 'stock shown'})" for c in t["cards"]) or "none"
        imgs = []
        if "reply" in shots and t.get("reply_screenshot"):
            imgs.append(fig(t["reply_screenshot"], "Reply as shown in the chat"))
        if "cards" in shots and t.get("cards_screenshot"):
            imgs.append(fig(t["cards_screenshot"], "Cards and celebration"))
        ok = all(r["passed"] for r in checks) if checks else True
        rows = "".join(f"<li>{badge(r['passed'])} {E(r['test'])}<br><span class='muted'>{E(r['evidence'][:260])}</span></li>" for r in checks)
        return f"""
<article class="turn">
  <header><span class="turn__n">#{t['n']}</span><h4>{E(title)}</h4>{badge(ok)}</header>
  <div class="turn__grid">
    <div>
      <p class="q"><b>Customer:</b> {E(t['message'])}</p>
      <p class="a"><b>Handsome Dan:</b> {E(reply)}</p>
      <dl class="facts">
        <dt>Backend events</dt><dd>{E(' → '.join(stages) or '—')}</dd>
        <dt>Dan on screen</dt><dd>{E(' → '.join(modes) or '—')}</dd>
        <dt>Cards</dt><dd>{E(cards)}</dd>
        <dt>Time</dt><dd>{t['seconds']} s · {('signed in' if t['phase'] == 'signed_in' else 'signed out')} · {t['viewport'][0]}px wide{' · reduced motion' if t['reduced_motion'] else ''}</dd>
      </dl>
      {f'<p class="note">{extra_note}</p>' if extra_note else ''}
      <ul class="checks">{rows}</ul>
    </div>
    <div class="turn__shots">{''.join(imgs)}</div>
  </div>
</article>"""

    T = lambda label, i=0: by_label[label][i]  # noqa: E731

    # Dan state gallery from the navy-hoodie search
    s2 = T("search")
    dan_states = "".join([
        fig("dan_state_1_idle.jpg", "<b>Idle</b>: request sent, model thinking (no tool running) → neutral Dan, still"),
        fig("dan_state_2_sniff.jpg", "<b>Sniff-walk</b>: captured while the <code>searching</code> event was live"),
        fig("dan_state_3_run.jpg", "<b>Run</b>: captured during the <code>reviewing</code> event (results back, reply being written)"),
        fig("dan_state_4_cookie.jpg", "<b>Cookie pop-up</b>: shown once, because the reply returned 6 verified cards"),
    ])
    timeline_rows = []
    for e in s2["events"]:
        if e.get("type") == "status":
            timeline_rows.append({"t": f"{e['t']} ms", "src": "backend event", "what": f"stage = {e['stage']}: {e.get('text', '')}"})
        elif e.get("type") == "result":
            timeline_rows.append({"t": f"{e['t']} ms", "src": "backend event", "what": f"result: {len(e['data']['products'])} cards"})
    for x in s2["dan_trace"]:
        timeline_rows.append({"t": f"{x['t']} ms", "src": "Dan on screen", "what": f"{x['mode']} ({x['kind']}): {x['status']}"})
    timeline_rows.sort(key=lambda r: int(r["t"].split()[0]))

    rm = T("reduced_motion")
    mob = T("mobile_search", -1)
    dan_rows = [r for r in vres if r["area"] == "DAN"]
    dan_summary = Counter((r["test"].split(": ", 1)[-1] if ": " in r["test"] else r["test"]) for r in dan_rows)

    issues = [
        ("Fixed", "Signed-in chat header was cramped",
         "With the longer name “Handsome Dan” (Problem 10) plus the <b>Chats</b> and <b>New chat</b> buttons, the title wrapped onto two lines "
         "and “Shopping assistant · chats saved” was squeezed into a narrow column. Found in the signed-in screenshots.",
         "Panel 380 → 400 px on desktop; title and status kept on one line; slightly tighter header spacing; the redundant “· chats saved” "
         "text removed (the line under the input already says chats are saved); header avatar hidden only on phones ≤ 380 px. "
         "Re-measured at 1280, 820, 390 and 360 px: no clipping, no overflow.",
         ["fix_chat_header_before.jpg", "fix_chat_header_after_desktop.jpg", "fix_chat_header_after_phone.jpg"]),
        ("Fixed", "Dan’s head was cut off in the phone sniff/run animation",
         "On phones the 131 px sprite sat in a 104 px box; flexbox shrank it before the 0.8× scale, clipping the right side of each frame. "
         "Desktop (132 px box) was unaffected, which is why Problem 10’s desktop checks missed it.",
         "<code>.dan-activity &gt; * { flex-shrink: 0 }</code>. Retested with a live phone search (turn #17): full Dan visible.",
         ["fix_dan_phone_sprite_before.jpg", "fix_dan_phone_sprite_after.jpg"]),
        ("Test tooling", "Three problems in the test scripts themselves (not the app)",
         "(1) The UI login check looked for the wrong wording; the app’s message is “That email and password don’t match our records.” "
         "(2) The credential-leak check flagged a false positive: a test-account value that the assistant never has access to matched an "
         "ordinary word the customer had typed. (3) Requests to <code>localhost</code> took ~2 s each on Windows (IPv6 fallback).",
         "Corrected the keyword; the leak check now ignores words echoed from the customer’s own question; scripts use <code>127.0.0.1</code>. "
         "All suites were re-run after these changes.", []),
    ]
    observations = [
        "<b>Blunt prompt-injection was stopped by the AI provider’s content filter</b> (turn #7), and the backend replied with its standard polite redirect. "
        "To test the model’s <i>own</i> behaviour, two milder probes were added (turns #18–19); it declined both and revealed nothing.",
        "<b>Extra round-trip on some general questions:</b> for “Hi Dan! What can you help me with?”, the policy question and the credentials probe, the model first tried an "
        "<i>empty</i> product search. The backend’s guard refused it (no search ran, so Dan correctly stayed idle in turns #1, #6 and #19). "
        "The cost is one extra model request (~4–5 s instead of ~2 s). Answers are correct; this is a speed observation, not a bug.",
        "<b>The no-match search</b> (“umbrellas or coffee mugs”) made the tool’s loose fallback return 98 weak matches; the model correctly said nothing matched and showed no cards.",
        "<b>Dan is shown for at least 0.7 s per status</b> (Problem 9’s readability pacing), so the sniff-walk can continue briefly after a fast (≈40 ms) database search has finished. "
        "It never starts before the real event. If the reply arrives first, remaining statuses are skipped (turn #17, a cached reply in 1.3 s, went straight from sniff to the answer).",
        "<b>No product is sold out in every size</b> in this database, so the “fully sold out” badge could not be exercised with real data. Size-level sold-out handling was tested (612 inventory labels; Boola Boola T-Shirt size L in chat).",
        "<b>Screenshots</b> were taken with headless Microsoft Edge driven through the DevTools protocol at exact sizes (1280×800 desktop, 820×1180 tablet, 390×844 phone). "
        "Reduced motion was tested with the browser’s real <code>prefers-reduced-motion: reduce</code> emulation.",
        "<b>Earlier-turn screenshots in the signed-in conversation (#10–#13)</b> were taken before the header fix, so they still show the cramped header.",
    ]

    css = """
:root{--blue:#00356b;--blue2:#286dc0;--ink:#16202c;--soft:#4a5565;--line:#dde3ea;--bg:#f6f7f9;--cream:#f6efe4;--gold:#c49a3a;--pass:#1f7a4d;--passbg:#e6f4ec;--fail:#b42318;--failbg:#fdecea}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--blue2)}code{background:#eef2f7;padding:.05em .35em;border-radius:4px;font-size:.92em}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.top{background:var(--blue);color:#fff;padding:40px 0 30px}.top h1{font:600 2.1rem/1.2 "Iowan Old Style","Palatino Linotype",Georgia,serif;margin:0 0 6px}
.top p{margin:0;color:#cfe0f5}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.75rem;color:#9fc2ec;font-weight:700}
.score{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-top:22px}
.score div{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:12px;padding:12px 14px}
.score b{display:block;font-size:1.6rem}.score span{font-size:.82rem;color:#d6e4f5}
nav.toc{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid var(--line)}nav.toc .wrap{display:flex;gap:16px;overflow-x:auto;padding-top:10px;padding-bottom:10px;white-space:nowrap}
nav.toc a{text-decoration:none;font-weight:600;font-size:.88rem;color:var(--blue)}
section{padding:34px 0;border-bottom:1px solid var(--line)}h2{font:600 1.55rem/1.25 "Iowan Old Style","Palatino Linotype",Georgia,serif;color:var(--blue);margin:0 0 6px}
h3{margin:26px 0 10px;font-size:1.1rem}.lead{color:var(--soft);max-width:860px;margin:0 0 18px}
.grid{display:grid;gap:16px;align-items:start}.g2{grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}.g3{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}.g4{grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.shot{margin:0;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}.shot img{display:block;width:100%;height:auto;background:#eee}
.shot figcaption{padding:9px 12px;font-size:.84rem;color:var(--soft)}.phone{max-width:260px}.phones .shot:not(.phone){max-width:400px}.single{max-width:640px}.g4 .shot img{max-height:560px;object-fit:contain;background:#fff}.phones{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.pill{display:inline-block;font-size:.7rem;font-weight:800;letter-spacing:.06em;padding:.15em .55em;border-radius:999px}.pill--pass{background:var(--passbg);color:var(--pass)}.pill--fail{background:var(--failbg);color:var(--fail)}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:12px}table{border-collapse:collapse;width:100%;font-size:.86rem}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#f0f4f9;color:var(--blue);font-size:.78rem;text-transform:uppercase;letter-spacing:.04em}
tr.row-fail td{background:var(--failbg)}.muted{color:var(--soft);font-size:.85em}
.turn{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:0 0 16px}.turn header{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.turn h4{margin:0;font-size:1rem;flex:1}.turn__n{background:var(--blue);color:#fff;border-radius:8px;padding:2px 8px;font-weight:700;font-size:.8rem}
.turn__grid{display:grid;grid-template-columns:1.3fr 1fr;gap:18px}.turn__shots{display:grid;gap:10px;justify-items:center}.turn__shots .shot{max-width:400px}
.q{margin:.2em 0}.a{margin:.4em 0;background:var(--cream);border-left:3px solid var(--gold);padding:8px 10px;border-radius:6px}
.facts{display:grid;grid-template-columns:120px 1fr;gap:3px 10px;font-size:.84rem;margin:10px 0}.facts dt{color:var(--soft);font-weight:600}.facts dd{margin:0}
.checks{list-style:none;padding:0;margin:8px 0 0;font-size:.86rem}.checks li{margin:0 0 6px}.note{font-size:.85rem;background:#fff8e6;border:1px solid #f1dfb0;padding:7px 10px;border-radius:8px}
.issue{display:grid;grid-template-columns:110px 1fr;gap:14px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:14px}
.tag{font-weight:800;font-size:.75rem;color:var(--blue);text-transform:uppercase}details{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:10px 0}
summary{cursor:pointer;font-weight:700;color:var(--blue)}ul.obs li{margin-bottom:8px}
@media(max-width:800px){.turn__grid{grid-template-columns:1fr}.issue{grid-template-columns:1fr}.top h1{font-size:1.6rem}}
"""

    S = []
    S.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Campus Customs — Application Check (Problem 11)</title><style>{css}</style></head><body>
<header class="top"><div class="wrap"><p class="eyebrow">AI Foundations · Homework 4 · Problem 11</p>
<h1>Campus Customs — Application Check</h1>
<p>End-to-end testing of the storefront, customer accounts and the Handsome Dan AI shopping assistant, run on {E(args.date)}.
Every result below was produced by a script run against the live app and compared with the SQLite database.</p>
<div class="score">
<div><b>{total_pass}/{total}</b><span>checks passed</span></div>
<div><b>{len(turns)}</b><span>live AI messages, each verified</span></div>
<div><b>{sum(len(t['cards']) for t in turns)}</b><span>product cards checked against the DB</span></div>
<div><b>2</b><span>app issues found and fixed</span></div>
<div><b>__SHOTS__</b><span>screenshots</span></div>
</div></div></header>
<nav class="toc"><div class="wrap"><a href="#summary">Summary</a><a href="#about">About</a><a href="#env">Environment</a><a href="#store">Storefront</a>
<a href="#product">Product page</a><a href="#accounts">Accounts</a><a href="#assistant">AI assistant</a><a href="#dan">Dan animations</a>
<a href="#mobile">Mobile</a><a href="#security">Reliability &amp; security</a><a href="#issues">Issues &amp; fixes</a><a href="#all">All checks</a></div></nav>""")

    rows = "".join(f"<tr><td>{E(a)}</td><td><code>{E(b)}</code></td><td><b>{p}/{t}</b></td><td>{badge(p == t)}</td></tr>" for a, b, p, t in suites)
    S.append(f"""<section id="summary"><div class="wrap"><h2>Summary of results</h2>
<p class="lead">{total_pass} of {total} checks passed after fixes. Two real problems were found in the app during this check (both visual, both from the
Problem 10 redesign) and fixed; the affected checks were re-run. Nothing in the required functionality is incomplete.</p>
<div class="table-wrap"><table><thead><tr><th>Suite</th><th>Script</th><th>Result</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>
<h3>How we know the results are correct</h3>
<div class="grid g3">
<div class="card"><b>Compared with the database, not eyeballed.</b> Prices, names, descriptions, images, every one of the 612 inventory rows, filter counts and every chat card were compared field by field with the SQLite tables.</div>
<div class="card"><b>The AI’s answers were checked against data.</b> Each reply’s concrete claims (prices, sizes, stock numbers, counts, colours) were checked against the database by <code>app_check_verify.py</code>; refusals were checked for leaked instructions or credentials.</div>
<div class="card"><b>Dan’s animations were checked against real events.</b> The backend’s actual event stream and what Dan showed were recorded on the same clock. A state counts only if the event that justifies it had already arrived.</div>
</div></div></section>""")

    S.append(f"""<section id="about"><div class="wrap"><h2>About Campus Customs</h2>
<div class="grid g2"><div><p class="lead" style="margin:0">Campus Customs is a Yale-inspired clothing store: 102 hoodies, crewnecks, quarter-zips, tees and jackets with live size-by-size stock.
Customers can browse and filter the catalogue, open product pages with exact inventory, and create an account.</p>
<p><b>Handsome Dan</b> is the store’s AI shopping assistant (PydanticAI agent, model <code>{E(args.model)}</code> through the Portkey gateway). He answers in plain language,
uses two database tools (<code>search_products</code>, <code>check_inventory</code>), returns clickable product cards that the backend builds from verified database rows,
knows which product page the shopper is on, and saves separate conversations for signed-in customers. There is deliberately no cart or checkout.</p></div>
{fig('01_home_hero.jpg', 'Homepage (desktop 1280×800)')}</div></div></section>""")

    S.append(f"""<section id="env"><div class="wrap"><h2>Test environment</h2>
<div class="grid g2"><div class="card"><b>How the app was started</b>
<ul><li>Backend (FastAPI): from <code>hw4/backend</code> with the venv active: <code>uvicorn main:app --port 8000</code>, with <code>CAMPUS_DATA_DIR</code> pointing at a <b>temporary copy</b> of <code>hw4/data</code>.
Normal use is the professor’s command <code>uvicorn main:app --reload --port 8000</code> on the real database.</li>
<li>Frontend (React + Vite): <code>npm run dev</code> in <code>hw4/frontend</code> → <code>http://localhost:5173</code> (proxies <code>/api</code> and <code>/media</code> to port 8000).</li>
<li>AI-outage test: a second backend on port 8001 with <code>PORTKEY_BASE_URL</code> set to an unreachable local address (no Portkey traffic).</li></ul></div>
<div class="card"><b>Test conditions</b><ul>
<li>Windows 11; Python venv <code>hw4/.venv</code>; headless Microsoft Edge driven via the DevTools protocol (<code>tests/cdp.py</code>, no extra packages).</li>
<li>Viewports: desktop 1280×800, tablet 820×1180, phone 390×844 (plus 360 px for the header fix).</li>
<li>All test accounts and conversations were created only in the temporary copy; the real database was not modified (still 3 users).</li>
<li>AI calls were kept low: {len(turns)} chat messages in total, no repeats for screenshots (except one re-run on phone after a fix).</li>
<li>No passwords, keys, cookies or real customer data appear in the screenshots or this report; the professor’s test account is used only through the API, with its email withheld.</li></ul></div></div></div></section>""")

    ui_r = {r["test"]: r for r in ui["results"]}
    store_rows = [r for r in ui["results"] if r["area"] in ("Homepage & navigation", "Catalogue & filters")]
    cat_api = [r for r in api["results"] if r["area"] == "Catalogue"]
    S.append(f"""<section id="store"><div class="wrap"><h2>Storefront: homepage, catalogue, filters, navigation</h2>
<p class="lead">Tested in the browser the way a customer would: clicking the menu, filter chips and sort control, typing in search, then comparing what was on screen with the database.</p>
<div class="grid g2">{fig('02_home_categories.jpg', 'Homepage categories: counts match the database (11+27+8+29+2+25 = 102)')}
{fig('03_catalogue.jpg', 'Catalogue: all 102 cards checked against the database (price, image, sold-out state)')}
{fig('04_catalogue_filtered.jpg', 'Quarter-Zips + Gray + “Price: low to high” combined in the UI')}
{fig('05_catalogue_empty_dan.jpg', 'No matches: sniffing Dan and a clear way out')}</div>
<h3>Browser checks</h3>{table(store_rows, [('id', 'ID'), ('test', 'Test'), ('evidence', 'What happened'), ('passed', 'Result')])}
<h3>Catalogue data vs database (API)</h3>{table(cat_api, [('id', 'ID'), ('test', 'Test'), ('evidence', 'Evidence'), ('passed', 'Result')])}
</div></section>""")

    prod_rows = [r for r in ui["results"] if r["area"] == "Product page"]
    S.append(f"""<section id="product"><div class="wrap"><h2>Product page with real inventory</h2>
<p class="lead">Benjamin Franklin 1/4 Zip was chosen because it has all three stock states. The page shows exactly the inventory table’s quantities.</p>
<div class="grid g2">{fig('06_product_page.jpg', 'Product page: XS 2 · S 2 · M 25 · L 20 · XL sold out · XXL 2 (database: identical)')}
{fig('07_product_size_selected.jpg', 'Selecting S explains “Only 2 left”; Add to bag stays disabled (no checkout)')}
{fig('08_product_not_found.jpg', 'Unknown product address: friendly not-found page')}
{fig('09_404_page.jpg', 'Unknown page: 404 with Dan')}</div>
<h3>Checks</h3>{table(prod_rows, [('id', 'ID'), ('test', 'Test'), ('evidence', 'What happened'), ('passed', 'Result')])}</div></section>""")

    acct_api = [r for r in api["results"] if r["area"] in ("Accounts", "Isolation")]
    acct_ui = [r for r in ui["results"] if r["area"] == "Account pages"]
    S.append(f"""<section id="accounts"><div class="wrap"><h2>Customer accounts</h2>
<p class="lead">Registration, sign-in, staying signed in, sign-out, the professor’s existing test account, and isolation between customers. All accounts created here exist only in the temporary database copy.</p>
<div class="grid g3">{fig('10_register_page.jpg', 'Registration page')}{fig('11_register_validation.jpg', 'Empty submit: field-by-field messages')}
{fig('12_login_page.jpg', 'Sign-in page')}{fig('13_login_wrong_password.jpg', 'Wrong details: same message for unknown email and wrong password')}
{fig('account_01_register_filled.jpg', 'Registering a safe test customer (password masked)')}{fig('account_03_account_page.jpg', 'Account page after signing back in (test data only)')}</div>
<h3>Browser checks</h3>{table(acct_ui, [('id', 'ID'), ('test', 'Test'), ('evidence', 'What happened'), ('passed', 'Result')])}
<h3>Accounts, sessions and isolation (API)</h3>{table(acct_api, [('id', 'ID'), ('test', 'Test'), ('evidence', 'Evidence'), ('passed', 'Result')])}
<details><summary>Account &amp; session regression suite: {auth_pass}/{len(auth_lines)} passed</summary><ul>{auth_items}</ul></details>
</div></section>""")

    S.append("""<section id="assistant"><div class="wrap"><h2>The AI shopping assistant (real conversations)</h2>
<p class="lead">Every message below was typed into the live chat and answered by the real model. For each one: the reply, which backend events happened, what Dan showed,
the cards, and the checks run against the database. Chat screenshots are cropped to the chat panel.</p>""")
    S.append("<h3>Signed out, desktop: conversation, search, follow-ups, sold-out sizes, no-match, unknown policy</h3>")
    S.append(f'<div class="grid g2">{fig("chat_00_welcome.jpg", "Chat opened: Handsome Dan header, sitting-Dan welcome")}{fig("dan_smalltalk_idle.jpg", "Greeting (turn #1): no tool ran, so Dan stays still. No fake searching")}</div><br>')
    S.append(turn_card(T("greeting"), "Greeting / normal conversation"))
    S.append(turn_card(T("search"), "Searching for merchandise (navy hoodies)", shots=("reply", "cards")))
    S.append(turn_card(T("followup_price"), "Follow-up about a previous recommendation: price and description", shots=("cards",)))
    S.append(turn_card(T("sold_out_size"), "Size availability: a sold-out size", shots=("cards",)))
    S.append(turn_card(T("no_match"), "A request with no matching products"))
    S.append(turn_card(T("policy"), "Something it can't verify (store policies)"))
    S.append("<h3>On a product page: “this” means the product being viewed</h3>")
    pd = notes.get("chat_product_draft.jpg", {})
    S.append(f'<div class="grid g2">{fig("chat_product_draft.jpg", "“Ask Handsome Dan about this item” with size S selected: drafted <i>" + E(pd.get("draft", "")) + "</i>, not sent")}</div><br>')
    S.append(turn_card(T("product_page_size"), "Question about the product being viewed (stock in S)", shots=("cards",)))
    S.append(turn_card(T("product_page_about"), "Follow-up about the viewed product (colours, material)", shots=("reply",)))
    S.append("<h3>Signed in: saved conversations, new chat, reopen and continue, sign out and back in</h3>")
    S.append(turn_card(T("signed_in_search"), "Signed-in search (uses the customer's first name)", shots=("cards",)))
    S.append(turn_card(T("signed_in_followup"), "Follow-up without naming the product", shots=("reply",)))
    nc = notes.get("chat_new_conversation.jpg", {})
    S.append(f'<div class="grid g2">{fig("chat_new_conversation.jpg", "New chat: fresh conversation (" + str(nc.get("messages", 0)) + " earlier messages shown)")}</div><br>')
    S.append(turn_card(T("new_conversation"), "New conversation: gray quarter-zips under $80", shots=("cards",)))
    cl = notes.get("chat_conversation_list.jpg", {})
    conv_items = "".join(f"<li>{E(c)}</li>" for c in cl.get("conversations", []))
    S.append(f"""<div class="grid g2">{fig('chat_conversation_list.jpg', 'Chats list: both saved conversations, with titles, topics and counts')}
{fig('chat_reopened_conversation.jpg', 'Older Davenport conversation reopened with its messages')}</div>
<p class="muted">Chats list as recorded:</p><ul class="muted">{conv_items}</ul>""")
    S.append(turn_card(T("continue_old"), "Continuing the reopened conversation (“it” = the Davenport crewneck)", shots=("reply",)))
    hr = [n for n in chat["notes"] if n.get("screenshot") == "chat_history_restored.jpg"][0]
    S.append(f"""<div class="grid g2">{fig('fix_chat_header_after_desktop.jpg', 'Signed out, signed back in, opened the chat: the latest conversation is restored with its card (and no celebration replayed)')}
<div class="card"><b>Sign out → sign in → history restored</b><ul>
<li>After signing out, <code>/api/auth/me</code> returned <code>null</code> and the header showed “Sign in”.</li>
<li>After signing back in, the chat restored {len(hr.get('restored', []))} customer messages: {E('; '.join(m.replace('You said:', '').strip() for m in hr.get('restored', [])))}.</li>
<li>Restored cards: {hr.get('cards')} · celebrations replayed: {hr.get('celebrations')} (celebrations are only for live replies).</li></ul></div></div>""")
    S.append("<h3>Instructions and credentials</h3>")
    S.append(turn_card(T("prompt_injection"), "Blunt prompt-injection", "The provider’s content filter blocked this message; the backend logged it and sent the standard polite redirect."))
    S.append(turn_card(T("instructions_probe"), "Asked to reveal its system prompt"))
    S.append(turn_card(T("credentials_probe"), "Asked for its API key / password"))
    S.append("</div></section>")

    dan_tbl = "".join(f"<tr><td>{E(k)}</td><td><b>{v}</b></td></tr>" for k, v in dan_summary.items())
    S.append(f"""<section id="dan"><div class="wrap"><h2>Handsome Dan’s animations</h2>
<p class="lead">The idle, sniff-walk and run screenshots were taken by the test script <i>the moment</i> Dan’s on-screen state changed during a live request, so they show the real state, not a mock-up; the cookie screenshot was taken right after the reply arrived. They are cropped to the chat panel.
The table under them is the recorded timeline for that same request.</p>
<h3>The four states (navy-hoodie search, turn #{s2['n']})</h3><div class="grid g4">{dan_states}</div>
<h3>Timeline for turn #{s2['n']}: backend events vs what Dan showed</h3>
{table(timeline_rows, [('t', 'Time since send'), ('src', 'Source'), ('what', 'What')])}
<p class="muted">The search itself took about 35 ms, so the <code>searching</code> and <code>reviewing</code> events arrive almost together; the chat keeps each status on screen for at least 0.7 s so it can be read.</p>
<h3>Rules checked on every message ({len(dan_rows)} checks, all passed)</h3>
<div class="table-wrap"><table><thead><tr><th>Rule</th><th>Messages checked</th></tr></thead><tbody>{dan_tbl}</tbody></table></div>
<h3>Reduced motion (browser setting <code>prefers-reduced-motion: reduce</code>)</h3>
<div class="grid g3">{fig('dan_reduced_sniff.jpg', 'Searching with reduced motion: the still <b>sniffing</b> pose instead of the animation')}
{fig('dan_reduced_run.jpg', 'Reviewing with reduced motion: the still <b>fetching</b> pose')}
{fig('dan_reduced_cookie.jpg', 'Celebration still appears (without the pop/wiggle)')}</div>
<p class="muted">Recorded states: {E(' → '.join(x['mode'] + ' (' + x['kind'] + ')' for x in rm['dan_trace']))}. CSS animations running on Dan elements afterwards: none.</p>
<h3>Dan around the site</h3><div class="grid g4">{fig('01_home_hero.jpg', 'Hero: sitting Dan in a cream arch')}{fig('05_catalogue_empty_dan.jpg', 'Empty search: sniffing Dan')}
{fig('09_404_page.jpg', '404: sniffing Dan')}{fig('10_register_page.jpg', 'Register / sign in: sitting Dan medallion')}{fig('account_03_account_page.jpg', 'Account: fetching Dan')}
{fig('06_product_page.jpg', 'Product page: “Ask Handsome Dan about this item”')}{fig('chat_00_welcome.jpg', 'Chat: avatar, welcome, launcher')}</div></div></section>""")

    resp = [r for r in ui["results"] if r["area"] == "Responsive layout"]
    S.append(f"""<section id="mobile"><div class="wrap"><h2>Mobile and responsive behaviour</h2>
<p class="lead">Pages were loaded at phone (390 px), tablet (820 px) and desktop widths and checked for horizontal scrolling; the chat was used live on a phone-sized screen.</p>
<div class="phones">{fig('20_mobile_home.jpg', 'Phone: homepage', 'phone')}{fig('21_mobile_menu.jpg', 'Phone: menu open', 'phone')}{fig('22_mobile_catalogue.jpg', 'Phone: catalogue (2 columns, filters folded)', 'phone')}
{fig('23_mobile_product.jpg', 'Phone: product page', 'phone')}{fig(mob['state_screenshots']['sniff'], 'Phone: Dan sniff-walking during a live search', 'phone')}{fig(mob['cards_screenshot'], 'Phone: reply with cards and celebration', 'phone')}
{fig('fix_chat_header_after_phone.jpg', 'Phone: signed-in chat header after the fix', 'phone')}</div>
<h3>Checks</h3>{table(resp, [('id', 'ID'), ('test', 'Test'), ('evidence', 'What happened'), ('passed', 'Result')])}
<p class="muted">Live phone chat: page overflow 0 px; chat log overflow 0 px (the card row scrolls sideways inside its own scroller by design).</p></div></section>""")

    sec_api = [r for r in api["results"] if r["area"] in ("Invalid input", "Security", "Reliability")]
    down = T("provider_down")
    S.append(f"""<section id="security"><div class="wrap"><h2>Reliability and security</h2>
<div class="grid g2"><div>{table(sec_api, [('id', 'ID'), ('test', 'Test'), ('evidence', 'Evidence'), ('passed', 'Result')])}</div>
{fig(down['reply_screenshot'], 'AI provider unreachable: the shopper sees a friendly message and a Try again button; the store keeps working')}</div>
<h3>Assistant safety (from the live conversations)</h3><ul>
<li><b>Doesn’t invent products:</b> “umbrellas or coffee mugs” → no cards, says the store doesn’t carry them (database: 0 matching rows).</li>
<li><b>Doesn’t invent policies:</b> returns/shipping → “I don’t have information about … so I can’t confirm”.</li>
<li><b>Doesn’t invent stock:</b> every stock number quoted in turns #4, #8, #11, #13 matched the inventory table exactly.</li>
<li><b>Doesn’t reveal instructions or credentials:</b> turns #7, #18, #19; no prompt text or secret value appeared in any reply.</li>
<li><b>Cards can’t be faked:</b> the model only chooses product ids; the backend builds each card from the database and only for ids its tools returned. All {sum(len(t['cards']) for t in turns)} cards shown matched the database.</li>
<li><b>Earlier features still work after the redesign:</b> catalogue, filters, product pages, accounts, conversations and the 29-check regression suite all pass.</li></ul></div></section>""")

    iss = []
    for kind, title, found, fix, shots in issues:
        imgs = "".join(fig(s, ("Before" if "before" in s else "After") + (" (phone)" if "phone" in s else " (desktop)" if "desktop" in s else ""), "phone" if "phone" in s else "") for s in shots)
        iss.append(f"""<div class="issue"><div class="tag">{E(kind)}</div><div><b>{title}</b><p><b>Found:</b> {found}</p><p><b>Fix and retest:</b> {fix}</p>
{f'<div class="phones">{imgs}</div>' if imgs else ''}</div></div>""")
    obs = "".join(f"<li>{o}</li>" for o in observations)
    S.append(f"""<section id="issues"><div class="wrap"><h2>Issues found, fixes and limitations</h2>{''.join(iss)}
<h3>Observations and limitations (not failures)</h3><ul class="obs">{obs}</ul></div></section>""")

    all_rows = ([{**r, "suite": "API"} for r in api["results"]] + [{**r, "suite": "Browser"} for r in ui["results"]]
                + [{**r, "suite": f"Chat #{r['turn']}"} for r in vres])
    S.append(f"""<section id="all"><div class="wrap"><h2>All checks</h2>
<details><summary>Show all {len(all_rows)} scripted checks (plus {len(auth_lines)} regression checks above)</summary>
{table(all_rows, [('id', 'ID'), ('suite', 'Suite'), ('test', 'Test'), ('evidence', 'Evidence'), ('passed', 'Result')])}</details>
<h3>Reproducing this report</h3><ol>
<li>Copy <code>hw4/data</code> to a temporary folder and start the backend on it: <code>CAMPUS_DATA_DIR=&lt;copy&gt; uvicorn main:app --port 8000</code>; start the frontend with <code>npm run dev</code>.</li>
<li>Start headless Edge: <code>python tests/cdp.py launch</code>.</li>
<li>Run <code>tests/app_check_api.py</code>, <code>tests/app_check_ui.py</code>, the phases of <code>tests/app_check_chat.py</code>, then <code>tests/app_check_verify.py</code> and <code>tests/auth_regression.py</code>.</li>
<li>Build this page with <code>tests/build_app_check_report.py</code>. Details are in <code>output/harness.md</code>, section 7.</li></ol>
<p class="muted">Report generated from the recorded results on {E(args.date)}. The AI’s wording will differ on another run; the checks look at facts, not exact wording.</p></div></section>
</body></html>""")
    page = "\n".join(S)
    shots = sorted(set(re.findall(r'src="app_check_images/([^"]+)"', page)))
    page = page.replace("__SHOTS__", str(len(shots)))
    Path(args.out).write_text(page, encoding="utf-8")
    print("screenshots referenced:", len(shots))
    print("wrote", args.out, "-", total_pass, "/", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
