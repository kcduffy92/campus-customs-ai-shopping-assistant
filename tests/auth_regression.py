"""Account and session regression checks (Problems 4 and 8), run in-process with FastAPI TestClient.

Usage (from hw4, venv active): python tests/auth_regression.py <folder holding a COPY of campus_customs.db>
Reads TEST_ACCOUNT_EMAIL / TEST_ACCOUNT_PASSWORD from hw4/.env; creates throwaway example.com accounts in the copy only.
"""
import os, sys, sqlite3, hashlib, re
HW4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["CAMPUS_DATA_DIR"] = sys.argv[1]          # isolated copy of the database
sys.path.insert(0, os.path.join(HW4, "backend"))
from dotenv import load_dotenv; load_dotenv(os.path.join(HW4, ".env"))
from fastapi.testclient import TestClient
import main, auth
TE, TP = os.environ["TEST_ACCOUNT_EMAIL"], os.environ["TEST_ACCOUNT_PASSWORD"]
results = []
def check(name, cond, extra=""):
    results.append(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))
db = os.path.join(sys.argv[1], "campus_customs.db")
before = sqlite3.connect(db).execute("select * from users order by id").fetchall()

c = TestClient(main.app)
check("not signed in initially -> /me null", c.get("/api/auth/me").json() is None)
r = c.post("/api/auth/login", json={"email": TE, "password": TP})
check("SEEDED TEST ACCOUNT logs in", r.status_code == 200, f"{r.status_code} user_id={r.json().get('id')}")
check("response has no password hash", "password" not in r.text)
ck = r.headers.get("set-cookie", "")
check("session cookie HttpOnly + SameSite=lax", "httponly" in ck.lower() and "samesite=lax" in ck.lower())
check("/me returns test account while signed in", c.get("/api/auth/me").json().get("email") == TE.lower())
check("logout -> 204", c.post("/api/auth/logout").status_code == 204)
check("after logout /me null", c.get("/api/auth/me").json() is None)
r = c.post("/api/auth/login", json={"email": "  " + TE.upper() + " ", "password": TP})
check("login is case/space-insensitive for email", r.status_code == 200)
c.post("/api/auth/logout")
r = c.post("/api/auth/login", json={"email": TE, "password": TP + "x"})
check("wrong password -> 401 friendly", r.status_code == 401 and "don't match" in r.json()["detail"], r.json()["detail"])
r2 = c.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever123"})
check("unknown email -> same 401 message", r2.status_code == 401 and r2.json()["detail"] == r.json()["detail"])
r = c.post("/api/auth/login", json={"email": "", "password": ""})
check("empty login -> 422 per-field", r.status_code == 422 and set(r.json()["fields"]) == {"email", "password"}, str(r.json()))

new = {"first_name": "  Test ", "last_name": "Shopper", "email": "New.Shopper@Example.com", "password": "Bulldog-2026!", "confirm_password": "Bulldog-2026!"}
c2 = TestClient(main.app)
r = c2.post("/api/auth/register", json=new)
check("NEW ACCOUNT registers -> 201", r.status_code == 201, f"{r.status_code} {r.json()}")
uid = r.json()["id"]
check("registration signs the user in", c2.get("/api/auth/me").json().get("id") == uid)
row = sqlite3.connect(db).execute("select name,email,password_hash,first_name,last_name,created_at from users where id=?", (uid,)).fetchone()
check("stored: names trimmed, email lowercased, full name", row[0] == "Test Shopper" and row[1] == "new.shopper@example.com" and row[3:5] == ("Test", "Shopper"), str(row[:2]+row[3:5]))
check("password NOT stored in plain text", new["password"] not in row[2])
m = re.fullmatch(r"pbkdf2_sha256\$([0-9a-f]{32})\$([0-9a-f]{64})", row[2])
check("hash format pbkdf2_sha256$salt$hash", bool(m))
check("hash = PBKDF2-SHA256, 120k iterations, stored salt", m and hashlib.pbkdf2_hmac("sha256", new["password"].encode(), m.group(1).encode(), 120_000).hex() == m.group(2))
c2.post("/api/auth/logout")
r = c2.post("/api/auth/login", json={"email": "new.shopper@example.com", "password": new["password"]})
check("NEW ACCOUNT logs back in after logout", r.status_code == 200 and r.json()["id"] == uid)
r = c2.post("/api/auth/login", json={"email": "new.shopper@example.com", "password": "Bulldog-2026"})
check("new account wrong password -> 401", r.status_code == 401)
r = c2.post("/api/auth/register", json={**new, "email": "NEW.SHOPPER@example.com"})
check("duplicate email (different case) -> 409 friendly", r.status_code == 409 and "already exists" in r.json()["detail"], r.json()["detail"])
r = c2.post("/api/auth/register", json={**new, "email": TE})
check("registering seeded email -> 409", r.status_code == 409)
r = c2.post("/api/auth/register", json={**new, "email": "x@y.com", "confirm_password": "different1"})
check("password mismatch -> 422 confirm_password", r.status_code == 422 and "confirm_password" in r.json()["fields"])
r = c2.post("/api/auth/register", json={"first_name": " ", "last_name": "", "email": "bad-email", "password": "short", "confirm_password": "short"})
check("missing/invalid fields -> 422 friendly per-field", r.status_code == 422 and set(r.json()["fields"]) >= {"first_name","last_name","email","password"}, str(r.json()["fields"]))
r = c2.post("/api/auth/register", json={**new, "email": "space@example.com", "password": " pad me 123 ", "confirm_password": " pad me 123 "})
c2.post("/api/auth/logout")
r = c2.post("/api/auth/login", json={"email": "space@example.com", "password": " pad me 123 "})
check("passwords kept exactly as typed (spaces preserved)", r.status_code == 200)
r = c2.post("/api/auth/register", data="not json", headers={"content-type": "application/json"})
check("malformed body -> 422 friendly, no field noise", r.status_code == 422 and r.json()["fields"] == {} and "Traceback" not in r.text, r.json()["detail"])

c3 = TestClient(main.app)
c3.cookies.set(auth.SESSION_COOKIE, auth.create_session_token(1)[:-1] + "0")
check("tampered cookie rejected", c3.get("/api/auth/me").json() is None)
c3.cookies.set(auth.SESSION_COOKIE, "2.9999999999.deadbeef")
check("forged cookie for another user rejected", c3.get("/api/auth/me").json() is None)
check("product API still works", c3.get("/api/products").json()["total"] == 102)

after = sqlite3.connect(db).execute("select * from users where id <= 3 order by id").fetchall()
check("original 3 users unchanged", before == after)
print(f"\n{sum(results)}/{len(results)} checks passed")
