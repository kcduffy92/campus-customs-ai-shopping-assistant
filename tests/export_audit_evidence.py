"""Problem 12: write output/audit_trail.json from REAL audit records captured during the audit tests.

    python tests/export_audit_evidence.py --data <copy> --runs runs.json --verify audit_verify.json --out output/audit_trail.json

The records are copied unchanged from <copy>/audit/audit_log.jsonl (the audit log the backend wrote while the tests ran
against a temporary database copy). Nothing is invented or edited; each record is linked to the test that produced it.
The ongoing local log of the running app is separate: hw4/data/audit/audit_log.jsonl (git-ignored, never published).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

FIELD_GUIDE = {
    "schema": "Record format version (campus-customs.audit/1).",
    "event": "chat_request (a message to the assistant), chat_request_rejected (invalid request stopped before the assistant), "
             "conversation_access_denied (someone asked for a conversation that isn't theirs).",
    "request_id": "Random id for this request; use it to find the matching console log line.",
    "received_at / finished_at / duration_ms": "UTC timestamps (ISO 8601) and total time in milliseconds.",
    "endpoint": "API path that received the message (/api/chat/stream is what the website uses).",
    "customer.signed_in / customer.customer_ref": "Whether the customer was signed in, and a keyed pseudonym (HMAC-SHA256 with the server's "
                                                  "SESSION_SECRET). Same customer = same ref; it can't be turned back into an account.",
    "conversation": "Pseudonymous conversation reference, whether it was a new conversation, and how many saved messages were used as context.",
    "input": "Message length in characters (never the text), whether it was treated as small talk, and the page type plus the verified product id if on a product page.",
    "model": "Model name, number of model requests, and token counts.",
    "tool_calls[]": "Each tool call in order: tool name, start offset and duration, arguments (search words truncated and masked), "
                    "status (ok, partial_matches, no_results, refused_no_search_terms, some_not_found, no_candidates, error) and what it retrieved: "
                    "product ids for search_products; product, size, quantity and stock status for check_inventory.",
    "recommendations": "Product ids the model selected, the size asked about, the cards actually shown, any dropped ids with the reason, "
                       "and all_verified_against_database (every shown card was built from a catalogue row for an id a tool returned).",
    "outcome": "status (success | blocked | failed), category (who is responsible, see error_categories), HTTP status, reply length, "
               "cards shown, whether it was saved to the customer's history, and a short masked error message.",
}
CATEGORIES = {
    "provider_timeout": "The AI provider didn't answer in time (AI provider problem).",
    "provider_unavailable": "The AI provider couldn't be reached or returned a server error / rate limit (AI provider problem).",
    "provider_rejected": "The AI provider refused the request, e.g. HTTP 401/400 (configuration or provider problem).",
    "provider_content_filter": "The provider's safety filter blocked the message; the customer got a polite redirect (blocked, not an outage).",
    "model_output_error": "The model answered but the answer was unusable (empty, invalid structure or too many steps).",
    "not_configured": "PORTKEY_API_KEY is missing.",
    "database_error": "The SQLite database was missing, locked or failed (database problem).",
    "application_error": "An unexpected error in Campus Customs code (application problem).",
    "validation_error": "The request was invalid (empty, too long or malformed) and never reached the assistant.",
    "conversation_not_owned": "The customer asked for a conversation that isn't theirs (or doesn't exist).",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    for a in ("data", "runs", "verify", "out"):
        ap.add_argument(f"--{a}", required=True)
    args = ap.parse_args()
    records = [json.loads(x) for x in (Path(args.data) / "audit" / "audit_log.jsonl").read_text(encoding="utf-8").splitlines()]
    runs = json.loads(Path(args.runs).read_text(encoding="utf-8"))
    ver = json.loads(Path(args.verify).read_text(encoding="utf-8"))
    tests = []
    for r in runs:
        rec = r["audit_records"][0] if r["audit_records"] else {}
        oc = rec.get("outcome", {})
        tests.append({
            "test": r["name"],
            "purpose": r["purpose"],
            "request_id": rec.get("request_id"),
            "audit_outcome": f"{oc.get('status')}" + (f" ({oc.get('category')})" if oc.get("category") else ""),
            "tools_recorded": [f"{t['tool']}:{t['status']}" for t in rec.get("tool_calls", [])],
            "cards_shown": rec.get("recommendations", {}).get("shown", []),
        })
    doc = {
        "about": {
            "title": "Campus Customs AI audit trail: captured test evidence (Problem 12)",
            "what_this_file_is": "Real audit records written by the Campus Customs backend while the Problem 12 audit tests ran. They were "
                                 "copied unchanged from the audit log; nothing was invented or edited. Each test below links to its record by request_id.",
            "what_this_file_is_not": "Not the ongoing log of the running store. That live log is written to hw4/data/audit/audit_log.jsonl "
                                     "(one JSON record per line), stays on the local machine and is git-ignored.",
            "environment": "Backends ran against a TEMPORARY copy of the database with throwaway example.com test accounts. For the "
                           "'injection_*' tests, one product description in that copy (morse-1-4-zip) was given planted instructions to test "
                           "that the assistant ignores instructions inside database text; the real database was not changed.",
            "provider_failure_simulation": "7a used a second backend whose PORTKEY_BASE_URL pointed at a closed local port (unreachable provider); "
                                           "7b pointed it at a local server that accepts connections and never answers (timeout). No real "
                                           "provider was harmed or flooded.",
            "privacy": "No message text, reply text, names, emails, passwords, cookies, tokens or API keys are stored. Customers and "
                       "conversations appear only as keyed pseudonyms.",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "record_count": len(records),
            "verification": f"{ver['passed']}/{ver['total']} checks passed (tests/audit_verify.py): records match the backend's console "
                            "log, the HTTP responses and the database; privacy scans found no sensitive data.",
        },
        "field_guide": FIELD_GUIDE,
        "error_categories": CATEGORIES,
        "tests": tests,
        "records": records,
    }
    Path(args.out).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out}: {len(tests)} tests, {len(records)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
