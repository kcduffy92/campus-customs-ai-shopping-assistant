# Campus Customs — Yale-Inspired Store with an AI Shopping Assistant

Campus Customs is a full-stack course project (AI Foundations, Homework 4). It is an online clothing store for
Yale-inspired apparel: 102 hoodies, crewnecks, quarter-zips, tees and jackets, with live size-by-size stock. Its AI
shopping assistant, **Handsome Dan**, helps customers find products, check prices and sizes, and pick up saved
conversations where they left off.

The assistant answers only from the store's database. It looks products up with tools, and the product cards it
shows are built by the backend from verified database records, never from the model's own text.

> **Course project, not a real store.** There is no checkout or payment: "Add to bag" is intentionally disabled.
> The product database and photos are course materials that are **not included in this repository** (see
> [Local data](#local-data-not-in-this-repository)).

## Features

**Storefront**
- Homepage, full catalogue with category / color / price filters, search, sorting, and product pages showing the
  exact stock for every size (sold-out sizes can't be selected).
- Customer accounts: register, sign in, stay signed in, sign out. Passwords are hashed with PBKDF2-HMAC-SHA256;
  sessions use a signed HttpOnly cookie.
- Responsive layout for desktop, tablet and phone. Respects the reduced-motion accessibility setting.

**AI shopping assistant (Handsome Dan)**
- Natural conversation through a chat window on every page.
- Two database tools: `search_products` (catalogue) and `check_inventory` (stock, optionally for one size).
- Clickable product cards (photo, name, price, stock) built from the database, only for products a tool actually returned.
- Knows which product page you're on ("is *this* in medium?").
- Signed-in customers get separate saved conversations (**New chat** / **Chats**), restored after signing back in.
- Live progress while it works ("Searching the catalogue…", "Checking stock…"). Dan's animations follow those
  real backend events: sniffing while a tool searches, running while results are prepared, and a cookie pop-up
  only when products are found.
- Says plainly what it doesn't know (shipping, returns, discounts). It declines to reveal its instructions or
  credentials, and ignores instructions hidden in customer messages or database text.
- **AI audit trail:** one structured JSON record per request, covering the tools used, the products retrieved, how
  the cards were verified, and whether the request succeeded, was blocked or failed (AI provider vs database vs
  application). It stores no message text or personal data.

## Technology

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + TypeScript, React Router (`frontend/`) |
| Backend | FastAPI + Uvicorn, Python 3.14 (`backend/`) |
| AI agent | PydanticAI (`pydantic-ai-slim[openai]`), model `gpt-5.6-luna` through the **Portkey** gateway |
| Database | SQLite (`campus_customs.db`: `catalogue`, `inventory`, `users`, `chat_messages`) |
| Tests and evidence | Python scripts in `tests/` driving headless Microsoft Edge through the DevTools protocol |

## Repository structure

```text
├── README.md
├── AI_prompts.md            # Required deliverable: every prompt submitted to the AI assistant, by problem (1–13)
├── CLAUDE.md                # Standing workflow rules given to the AI coding assistant
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable names with placeholder values only
├── .gitignore               # Keeps .env, data/, .venv/, node_modules/ and build output out of Git
├── backend/
│   ├── main.py              # FastAPI app: catalogue, accounts and chat endpoints
│   ├── agent.py             # PydanticAI agent, Portkey model connection, verified product cards
│   ├── tools.py             # Agent tools: search_products and check_inventory
│   ├── prompts/prompt.md    # The assistant's system prompt (accuracy, personality and safety rules)
│   ├── models.py            # Pydantic models for the API, accounts, chat and agent
│   ├── catalogue.py         # Catalogue/inventory queries and label normalization
│   ├── chat_history.py      # Saved conversations (and the one-time database migration)
│   ├── audit.py             # AI audit trail
│   ├── auth.py, users.py    # Password hashing, signed sessions, account queries
│   ├── smalltalk.py         # Detects greetings/thanks (no tools needed)
│   └── config.py, db.py     # Settings from .env; SQLite connection helper
├── frontend/
│   ├── package.json, package-lock.json, vite.config.ts, tsconfig.json, index.html
│   ├── public/              # favicon
│   └── src/                 # pages, components (incl. ChatWidget, DanMascot), styles, Handsome Dan artwork
├── tests/                   # Application checks, audit checks and report builders (see "Testing")
└── output/
    ├── design.md            # Database documentation, architecture, visual design (Problems 2, 3, 10)
    ├── harness.md           # Accounts, AI assistant, tools, memory, testing, audit trail and safety (Problems 4–12)
    ├── usability.md         # Usability and performance improvements with measurements (Problem 9)
    ├── app_check.html       # End-to-end testing report with screenshots (Problem 11)
    ├── app_check_images/    # Screenshots used by the report
    └── audit_trail.json     # Real audit records captured during testing (Problem 12)
```

`data/` (database, product photos, live audit log) exists only on the developer's machine and is not in Git.

## Local data (not in this repository)

The SQLite database and product photos were provided with the course and are **not published**. The application
needs them: without the database the API answers "The store is temporarily unavailable" and nothing loads. Without
the photos, product images don't load. Place them like this:

```text
data/
├── campus_customs.db        # the course database
└── products/                # product photos named as in the catalogue's image_file_path column (products/<file>.jpg)
```

The backend reads `data/` next to `backend/` by default. To use another folder (for example a throwaway copy for
testing), set `CAMPUS_DATA_DIR` to its path.

**One-time conversation migration.** Separate saved conversations need one extra column. On its first start with a
database that doesn't have it, the backend:
1. saves a full backup next to the database (`campus_customs.backup-before-conversations-<UTC time>.db`);
2. adds `chat_messages.conversation_id` and an index;
3. puts each customer's existing messages into one earlier conversation;
4. checks that no message was lost, rolling back if the count changed.

Later starts make no changes. Nothing else in the database is modified; accounts and chats are only added through
normal use of the site.

The assistant also writes its audit log to `data/audit/audit_log.jsonl` (created automatically; set
`AUDIT_LOG_PATH` to move it).

## Configuration

Secrets are read from a local `.env` file that is never committed.

1. Copy `.env.example` to `.env` (in the repository root, next to `requirements.txt`).
2. Set `PORTKEY_API_KEY` to your Portkey key. The key stays on the server and is never sent to the browser.
3. Set `SESSION_SECRET` to a long random value, e.g. the output of
   `python -c "import secrets; print(secrets.token_hex(32))"`. It signs login cookies and keys the audit pseudonyms.
4. Optional:
   - `OPENAI_MODEL` (default `gpt-5.6-luna`).
   - `COOKIE_SECURE=true` when served over HTTPS.
   - `TEST_ACCOUNT_EMAIL` / `TEST_ACCOUNT_PASSWORD`: the course's test account, used only by the test scripts.

Without a Portkey key the store still works, but the assistant replies that it is unavailable.

## Setup

Tested on Windows with Python 3.14, Node.js 24 and npm 11.

```powershell
# Backend, from the repository root
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## Running locally

Start the backend first, then the frontend, each in its own terminal.

```powershell
# Terminal 1: FastAPI backend on http://127.0.0.1:8000 (the course's required command, run from backend/)
cd backend
..\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000

# Terminal 2: React dev server on http://localhost:5173
cd frontend
npm run dev
```

Open **http://localhost:5173**. The dev server forwards `/api` and `/media` requests to the backend on port 8000.

| URL | What it is |
|---|---|
| http://localhost:5173/ | Homepage |
| http://localhost:5173/shop | Catalogue (filters in the URL, e.g. `/shop?category=hoodies`) |
| http://localhost:5173/products/basic-hoodie-big-yale | Example product page |
| http://localhost:5173/account/register, `/account/login`, `/account` | Create an account, sign in (the course's test account works), my account |
| http://127.0.0.1:8000/docs | Interactive API documentation |

The **Ask Handsome Dan** button in the bottom-right corner of every page opens the assistant.

`--reload` restarts the backend when files in `backend/` change. Edits to `backend/prompts/prompt.md` take effect on the
next message. Before restarting, make sure nothing still holds the ports. With `--reload`, uvicorn runs a reloader
plus a server process, so stop the whole process tree:

```powershell
netstat -ano | findstr ":8000 :5173"
taskkill /PID <pid> /T /F
```

Other frontend commands (from `frontend/`): `npm run typecheck` and `npm run build` (output in `frontend/dist/`, not committed).

## Testing and evidence

| Evidence | Where |
|---|---|
| End-to-end test report with 56 screenshots: storefront, accounts, 19 live AI conversations checked against the database, Dan's animations, mobile, reduced motion; 222/222 checks | [`output/app_check.html`](output/app_check.html) (download the file and the `output/app_check_images/` folder and open it in a browser; GitHub shows HTML as source) |
| AI audit trail: 19 real records from the Problem 12 tests (greeting, search, stock, nonexistent and sold-out products, invalid and suspicious requests, provider outage and timeout, signed-in customer, restart); 119/119 checks | [`output/audit_trail.json`](output/audit_trail.json) |
| How each part works and how it was tested | [`output/harness.md`](output/harness.md) (sections 1–8), [`output/design.md`](output/design.md), [`output/usability.md`](output/usability.md) |
| Prompt history | [`AI_prompts.md`](AI_prompts.md) |

The scripts in `tests/` reproduce the checks. They need the local data, a running backend and frontend, and (for
browser checks) Microsoft Edge. They refuse to run against the real database: copy `data/` and point
`CAMPUS_DATA_DIR` at the copy.

| Script | Purpose |
|---|---|
| `app_check_api.py` | Catalogue and inventory vs the database, accounts, isolation, invalid input, AI outage (no AI calls) |
| `app_check_ui.py` | Customer-style browser checks and storefront screenshots (no AI calls) |
| `app_check_chat.py`, `app_check_verify.py` | Live chat runs (real AI calls) and their verification against the database |
| `auth_regression.py` | 29 account and session checks (FastAPI TestClient) |
| `audit_check.py`, `audit_verify.py`, `export_audit_evidence.py` | Audit-trail scenarios, verification, and the `audit_trail.json` export |
| `build_app_check_report.py`, `cdp.py`, `crop_shots.py` | Report builder and headless-Edge helpers |

Exact commands are in [`output/harness.md`](output/harness.md), section 7.5.

## Limitations

- **No checkout, payment or orders.** Prices and stock are shown, but nothing can be bought or reserved.
- **Not runnable from this repository alone.** The course database and product photos must be supplied locally,
  and the assistant needs a Portkey API key.
- **Local development only.** It runs with the Vite dev server and Uvicorn; there is no production deployment,
  HTTPS setup or rate limiting on the chat endpoint.
- **AI behaviour is probabilistic.** The code guarantees that cards, prices and stock come from the database and that
  customers' conversations stay separate. The wording of replies depends on the model following its prompt (tested
  extensively, but not guaranteed).
- The audit log is a local file without rotation or tamper protection, and its customer references are pseudonymous
  (keyed hashes), not anonymous.

More detail on risks and limitations: [`output/harness.md`](output/harness.md), section 8.8.
