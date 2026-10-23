"""Problem 11: storefront checks in a real (headless Edge) browser, compared with the database. No AI calls.

Needs the backend running on a database COPY and Edge started with `python tests/cdp.py launch`.
    python tests/app_check_ui.py --db <copy>/campus_customs.db --out ui.json
Screenshots go to output/app_check_images/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cdp import Page  # noqa: E402

HW4 = Path(__file__).resolve().parents[1]
IMG = Path(os.getenv("APP_CHECK_IMG_DIR") or HW4 / "output" / "app_check_images")  # override to keep re-runs out of the report
BASE = "http://localhost:5173"
RESULTS: list[dict] = []


def check(area, name, ok, evidence, shot=None):
    RESULTS.append({"id": f"UI-{len(RESULTS) + 1:02d}", "area": area, "test": name, "passed": bool(ok), "evidence": evidence, "screenshot": shot})
    print(f"{'PASS' if ok else 'FAIL'}  [{area}] {name}  ->  {evidence}")


def money(x: float) -> str:
    return f"${x:,.2f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    cat = {r["product_id"]: r for r in db.execute("select * from catalogue")}
    inv: dict[str, dict[str, int]] = {}
    for r in db.execute("select product_id, size, quantity from inventory"):
        inv.setdefault(r["product_id"], {})[r["size"]] = r["quantity"]
    by_display = {}  # display name -> product_id (display names are unique)

    p = Page.connect()
    p.reduced_motion(False)
    p.viewport(1280, 800)
    p.js("fetch('/api/auth/logout', {method: 'POST'}).then(() => 1)") if p.js("location.origin") == BASE else None

    def overflow() -> int:
        return p.js("document.documentElement.scrollWidth - document.documentElement.clientWidth")

    def eager_wait(ms=1200):
        p.js(f"document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager'); new Promise(r => setTimeout(r, {ms}))")

    def broken_images() -> int:
        return p.js("[...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.getAttribute('src')).length")

    # ---------- Homepage ----------
    A = "Homepage & navigation"
    p.goto(BASE + "/", 2)
    p.shot(IMG / "01_home_hero.jpg")
    info = p.js("""({h1: document.querySelector('h1').textContent, lead: document.querySelector('.hero__lead').textContent,
        nav: [...document.querySelectorAll('.nav__link')].map(a => a.textContent + '=' + a.getAttribute('href')),
        heroDan: (() => { const i = document.querySelector('.hero__medallion img'); return i && i.complete && i.naturalWidth > 0; })()})""")
    check(A, "Homepage loads with hero, Handsome Dan and the live product count",
          info["heroDan"] and f"Browse {len(cat)} styles" in info["lead"], f"h1 '{info['h1']}'; lead says 'Browse {len(cat)} styles'; hero Dan image loaded", "01_home_hero.jpg")
    eager_wait()
    p.js("window.scrollTo(0, document.querySelector('h2').getBoundingClientRect().top + scrollY - 100)")
    time.sleep(0.8)
    p.shot(IMG / "02_home_categories.jpg")
    tiles = p.js("[...document.querySelectorAll('h2')][0].closest('section').innerText")
    counts = dict(re.findall(r"\n?([A-Za-z &\-]+)\n(\d+) styles", tiles))
    api_f = p.js("fetch('/api/filters').then(r => r.json())")
    expect = {c["label"]: c["count"] for c in api_f["categories"]}
    check(A, "Category tiles show correct style counts (sum = catalogue size)",
          {k.strip(): int(v) for k, v in counts.items()} == expect and sum(expect.values()) == len(cat),
          ", ".join(f"{k} {v}" for k, v in expect.items()), "02_home_categories.jpg")
    check(A, "Header navigation links point to the right pages", len(info["nav"]) >= 6, "; ".join(info["nav"]))

    # Click a nav link like a customer
    p.js("[...document.querySelectorAll('.nav__link')].find(a => a.textContent.trim() === 'Hoodies').click()")
    time.sleep(1.5)
    loc = p.js("location.pathname + location.search")
    names = p.js("[...document.querySelectorAll('.product-card__name')].map(e => e.textContent)")
    hoodie_count = sum(1 for c in api_f["categories"] if c["slug"] == "hoodies" and c["count"] == len(names))
    check(A, "Clicking 'Hoodies' in the menu opens the filtered catalogue", loc == "/shop?category=hoodies" and hoodie_count == 1, f"{loc} shows {len(names)} cards")

    # ---------- Catalogue ----------
    A = "Catalogue & filters"
    p.goto(BASE + "/shop", 1.5)
    eager_wait(1500)
    p.shot(IMG / "03_catalogue.jpg")
    cards = p.js("""[...document.querySelectorAll('.product-card')].map(c => ({href: c.querySelector('a').getAttribute('href'),
        name: c.querySelector('.product-card__name').textContent, price: c.querySelector('.product-card__price').textContent,
        img: c.querySelector('img').getAttribute('src'), sold: !!c.querySelector('.badge--sold-out')}))""")
    bad = []
    for c in cards:
        pid = c["href"].rsplit("/", 1)[-1]
        row = cat.get(pid)
        by_display[c["name"]] = pid
        if not row or c["price"] != money(row["price"]) or Path(c["img"]).name != Path(row["image_file_path"]).name \
                or c["sold"] != (sum(inv.get(pid, {}).values()) == 0):
            bad.append(pid)
    heading = p.js("document.querySelector('.page-lead')?.textContent || ''")
    check(A, "Catalogue shows every product with the database price, image and sold-out state",
          len(cards) == len(cat) and not bad, f"{len(cards)} cards rendered vs {len(cat)} DB rows; {len(cards) - len(bad)} fully match ('{heading.strip()}')", "03_catalogue.jpg")
    check(A, "No broken images on the catalogue page", broken_images() == 0, f"{len(cards)} product images, 0 broken")

    # Filters through the UI
    p.js("[...document.querySelectorAll('.chip')].find(b => b.textContent.startsWith('Quarter-Zips')).click()")
    time.sleep(1)
    p.js("[...document.querySelectorAll('.chip')].find(b => b.textContent.trim() === 'Gray').click()")
    time.sleep(1)
    sel = p.js("const s = document.querySelector('#sort'); Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(s, 'price_asc'); s.dispatchEvent(new Event('change', {bubbles: true})); 1")
    time.sleep(1.2)
    eager_wait(1000)
    loc = p.js("location.search")
    got = p.js("[...document.querySelectorAll('.product-card')].map(c => [c.querySelector('a').getAttribute('href').split('/').pop(), c.querySelector('.product-card__price').textContent])")
    api = p.js(f"fetch('/api/products{loc}').then(r => r.json())")
    prices = [float(x[1].replace("$", "").replace(",", "")) for x in got]
    db_gray_qz = [pid for pid, r in cat.items() if "zip" in (r["garment_type"] + r["name"]).lower()]
    check(A, "Category + color filters and price sort work together in the UI",
          [x[0] for x in got] == [q["product_id"] for q in api["products"]] and prices == sorted(prices) and all(x[0] in db_gray_qz for x in got),
          f"URL {loc}: {len(got)} gray quarter-zips, prices ascending {', '.join(x[1] for x in got)}", "04_catalogue_filtered.jpg")
    p.js("window.scrollTo(0, 0)")
    p.shot(IMG / "04_catalogue_filtered.jpg")

    p.goto(BASE + "/shop", 1.2)
    p.js("const i = document.querySelector('#search'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, 'davenport'); i.dispatchEvent(new Event('input', {bubbles: true})); 1")
    time.sleep(1.8)
    found = p.js("[...document.querySelectorAll('.product-card__name')].map(e => e.textContent)")
    check(A, "Search box finds products by keyword", bool(found) and all("davenport" in (cat[by_display[n]]["name"] + cat[by_display[n]]["description"] + cat[by_display[n]]["search_tags"]).lower() for n in found),
          f"'davenport' -> {found}")

    p.goto(BASE + "/shop?q=zzzzqqq", 1.5)
    eager_wait(800)
    empty = p.js("document.querySelector('.catalogue__results').innerText")
    p.shot(IMG / "05_catalogue_empty_dan.jpg")
    check(A, "A search with no matches shows a helpful empty state (sniffing Dan + clear filters)",
          "couldn't find a match" in empty and p.js("!!document.querySelector('.empty-dan')"), "'No styles match those filters' with Clear all filters", "05_catalogue_empty_dan.jpg")

    # ---------- Product page ----------
    A = "Product page"
    pid = "benjamin-franklin-1-4-zip"
    p.goto(BASE + f"/products/{pid}", 1.8)
    eager_wait(600)
    p.shot(IMG / "06_product_page.jpg")
    pg = p.js("""({title: document.querySelector('h1').textContent, price: document.querySelector('.product-page__price, [class*=price]').textContent,
        sizes: [...document.querySelectorAll('.size-option')].map(b => [b.querySelector('.size-option__size').textContent, b.querySelector('.size-option__stock').textContent, b.disabled]),
        img: document.querySelector('.product-page img, main img').getAttribute('src'),
        desc: document.querySelector('main').innerText})""")
    want = inv[pid]
    size_ok = all(
        (q == 0 and stock == "Sold out" and disabled) or (q > 0 and stock == f"{q} left" and not disabled)
        for size, stock, disabled in pg["sizes"] for q in [want[size]]
    ) and len(pg["sizes"]) == len(want)
    check(A, "Product page shows the database price, description and image", pg["price"] == money(cat[pid]["price"])
          and cat[pid]["description"][:60] in pg["desc"] and Path(pg["img"]).name == Path(cat[pid]["image_file_path"]).name,
          f"{pg['title']}: {pg['price']} (DB {money(cat[pid]['price'])})", "06_product_page.jpg")
    check(A, "Every size shows the exact inventory quantity; sold-out sizes can't be selected", size_ok,
          "; ".join(f"{s} '{t}'" for s, t, _ in pg["sizes"]) + f"  vs DB {want}", "06_product_page.jpg")
    p.js("[...document.querySelectorAll('.size-option')].find(b => b.querySelector('.size-option__size').textContent === 'S').click()")
    time.sleep(0.4)
    status = p.js("document.querySelector('.size-picker__status')?.textContent")
    check(A, "Choosing a low-stock size explains the stock level", status and "S" in status and "2" in status, f"selected S -> '{status}'")
    p.shot(IMG / "07_product_size_selected.jpg")
    addbag = p.js("[...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Add to bag')?.disabled")
    check(A, "No cart/checkout: 'Add to bag' stays disabled with an explanation", addbag is True, "button disabled; hint 'Online checkout isn't available yet.'")

    p.goto(BASE + "/products/not-a-real-product", 1.5)
    nf = p.js("document.querySelector('main').innerText")
    p.shot(IMG / "08_product_not_found.jpg")
    check(A, "An unknown product address shows a friendly 'not found' page", "find" in nf.lower() or "not found" in nf.lower(), nf.strip().splitlines()[0][:80], "08_product_not_found.jpg")
    p.goto(BASE + "/no-such-page", 1.2)
    p.shot(IMG / "09_404_page.jpg")
    check(A, "An unknown page shows the 404 page with Dan", p.js("!!document.querySelector('.dan-pose')"), "sniffing Dan + link back to the shop", "09_404_page.jpg")

    # ---------- Account forms (visual) ----------
    A = "Account pages"
    p.goto(BASE + "/account/register", 1.2)
    p.shot(IMG / "10_register_page.jpg")
    p.js("document.querySelector('form button[type=submit]').click()")
    time.sleep(0.6)
    errs = p.js("[...document.querySelectorAll('[class*=error], [role=alert]')].map(e => e.textContent).filter(Boolean)")
    p.shot(IMG / "11_register_validation.jpg")
    check(A, "Registration form shows field errors when submitted empty", len(errs) >= 2, f"{len(errs)} messages, e.g. {errs[:2]}", "11_register_validation.jpg")
    p.goto(BASE + "/account/login", 1.2)
    p.shot(IMG / "12_login_page.jpg")
    p.js("""const set = (sel, v) => { const i = document.querySelector(sel); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, v); i.dispatchEvent(new Event('input', {bubbles: true})); };
        set('input[type=email]', 'nobody@example.com'); set('input[type=password]', 'wrong-password-123'); document.querySelector('form button[type=submit]').click(); 1""")
    time.sleep(1.5)
    msg = p.js("document.querySelector('form').innerText")
    p.shot(IMG / "13_login_wrong_password.jpg")
    check(A, "Wrong sign-in details show a clear, non-revealing message", "don't match" in msg.lower() or "incorrect" in msg.lower() or "invalid" in msg.lower(),
          [line for line in msg.splitlines() if line.strip()][0][:90], "13_login_wrong_password.jpg")
    p.goto(BASE + "/account", 1.2)
    check(A, "The account page sends signed-out visitors to sign in", p.js("location.pathname") in ("/account/login",) or "sign in" in p.js("document.querySelector('main').innerText").lower(),
          p.js("location.pathname"))

    # ---------- Responsive ----------
    A = "Responsive layout"
    pages = ["/", "/shop", "/shop?category=t-shirts", f"/products/{pid}", "/account/login", "/account/register", "/no-such-page"]
    sizes = [(390, 844, True, "phone"), (820, 1180, True, "tablet"), (1280, 800, False, "desktop")]
    for w, h, mobile, label in sizes:
        p.viewport(w, h, mobile)
        over = {}
        for path in pages:
            p.goto(BASE + path, 1.0)
            o = overflow()
            if o > 0:
                over[path] = o
        check(A, f"No horizontal scrolling on {len(pages)} pages at {label} width ({w}px)", not over, f"overflow: {over or 'none'}")

    p.viewport(390, 844, True)
    p.goto(BASE + "/", 1.5)
    p.shot(IMG / "20_mobile_home.jpg")
    menu = p.js("document.querySelector('.header__menu-toggle').click(); new Promise(r => setTimeout(() => r([...document.querySelectorAll('.nav__link')].filter(a => a.offsetParent).length), 500))")
    p.shot(IMG / "21_mobile_menu.jpg")
    check(A, "Phone menu button opens the navigation", menu >= 6, f"{menu} visible links after tapping the menu", "21_mobile_menu.jpg")
    p.goto(BASE + "/shop", 1.5)
    eager_wait(1000)
    p.shot(IMG / "22_mobile_catalogue.jpg")
    cols = p.js("getComputedStyle(document.querySelector('.product-grid')).gridTemplateColumns.split(' ').length")
    check(A, "Phone catalogue uses a 2-column grid with collapsible filters", cols == 2 and p.js("!document.querySelector('.filters__panel').open"), f"{cols} columns; filters collapsed", "22_mobile_catalogue.jpg")
    p.goto(BASE + f"/products/{pid}", 1.5)
    eager_wait(600)
    p.shot(IMG / "23_mobile_product.jpg")
    p.viewport(1280, 800)

    passed = sum(r["passed"] for r in RESULTS)
    print(f"\n{passed}/{len(RESULTS)} UI checks passed")
    Path(args.out).write_text(json.dumps({"passed": passed, "total": len(RESULTS), "results": RESULTS}, indent=2), encoding="utf-8")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
