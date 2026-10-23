# Usability

## Problem 9: Four improvements to the shopping experience

Two **frontend** improvements and two **backend / AI-agent** improvements, chosen from problems we had observed
(slow answers, a silent typing indicator, pointless product searches, and conversation lists full of "hi").

All measurements used a **temporary copy** of the database. The real database was never written to (it still has
3 users and 22 messages). Timings bypass Portkey's response cache (`PORTKEY_FORCE_REFRESH=1`, measurement only),
because cached repeats made the first measurements look 2–3× faster than a real customer's experience.

---

### Baseline: how the assistant performed before the changes

Benchmark: 7 representative questions, each asked 3 times through the chat API, signed in, each in a new
conversation, model `gpt-5.6-luna` at reasoning effort `low`, cache bypassed. 21/21 requests succeeded.

| Question | Median time | Tool calls, every run |
|---|---|---|
| "hi there!" | 4.66 s | 1 search (unnecessary) |
| "Thanks, that's helpful!" | 4.60 s | 1 search (unnecessary) |
| "How much is the Basic Hoodie Big Yale?" | 7.39 s | search |
| "Show me some navy hoodies" | 3.94 s | search |
| "Which hoodies do you have in a large?" | 7.21 s | search, then check_inventory |
| "Is the Champion Reverse Weave Crewneck available in XXL?" | 5.34 s | search, then check_inventory |
| "Is this available in medium?" (product page) | 4.26 s | check_inventory |

**Where the time goes** (profiled before changing anything):

| Step | Time |
|---|---|
| One model request (even a tiny prompt with no tools) | **2.2 – 3.5 s** |
| `catalogue.search_products` | 7 ms |
| Stock for 10 products | 11 ms |
| Building 6 product cards | ~40 ms |
| Loading a saved conversation | < 1 ms |

**Conclusion:** response time ≈ (number of model requests) × 2–3 s. Database tuning can't help. The only levers are
**fewer model round trips** and **better feedback while waiting**. A typical answer took 2 requests (tool, then
answer). Size questions took 3 (search, then stock, then answer), and greetings took 2 because of a pointless search.

---

## Frontend improvement 1: Accurate progress messages while the assistant works

**The issue.** The only feedback while waiting was three dots and "Typing…". On 5–10 second answers the chat
looked frozen, and customers couldn't tell whether anything was happening.

**What changed.**
- New endpoint **`POST /api/chat/stream`**. It does the same work as `/api/chat` (same validation, identity,
  conversation ownership checks, saving and card verification), but streams newline-delimited JSON:
  `{"type":"status",…}` lines while working, then one `{"type":"result",…}` (or `{"type":"error",…}`).
- **Status messages come only from code that is actually running**, through a `progress` callback in `AgentDeps`:

  | When | Message (examples from testing) |
  |---|---|
  | The agent starts | "Thinking…" |
  | `search_products` starts | "Searching the catalogue for "Yale Law School quarter zip"…" |
  | `check_inventory` starts | "Checking stock for Davenport College Crewneck in size S…" / "Finding navy t-shirts and checking stock in size XL…" |
  | A tool finishes | "Found 1 matching product for "…" · reviewing the results…" / "Checked stock for 10 products in size XL · putting your answer together…" |

- The chat widget shows the message in the typing bubble, and a short version in the header ("Searching
  products…", "Checking stock…", "Writing a reply…"). After 8 seconds it adds "Still working, thanks for waiting
  (Ns)".
- Each message stays readable for **at least 0.7 s**. A stock lookup takes about 10 ms, so without this it flashed
  by unseen. This only paces the status text; **the reply is shown the moment it arrives**.

**Why this approach.** A real streaming response tells the truth about progress. Rotating "fake" messages ("Looking
through hoodies…") would claim work that might not be happening, which you specifically ruled out. Streaming only
the *status* (not the reply text) kept the change small: the verified product cards still arrive in one piece at the
end, exactly as before. The original `/api/chat` endpoint is unchanged and still works.

**What testing showed** (website, desktop and 375 px phone):
- Small talk ("hi there!", "ok great, thank you!") showed **only "Thinking…"**, because no tools ran.
- "Is this available in small?" on the Davenport page: Thinking… → **Checking stock for Davenport College
  Crewneck in size S…** → Checked stock… · putting your answer together… The answer ("S is sold out") matched the
  database (S = 0).
- Price question: Thinking… → **Searching the catalogue for "Yale Law School quarter zip"…** → Found 1 matching
  product… ($72.00 ✔).
- An API check confirmed the `inventory` stage appears **only** when `check_inventory` actually ran (server log).
  A conversation id belonging to another customer is rejected with a 404 **before** any streaming starts. Signed-out
  streaming saves nothing.
- **Fixed during testing:** (1) the stock-check message was invisible because it lasted 10 ms; fixed with the
  0.7 s pacing and the past-tense "Checked stock for …" summary. (2) The status text, and the chat panel itself,
  faded in from fully transparent, which left them invisible or see-through whenever the browser paused animations.
  Both now slide in without ever being transparent. This also explains the "see-through panel" screenshots in
  Problems 7–8, which had been put down to the preview pane.

---

## Frontend improvement 2: Conversations that are easy to recognize and find

**The issue.** Problem 8 titled each conversation with its first message, so many were named "hi there!" or
"Thanks…". The list was one flat column with no dates or topics, and it stopped at 50 conversations, which hid older
chats from frequent shoppers.

**What changed** (no database change; everything is derived from existing messages in `chat_history.list_conversations`):
- **Smarter titles:**
  - The first message that **isn't small talk** becomes the title, using the same detector as improvement 3.
  - If that message says "this", "it" or "that one" and the reply showed a single product, the product is named:
    "**Davenport College Crewneck: Is this available in small?**"
  - With no real question, the title is "Chat about hoodies" (from the products shown) or "Quick chat".
- **Topic tags:** up to 3 product categories shown in the conversation (e.g. "Hoodies", "Crewnecks & Sweatshirts").
- **Preview:** the first line of the latest assistant reply.
- **Date groups:** Today / Yesterday / Previous 7 days / Earlier.
- **Search box** (when there are more than 5 chats): filters by title, topics and preview.
- **Up to 200 conversations** listed (was 50). Listing 102 conversations takes 97 ms.

**Why this approach.** Renaming would also help, but it needs somewhere to store a custom title: another schema
change, which you asked us to avoid this late. Better automatic titles fix the "hi" problem for every conversation,
including existing ones, with no effort from the customer. Topics, previews and dates make chats recognizable at a
glance, and search covers long histories.

**What testing showed** (website):
- On a list of 50 conversations: **0 titles were just a greeting** (8 greeting-only chats became "Quick chat").
  Product-page chats were named after their product.
- Searching "davenport" found the right chat at once.
- With the limit raised, the seeded September 19 chat appeared under **"Earlier"** ("What hoodies do you have?",
  tagged Hoodies · Crewnecks & Sweatshirts, "Sep 19 · 6 messages").
- Switching from that chat to the Davenport chat showed each conversation's own messages. **No mixing.**
- A different customer (Beth) saw only "No saved conversations yet", then only her own chat, on the phone layout.

---

## Backend / agent improvement 3: No product searches for small talk

**The issue.** In the baseline, **"hi there!" and "Thanks, that's helpful!" each triggered a catalogue search in
3 of 3 runs**. That's a whole extra model round trip, about 2–3 s, plus API cost, for nothing. Telling the model "don't
call tools for greetings" in the prompt hadn't worked.

**What changed.**
- `backend/smalltalk.py`: `is_small_talk(message)` recognizes short messages made **only** of greeting, thanks,
  acknowledgement and goodbye words (plus punctuation and emoji). It is deliberately strict:
  - It must contain a real greeting, thanks or goodbye word ("hi", "thanks", "bye"…).
  - Agreement words on their own ("yes", "sure", "ok", "sounds good") are **not** small talk. They often answer
    the assistant's own offer ("Want me to check medium?" → "yes") and need the tools.
  - Any question mark, digit, or other word (product, size, price…) means it is not small talk.
- For small-talk messages only, both tools are hidden for that turn with PydanticAI's per-tool `prepare` hook
  (`Tool(search_products, prepare=_hide_for_small_talk)`). The agent is told to reply warmly without product
  details.
- `search_products` now refuses an empty "search everything" call instead of returning the whole catalogue.

**Why this approach.** A code-level check is predictable and testable; prompt wording had already failed. Keeping
the detector narrow protects accuracy: if it misses some small talk, the cost is only a little time; if it wrongly
caught a product question, the assistant couldn't verify prices or stock. All other messages keep full tool access.

**What testing showed.**
- Detector: 14/15 small-talk phrases recognized ("Have a nice day!" isn't, because it has no greeting or thanks
  word, so it keeps tool access). **26/26 messages that need tools** were correctly *not* treated as small talk,
  including "yes", "sure", "ok", "sounds good", "thanks, what about XL", "hi, do you have hoodies?".
- Benchmark: greeting **4.66 s → 1.95 s (−58%)**, thanks **4.60 s → 1.80 s (−61%)**, with 0 tool calls and
  1 model request in every run (server log: `1 model requests, 0 tool calls, small_talk=True`).
- Website: "hi there!", "thanks, that's helpful!" and "ok great, thank you!" got friendly replies and no cards.
  "thanks!" in the middle of a product conversation stayed in that conversation.
- Product questions still trigger lookups: price → `search_products`; stock → `check_inventory`.

---

## Backend / agent improvement 4: One fewer round trip for size questions, and safer timeouts

**The issue.** "Which hoodies do you have in a large?" needed **3 model requests**: search → stock check →
answer (median 7.2 s, about 15,500 input tokens). The search step only existed to get ids to pass to the stock
check.

**What changed.**
- `check_inventory` can now take a **description instead of ids** (`query` / `category` / `color` plus `size`). It
  finds the candidates with the same `catalogue.search_products` code and returns their real stock **in one step**.
  It is still the inventory tool and still reads the `inventory` table. The two tools stay separate as the
  professor requires, and every card is still verified (`seen_product_ids` + catalogue lookup).
- The prompt's typical flows use it for "X in size Y" and named-product size questions ("Davenport crewneck in a
  medium?"), and the product-page id for "Is this in medium?".
- **Timeouts that actually hold.** During testing, one request hung on a brief network drop and took **113 s**
  even though the run timeout was 45 s, because PydanticAI checks its timeout between steps. Now each request to
  the provider times out after **25 s** (one retry kept), and the whole answer is capped at **50 s**
  (`asyncio.wait_for`), inside the browser's 60 s limit.
- Every reply now logs its duration, model requests, tool calls and the small-talk flag, so speed can be
  monitored.

**What else was tried, and not kept.**
- **Faster reasoning setting.** `minimal` is **not supported** by this model (the provider rejected every request:
  "Supported values are: 'none', 'low', …"). `none` was benchmarked against `low` on the improved code: the medians
  differed by about 0.3 s in both directions (within normal run-to-run noise). Turning reasoning off could make
  tool decisions worse, so we **kept `low`**.
- **Database tuning.** Not worth it: all database work is 1–40 ms per answer, against 2–3 s per model request.
- **Putting stock information inside `search_products`.** Rejected. It would remove a round trip too, but blur the
  required split between the product tool and the inventory tool.

**What testing showed** (same benchmark; final code, cache bypassed, 21/21 succeeded):

| Question | Before: median | After: median | Model requests per answer | Note |
|---|---|---|---|---|
| Greeting | 4.66 s | **1.95 s** | 2 → **1** | improvement 3 |
| Thanks (follow-up) | 4.60 s | **1.80 s** | 2 → **1** | improvement 3 |
| Size recommendations | 7.21 s | **5.21 s** | 3 → **2** | **−28%**, improvement 4 |
| Sold-out size | 5.34 s | **4.26 s** | 3 → **2** | **−20%**, improvement 4 |
| Price | 7.39 s | 3.49 s | 2 → 2 | same steps; the difference is noise (the baseline included a 10.6 s run) |
| Browse | 3.94 s | 3.74 s | 2 → 2 | unchanged, as expected |
| Product-page stock | 4.26 s | 3.25 s | 2 → 2 | same steps; likely noise |

Per round of the 7 questions: **model requests 16 → 12 (−25%)**, **tool calls 9 → 5 (−44%)**.

**Accuracy after the changes** (website answers compared with direct SQL):
- "Hoodies in a large": all 6 cards have L in stock, and the "only 5 left" figure is exact.
- "Navy t-shirts in XL": 5 shown, all with XL in stock ("only 2 left" exact); the 5 left out all have XL = 0.
- Davenport S sold out (S = 0). Davenport M "only 5 left" (M = 5). Morse XL "25 in stock" (XL = 25). Yale Law
  $72.00, all sizes in stock.
- The by-description stock check returned exactly the database's L quantities for all 10 hoodies it considered.

**Honest limits of the speed-up.** Questions that need product information still take about 3–5 s, because one
model request to choose and run the tool and one to write the answer are unavoidable without dropping
verification. Run-to-run variance from the provider is large (the same question ranged 3–12 s). Improvement 1 makes
that wait visible and understandable rather than shorter.

---

## Still worth considering

- **Stream the reply text itself** (not just status). Answers would start appearing after about 2 s, but the
  verified cards and saving would need to be reworked around a partial reply.
- **Rename conversations** (needs a small table or column for custom titles), and delete conversations.
- **Cache catalogue lookups** if the catalogue grows much larger. Not needed at 102 products.
- **Rate limiting** on the chat endpoints, to control API cost.
- The phone chat header is a little tall (the title wraps beside the Chats and New chat buttons). It's usable, but
  icon buttons could tighten it.
