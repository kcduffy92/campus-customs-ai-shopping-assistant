# Homework 4 — Campus Customs: Standing Workflow Instructions

These rules apply to all work in `hw4/`. They add to the workspace-level `../CLAUDE.md`
(default model `gpt-5.6-luna` via `OPENAI_MODEL`, Portkey key handling, secrets rules, black-and-pink styling,
`pydantic-ai-slim[openai]`, venv hygiene). Those general rules are not repeated here.

## Working one problem at a time

- Work on only one problem at a time, and only when the student explicitly says to proceed.
- Do not anticipate or implement future problems unless the student asks for them.
- Keep the existing project structure (see `README.md`) and build on completed work.
- Before overwriting or replacing any existing file, asset, or working code, read its current contents first.

## Maintaining `AI_prompts.md` (required deliverable)

- Record every prompt the student submits as it happens, before or while doing the work. Never reconstruct it at the end.
- Each problem gets its own section: problem number and title, the initial prompt, follow-up prompts, and
  a brief note on what was missing or needed improvement after the initial attempt (when applicable).
- Copy prompts verbatim inside `text` code blocks. Do not paraphrase, polish, summarize, or invent prompts or interactions.
- Follow-up prompts go under the current problem's "Follow-up prompts", in the order they were submitted.
- The "what was missing" note should be short, factual, and based on what actually happened.

## Documentation

- As features are implemented, update the relevant docs: `README.md` (setup/run), `output/*.md`, and `output/audit_trail.json`.
- Explain major implementation decisions and technical issues to the student in plain English.

## Protecting sensitive files (public GitHub repo)

- `data/` (SQLite database, product images), `.env`, `.venv/`, `node_modules/`, and build output are git-ignored. Keep them that way.
- Product images copied for serving (e.g. `frontend/public/products/`) must also stay ignored.
- `.env.example` contains placeholder values only.
- Before any commit, check `git status` to make sure no secrets, database, or product images are staged.
- Do not create or publish the GitHub repository until the student asks.

## Testing completed features

- Test each feature when possible (imports, API calls, endpoints, browser checks) and report exactly what was verified.
- If something cannot be tested, say so clearly. Do not assume it works.
- Backend: use `hw4/.venv`. Frontend: use local packages in `frontend/node_modules`.
- Stop any dev servers you started, and check for orphaned processes on their ports before restarting.
