"""Problem 11: end-to-end API checks for Campus Customs (no AI calls).

Compares what the running website serves with the SQLite database itself, and checks accounts, session and
conversation isolation, input validation and error handling.

Run it against a backend that uses a TEMPORARY COPY of the data folder, because it creates test accounts:

    # terminal 1 (from hw4/backend, venv active)
    CAMPUS_DATA_DIR=<copy of hw4/data> uvicorn main:app --port 8000
    # terminal 2 (from hw4)
    python tests/app_check_api.py --base http://127.0.0.1:5173 --db <copy>/campus_customs.db --out results.json

The professor's test account is read from TEST_ACCOUNT_EMAIL / TEST_ACCOUNT_PASSWORD in hw4/.env. Credentials are
never printed or written to the results file.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path

import httpx

HW4 = Path(__file__).resolve().parents[1]
RESULTS: list[dict] = []


def load_env() -> None:
    env = HW4 / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def check(area: str, name: str, ok: bool, evidence: str) -> bool:
    RESULTS.append({"id": f"API-{len(RESULTS) + 1:02d}", "area": area, "test": name, "passed": bool(ok), "evidence": evidence})
    print(f"{'PASS' if ok else 'FAIL'}  [{area}] {name}  ->  {evidence}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:5173")
    ap.add_argument("--db", required=True, help="Path to the database COPY the backend is using")
    ap.add_argument("--out", required=True)
    ap.add_argument("--offline-base", help="Optional second backend whose AI provider is unreachable")
    args = ap.parse_args()
    load_env()

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    real_db = HW4 / "data" / "campus_customs.db"
    if Path(args.db).resolve() == real_db.resolve():
        sys.exit("Refusing to run against the real database; use a copy.")
    users_before = db.execute("select count(*) from users").fetchone()[0]

    anon = httpx.Client(base_url=args.base, timeout=30)

    # ---------- Catalogue ----------
    A = "Catalogue"
    r = anon.get("/api/health")
    check(A, "Health endpoint responds", r.status_code == 200, f"GET /api/health -> {r.status_code}")

    cat = {row["product_id"]: row for row in db.execute("select * from catalogue")}
    inv: dict[str, dict[str, int]] = {}
    for row in db.execute("select product_id, size, quantity from inventory"):
        inv.setdefault(row["product_id"], {})[row["size"]] = row["quantity"]

    lst = anon.get("/api/products").json()
    api_ids = [p["product_id"] for p in lst["products"]]
    check(A, "Product list contains every catalogue row exactly once",
          lst["total"] == len(cat) and sorted(api_ids) == sorted(cat),
          f"API total {lst['total']}, DB catalogue rows {len(cat)}, duplicates {len(api_ids) - len(set(api_ids))}")

    price_bad, name_bad, desc_bad, stock_bad, status_bad = [], [], [], [], []
    for pid, row in cat.items():
        d = anon.get(f"/api/products/{pid}").json()
        if abs(d["price"] - row["price"]) > 1e-9:
            price_bad.append(pid)
        if d["name"] != row["name"]:
            name_bad.append(pid)
        if d["description"] != row["description"]:
            desc_bad.append(pid)
        api_sizes = {s["size"]: s["quantity"] for s in d["sizes"]}
        if api_sizes != inv.get(pid, {}) or d["total_stock"] != sum(inv.get(pid, {}).values()):
            stock_bad.append(pid)
        for s in d["sizes"]:
            want = "sold_out" if s["quantity"] == 0 else "low_stock" if s["quantity"] <= 5 else "in_stock"
            if s["status"] != want:
                status_bad.append(f"{pid}/{s['size']}")
    n = len(cat)
    check(A, "Every product page price equals catalogue.price", not price_bad, f"{n - len(price_bad)}/{n} match; mismatches: {price_bad[:3]}")
    check(A, "Every product name and description equals the database", not name_bad and not desc_bad,
          f"names {n - len(name_bad)}/{n}, descriptions {n - len(desc_bad)}/{n}")
    inv_rows = sum(len(v) for v in inv.values())
    check(A, "Every size quantity and total stock equals the inventory table", not stock_bad,
          f"{inv_rows} inventory rows compared across {n} products; mismatches: {stock_bad[:3]}")
    check(A, "Stock labels follow the rule (0 sold out, 1-5 low, 6+ in stock)", not status_bad, f"{inv_rows - len(status_bad)}/{inv_rows} labels correct")

    img_bad = []
    sample = list(cat)
    for pid in sample:
        url = anon.get(f"/api/products/{pid}").json()["image_url"]
        ir = anon.get(url)
        expected_file = Path(cat[pid]["image_file_path"]).name
        if ir.status_code != 200 or not ir.headers.get("content-type", "").startswith("image/") or Path(url).name != expected_file:
            img_bad.append(pid)
    check(A, "Every product image loads and is the file named in image_file_path", not img_bad,
          f"{len(sample) - len(img_bad)}/{len(sample)} images served (HTTP 200, image/*); failures: {img_bad[:3]}")

    filters = anon.get("/api/filters").json()
    cat_ok = True
    detail = []
    for c in filters["categories"]:
        got = anon.get("/api/products", params={"category": c["slug"]}).json()
        same = all(p["category"]["slug"] == c["slug"] for p in got["products"]) and got["total"] == c["count"]
        cat_ok &= same
        detail.append(f"{c['slug']}={got['total']}")
    check(A, "Category filters return only that category, with the advertised count",
          cat_ok and sum(c["count"] for c in filters["categories"]) == n, ", ".join(detail))

    col_ok = all(
        all(c["slug"] in p["color_families"] for p in anon.get("/api/products", params={"color": c["slug"]}).json()["products"])
        for c in filters["colors"]
    )
    check(A, "Color filters return only products in that color family", col_ok, f"{len(filters['colors'])} color filters checked")

    asc = [p["price"] for p in anon.get("/api/products", params={"sort": "price_asc"}).json()["products"]]
    desc = [p["price"] for p in anon.get("/api/products", params={"sort": "price_desc"}).json()["products"]]
    check(A, "Price sorting is ordered and the price range matches the database",
          asc == sorted(asc) and desc == sorted(desc, reverse=True)
          and filters["price_min"] == min(r["price"] for r in cat.values()) and filters["price_max"] == max(r["price"] for r in cat.values()),
          f"min ${filters['price_min']:.2f}, max ${filters['price_max']:.2f}")

    instock = anon.get("/api/products", params={"in_stock": "true"}).json()
    db_instock = sum(1 for pid in cat if sum(inv.get(pid, {}).values()) > 0)
    check(A, "'In stock only' matches products with stock in the inventory table",
          instock["total"] == db_instock and all(p["total_stock"] > 0 for p in instock["products"]), f"API {instock['total']}, DB {db_instock}")

    srch = anon.get("/api/products", params={"q": "davenport"}).json()
    db_dav = [pid for pid, r in cat.items() if "davenport" in (r["name"] + r["description"] + r["search_tags"]).lower()]
    check(A, "Text search finds the matching products", srch["total"] >= 1 and set(db_dav) <= {p["product_id"] for p in srch["products"]},
          f"q=davenport -> {srch['total']} results; DB rows mentioning it: {len(db_dav)}")

    # ---------- Invalid input / unavailable products ----------
    A = "Invalid input"
    r = anon.get("/api/products/no-such-product-123")
    check(A, "Unknown product returns 404 with a friendly message", r.status_code == 404 and "not found" in r.text.lower(), f"{r.status_code} {r.json().get('detail')}")
    r = anon.get("/api/products", params={"category": "spaceships"})
    check(A, "Unknown category is rejected cleanly (422, not a crash)", r.status_code == 422, f"{r.status_code} {r.json().get('detail')}")
    r = anon.get("/api/products", params={"sort": "random"})
    check(A, "Invalid sort option is rejected cleanly", r.status_code == 422, f"{r.status_code}")
    r = anon.get("/api/products", params={"q": "x" * 500})
    check(A, "Over-long search text is rejected cleanly", r.status_code == 422, f"{r.status_code}")
    r = anon.get("/api/products", params={"q": "' OR 1=1 --"})
    check(A, "SQL-like search text is treated as plain text", r.status_code == 200 and r.json()["total"] < n, f"{r.status_code}, {r.json().get('total')} results")
    sold_out = [pid for pid in cat if sum(inv.get(pid, {}).values()) == 0]
    if sold_out:
        d = anon.get(f"/api/products/{sold_out[0]}").json()
        check(A, "A fully sold-out product is shown as sold out in every size",
              d["in_stock"] is False and all(s["status"] == "sold_out" for s in d["sizes"]), f"{sold_out[0]}: total_stock {d['total_stock']}")
    else:
        print("NOTE  no product is sold out in every size in this database; size-level sold-out labels are checked above")
    r = anon.post("/api/chat", json={"message": "   "})
    check(A, "Empty chat message is rejected before reaching the AI", r.status_code == 422, f"{r.status_code}")
    r = anon.post("/api/chat", json={"message": "a" * 1001})
    check(A, "Chat message over 1000 characters is rejected before reaching the AI", r.status_code == 422, f"{r.status_code}")
    r = anon.post("/api/chat", content=b"{not json", headers={"Content-Type": "application/json"})
    check(A, "Malformed JSON gets a friendly error", r.status_code == 422 and "detail" in r.json(), f"{r.status_code} {r.json().get('detail')}")

    # ---------- Accounts ----------
    A = "Accounts"
    prof = httpx.Client(base_url=args.base, timeout=30)
    te, tp = os.environ.get("TEST_ACCOUNT_EMAIL"), os.environ.get("TEST_ACCOUNT_PASSWORD")
    if te and tp:
        r = prof.post("/api/auth/login", json={"email": te, "password": tp})
        me = prof.get("/api/auth/me").json() if r.status_code == 200 else None
        check(A, "Professor's existing test account can sign in", r.status_code == 200 and me and me["email"].lower() == te.lower(),
              f"login {r.status_code}; /me returns the same account (email withheld)")
        check(A, "Account responses never include a password or hash",
              "password" not in r.text.lower() and "pbkdf2" not in r.text, "keys: " + ", ".join(sorted(r.json())))
    else:
        check(A, "Professor's existing test account can sign in", False, "TEST_ACCOUNT_EMAIL/PASSWORD not set")

    tag = uuid.uuid4().hex[:6]
    pw_a, pw_b = f"Check-{uuid.uuid4().hex[:10]}", f"Check-{uuid.uuid4().hex[:10]}"
    ua = httpx.Client(base_url=args.base, timeout=30)
    ub = httpx.Client(base_url=args.base, timeout=30)
    ra = ua.post("/api/auth/register", json={"first_name": "Avery", "last_name": "Tester", "email": f"avery.{tag}@example.com", "password": pw_a, "confirm_password": pw_a})
    rb = ub.post("/api/auth/register", json={"first_name": "Blake", "last_name": "Tester", "email": f"blake.{tag}@example.com", "password": pw_b, "confirm_password": pw_b})
    check(A, "New customers can register and are signed in immediately",
          ra.status_code == 201 and rb.status_code == 201 and ua.get("/api/auth/me").json()["first_name"] == "Avery",
          f"register -> {ra.status_code}, {rb.status_code}; HttpOnly session cookie set: {'httponly' in ra.headers.get('set-cookie', '').lower()}")
    row = db.execute("select password_hash from users where email=?", (f"avery.{tag}@example.com",)).fetchone() if "password_hash" in [c[1] for c in db.execute("pragma table_info(users)")] else None
    check(A, "Passwords are stored hashed (PBKDF2), never as plain text",
          row is not None and row[0].startswith("pbkdf2_sha256$") and pw_a not in row[0], "stored value starts with pbkdf2_sha256$ (value withheld)")
    r = anon.post("/api/auth/register", json={"first_name": "Dup", "last_name": "Tester", "email": f"AVERY.{tag}@example.com", "password": pw_a, "confirm_password": pw_a})
    check(A, "Duplicate email (different capitalisation) is refused", r.status_code in (409, 422), f"{r.status_code} {r.json().get('detail')}")
    r = anon.post("/api/auth/register", json={"first_name": "S", "last_name": "T", "email": f"short.{tag}@example.com", "password": "abc", "confirm_password": "abc"})
    check(A, "Too-short password is refused with a field message", r.status_code == 422 and "password" in json.dumps(r.json()).lower(), f"{r.status_code}")
    r = anon.post("/api/auth/register", json={"first_name": "S", "last_name": "T", "email": "not-an-email", "password": pw_a, "confirm_password": pw_a})
    check(A, "Invalid email is refused", r.status_code == 422, f"{r.status_code}")
    r = anon.post("/api/auth/register", json={"first_name": "S", "last_name": "T", "email": f"mm.{tag}@example.com", "password": pw_a, "confirm_password": pw_a + "x"})
    check(A, "Mismatched password confirmation is refused", r.status_code == 422, f"{r.status_code}")

    c3 = httpx.Client(base_url=args.base, timeout=30)
    bad = c3.post("/api/auth/login", json={"email": f"avery.{tag}@example.com", "password": "wrong-password"})
    nouser = c3.post("/api/auth/login", json={"email": f"nobody.{tag}@example.com", "password": "wrong-password"})
    check(A, "Wrong password is refused, with the same message as an unknown email",
          bad.status_code == 401 and nouser.status_code == 401 and bad.json()["detail"] == nouser.json()["detail"], f"{bad.status_code}: {bad.json()['detail']}")
    ok = c3.post("/api/auth/login", json={"email": f"  Avery.{tag}@EXAMPLE.com ", "password": pw_a})
    check(A, "Login works with the right password (email case/spaces ignored)", ok.status_code == 200, f"{ok.status_code}")
    stay = [c3.get("/api/auth/me").json()["first_name"] for _ in range(3)]
    check(A, "Customer stays signed in across requests", stay == ["Avery"] * 3, f"/me x3 -> {stay}")
    out = c3.post("/api/auth/logout")
    check(A, "Logout ends the session", out.status_code == 204 and c3.get("/api/auth/me").json() is None, f"logout {out.status_code}; /me afterwards -> null")

    # ---------- Isolation ----------
    A = "Isolation"
    victim = db.execute("select user_id, conversation_id from chat_messages where conversation_id is not null order by id limit 1").fetchone()
    if victim:
        r = ub.get("/api/chat/history", params={"conversation_id": victim["conversation_id"]})
        check(A, "Another customer's conversation can't be read by id", r.status_code == 404 and "messages" not in r.json(),
              f"Blake requests conversation {victim['conversation_id']} (owned by user {victim['user_id']}) -> {r.status_code}")
        r = ub.post("/api/chat", json={"message": "continue please", "conversation_id": victim["conversation_id"]})
        check(A, "Another customer's conversation can't be continued (refused before any AI call)", r.status_code == 404, f"{r.status_code} {r.json().get('detail')}")
        r = ub.get("/api/chat/conversations").json()
        check(A, "A new customer's conversation list is empty (no one else's chats)", r["conversations"] == [], f"{len(r['conversations'])} conversations")
        r = ub.get("/api/chat/history").json()
        check(A, "A new customer's default history is empty", r["messages"] == [] and r["conversation_id"] is None, "0 messages")
        if te and tp:
            mine = prof.get("/api/chat/conversations").json()["conversations"]
            owned = {r[0] for r in db.execute("select distinct conversation_id from chat_messages where user_id=(select id from users where lower(email)=lower(?))", (te,))}
            check(A, "The professor account lists exactly its own conversations", {c["id"] for c in mine} == owned,
                  f"{len(mine)} listed, {len(owned)} owned in DB")
    r = anon.get("/api/chat/history")
    check(A, "Signed-out visitors can't read saved history", r.status_code == 401, f"{r.status_code}")
    r = anon.get("/api/chat/conversations")
    check(A, "Signed-out visitors can't list conversations", r.status_code == 401, f"{r.status_code}")
    cookie = ua.cookies.get("cc_session")
    forged = cookie[:-4] + ("AAAA" if not cookie.endswith("AAAA") else "BBBB")
    r = httpx.get(args.base + "/api/auth/me", cookies={"cc_session": forged})
    check(A, "A tampered session cookie is rejected", r.json() is None, "/me with altered signature -> null")
    r = httpx.get(args.base + "/api/auth/me", cookies={"cc_session": "1.9999999999.deadbeef"})
    check(A, "A made-up session cookie for user 1 is rejected", r.json() is None, "/me -> null")
    r = ua.get("/api/chat/history", params={"conversation_id": victim["conversation_id"], "user_id": victim["user_id"]}) if victim else None
    if r is not None:
        check(A, "Adding a user_id parameter doesn't bypass the check", r.status_code == 404, f"{r.status_code}")

    # ---------- Secrets ----------
    A = "Security"
    html = anon.get("/").text
    leaked = [k for k in ("PORTKEY_API_KEY", "SESSION_SECRET", "TEST_ACCOUNT_PASSWORD") if os.environ.get(k) and os.environ[k] in html]
    check(A, "The page sent to the browser contains no secrets", not leaked, "checked index.html for the Portkey key, session secret and test password")

    # ---------- AI provider unavailable ----------
    if args.offline_base:
        A = "Reliability"
        off = httpx.Client(base_url=args.offline_base, timeout=90)
        t0 = time.time()
        r = off.post("/api/chat", json={"message": "Do you have navy hoodies?"})
        secs = time.time() - t0
        check(A, "If the AI provider is unreachable, chat returns a friendly 503 (no crash, no details leaked)",
              r.status_code == 503 and "unavailable" in r.json()["detail"].lower() and "portkey" not in r.text.lower(),
              f"{r.status_code} in {secs:.1f}s: {r.json().get('detail')}")
        r = off.get("/api/products", params={"category": "hoodies"})
        check(A, "The storefront keeps working while the AI provider is down", r.status_code == 200 and r.json()["total"] > 0, f"{r.status_code}, {r.json()['total']} hoodies")

    users_after = db.execute("select count(*) from users").fetchone()[0]
    print(f"\nTest accounts created in the COPY: {users_after - users_before}")
    passed = sum(r["passed"] for r in RESULTS)
    print(f"{passed}/{len(RESULTS)} API checks passed")
    Path(args.out).write_text(json.dumps({"passed": passed, "total": len(RESULTS), "results": RESULTS}, indent=2), encoding="utf-8")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
