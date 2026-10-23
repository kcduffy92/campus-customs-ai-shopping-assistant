"""Tools the shopping assistant can call. Both are read-only and go through catalogue.py / db.py (parameterized SQL).

- search_products  -> product information from the `catalogue` table (names, descriptions, garment types, colors,
                      prices, tags). Understands shopper wording and the database's inconsistent labels.
- check_inventory  -> stock for one product from the `inventory` table, optionally for one size.

They are registered with the agent through `Agent(tools=TOOLS)` in agent.py. PydanticAI builds each tool's schema
from its type hints and turns the docstring (including the Args section) into the description the model sees.

Problem 9 additions:
- Both tools are hidden for a turn when the customer's message is pure small talk (`_hide_for_small_talk`), so the
  model can't spend a round trip searching after "thanks!".
- Each tool reports what it is actually doing through `ctx.deps.progress` (shown to the shopper while waiting).
- check_inventory can also find its candidates from a description ("hoodies" + size L) in the same step, using the
  same catalogue search, which saves one model round trip for "X in size Y" questions.
- search_products refuses an empty "search everything" call instead of listing the whole catalogue.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic_ai import RunContext, Tool
from pydantic_ai.tools import ToolDefinition

import catalogue
from audit import safe_text, short_error
from models import AgentDeps, InventoryResult, ProductInfo, ProductSearchResult, SizeAvailability

log = logging.getLogger("campus_customs.tools")

MAX_RESULTS = 10


def _report(ctx: RunContext[AgentDeps], stage: str, text: str) -> None:
    """Tell the waiting shopper what the assistant is doing right now (only called when it really happens)."""
    if ctx.deps.progress is not None:
        try:
            ctx.deps.progress({"stage": stage, "text": text})
        except Exception:  # progress is a nicety; never let it break a lookup
            log.debug("progress callback failed", exc_info=True)


def _audit(ctx: RunContext[AgentDeps], tool: str, arguments: dict[str, Any], status: str, started: float,
           result: dict[str, Any] | None = None, error: str | None = None) -> None:
    """Add this tool call to the request's audit record (Problem 12). Never lets auditing break a lookup."""
    record = ctx.deps.audit
    if record is None:
        return
    try:
        record.tool_call(tool, arguments=arguments, status=status, started=started, result=result, error=error)
    except Exception:
        log.debug("audit tool_call failed", exc_info=True)


def _quote(text: str, limit: int = 40) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


async def _hide_for_small_talk(ctx: RunContext[AgentDeps], tool_def: ToolDefinition) -> ToolDefinition | None:
    """Don't offer the database tools when the message is pure small talk (see smalltalk.py)."""
    return None if ctx.deps.small_talk else tool_def


def _info(p) -> ProductInfo:
    return ProductInfo(
        product_id=p.product_id,
        name=p.display_name,
        category=p.category.label,
        garment_type=p.garment_type,
        colors=p.colors,
        price=p.price,
        description=p.description,
        tags=p.search_tags,
        page=f"/products/{p.product_id}",
    )


async def search_products(
    ctx: RunContext[AgentDeps],
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    limit: int = 6,
) -> ProductSearchResult:
    """Look up Campus Customs products in the catalogue: names, descriptions, garment types, colors, prices and tags.

    Use this before stating anything about a product, a price, or which colors or styles exist. It does not return
    stock; use check_inventory for that. Customer wording is fine ('grey quarter zip', 'Davenport crewneck',
    'Yale Law', 'dad hoodie', 'bulldog tee'), including words that differ from the database's labels.

    Args:
        query: Free-text words from the customer: product name, design, school, sport, family member, etc.
            Leave out size words. Can be empty when filtering only by category/color/price.
        category: Optional. One of: hoodies, sweatshirts (crewnecks), quarter-zips, t-shirts, jackets (jackets &
            fleece), long-sleeve. Shopper wording such as 'crewneck', 'tee' or 'quarter zip' also works.
        color: Optional color the customer asked for, e.g. 'navy', 'gray'/'grey', 'white', 'red', 'Yale blue'.
        max_price: Optional maximum price in US dollars.
        min_price: Optional minimum price in US dollars.
        limit: How many products to return (1-10). Use a small number for a specific product, more for browsing.
    """
    limit = max(1, min(int(limit or 6), MAX_RESULTS))
    started = time.perf_counter()
    audit_args = {"query": safe_text(query), "category": category, "color": color, "max_price": max_price,
                  "min_price": min_price, "limit": limit}
    if not (query or "").strip() and not category and not color and max_price is None and min_price is None:
        log.info("tool search_products() with no search terms -> refused")
        _audit(ctx, "search_products", audit_args, "refused_no_search_terms", started)
        return ProductSearchResult(
            query="",
            filters_applied=[],
            exact_match=False,
            total_matches=0,
            products=[],
            note="No search terms given. Only search when the customer asks about products; otherwise just reply.",
        )

    what = _quote(query) or " ".join(x for x in (color, category) if x) or "products"
    _report(ctx, "searching", f"Searching the catalogue for “{what}”…")
    started = time.perf_counter()
    try:
        matches, exact = catalogue.search_products(query, category, color, max_price, min_price)
    except Exception as exc:
        _audit(ctx, "search_products", audit_args, "error", started, error=short_error(exc))
        raise

    filters = []
    if category:
        cat = catalogue.category_from_text(category)
        filters.append(f"category={cat}" if cat else f"category '{category}' not recognized (ignored)")
    if color:
        col = catalogue.color_from_text(color)
        filters.append(f"color={col}" if col else f"color '{color}' not recognized (ignored)")
    if max_price is not None:
        filters.append(f"max_price={max_price}")
    if min_price is not None:
        filters.append(f"min_price={min_price}")

    if not matches:
        note = "No products match. Tell the customer we don't carry that, and offer related categories."
    elif not exact:
        note = "No product matched every word; these are the closest partial matches. Don't present them as exact."
    elif len(matches) > limit:
        note = f"Showing {limit} of {len(matches)} matches. Mention there are more, or ask a narrowing question."
    else:
        note = ""

    result = ProductSearchResult(
        query=query,
        filters_applied=filters,
        exact_match=exact,
        total_matches=len(matches),
        products=[_info(p) for p in matches[:limit]],
        note=note,
    )
    ctx.deps.seen_product_ids.update(p.product_id for p in result.products)
    log.info(
        "tool search_products(query=%r, category=%r, color=%r, max_price=%r, min_price=%r) -> %d matches, exact=%s "
        "in %.0f ms: %s",
        query, category, color, max_price, min_price, len(matches), exact,
        (time.perf_counter() - started) * 1000, [p.product_id for p in result.products],
    )
    _audit(
        ctx, "search_products", audit_args,
        "ok" if matches and exact else "partial_matches" if matches else "no_results", started,
        result={"total_matches": len(matches), "exact_match": exact, "filters_applied": filters,
                "returned_product_ids": [p.product_id for p in result.products]},
    )
    found = f"Found {len(matches)} matching product{'s' if len(matches) != 1 else ''}" if matches else "No matches found"
    _report(ctx, "reviewing", f"{found} for “{what}” · reviewing the results…")
    return result


def inventory_for(product_id: str, size: str | None = None) -> InventoryResult:
    """Stock for one product (and optionally one size) from the inventory table."""
    pid = (product_id or "").strip().lower()
    product = catalogue.get_product(pid) if pid else None

    if product is None:
        # Not a real id: offer close matches so the agent can recover instead of guessing.
        words = pid.replace("-", " ").replace("_", " ")
        close, _ = catalogue.search_products(words) if words else ([], False)
        result = InventoryResult(
            found=False,
            product_id=product_id,
            suggestions=[f"{p.product_id}: {p.display_name}" for p in close[:5]],
            message="No product has this id. Use search_products to find the right product_id; don't guess.",
        )
        return result

    sizes = [SizeAvailability(size=s.size, quantity=s.quantity, status=s.status) for s in product.sizes]
    result = InventoryResult(
        found=True,
        product_id=product.product_id,
        name=product.display_name,
        price=product.price,
        sizes=sizes,
        available_sizes=[s.size for s in sizes if s.quantity > 0],
        sold_out_sizes=[s.size for s in sizes if s.quantity == 0],
        total_in_stock=product.total_stock,
    )

    if size:
        code = catalogue.size_from_text(size)
        match = next((s for s in sizes if s.size == code), None) if code else None
        if match is None:
            result.message = (
                f"'{size}' is not a size we carry. Sizes are {', '.join(catalogue.SIZE_ORDER)}. Ask the customer which one they mean."
            )
        else:
            result.requested_size = match.size
            result.requested_size_quantity = match.quantity
            result.requested_size_status = match.status
            result.message = {
                "sold_out": f"{match.size} is SOLD OUT.",
                "low_stock": f"{match.size} is in stock but low: only {match.quantity} left.",
                "in_stock": f"{match.size} is in stock ({match.quantity} available).",
            }[match.status]
    if not result.available_sizes:
        result.message = (result.message + " This product is sold out in every size.").strip()
    return result


async def check_inventory(
    ctx: RunContext[AgentDeps],
    product_ids: list[str] | None = None,
    size: str | None = None,
    query: str | None = None,
    category: str | None = None,
    color: str | None = None,
) -> list[InventoryResult]:
    """Check current stock from the inventory table, optionally for one size.

    Always use this before saying whether something is in stock, how many are left, or which sizes are available,
    and before recommending products for a particular size. Two ways to say which products:
    - product_ids: exact ids you already have (from search_products, the current page, or earlier product cards).
    - query / category / color: when the customer wants things of a kind IN A SIZE ("hoodies in a large",
      "navy tees in medium") and you don't have ids yet, describe them here and this tool finds the candidates with
      the same catalogue search and returns their stock in one step. No need to call search_products first.
    Never guess an id.

    Args:
        product_ids: Exact product_id values (max 10), e.g. ['basic-hoodie-big-yale']. Leave empty to use query.
        size: Optional size the customer asked about: XS, S, M, L, XL or XXL. Words like 'medium',
            'extra large' or '2XL' also work. Omit to get every size.
        query: Optional description of the products when no ids are given, e.g. 'dad', 'bulldog', 'Davenport'.
        category: Optional, with no ids: hoodies, sweatshirts, quarter-zips, t-shirts, jackets, long-sleeve.
        color: Optional, with no ids: e.g. 'navy', 'gray', 'white'.
    """
    ids = list(dict.fromkeys(product_ids or []))[:MAX_RESULTS]
    started = time.perf_counter()
    by_description = not ids and bool((query or "").strip() or category or color)
    if by_description:
        what = _quote(query or "") or " ".join(x for x in (color, category) if x)
        size_code = catalogue.size_from_text(size) if size else None
        _report(ctx, "inventory", f"Finding {what} and checking stock{f' in size {size_code}' if size_code else ''}…")
        matches, _ = catalogue.search_products(query or "", category, color)
        ids = [p.product_id for p in matches[:MAX_RESULTS]]
    elif ids:
        if len(ids) == 1:
            product = catalogue.get_product(ids[0].strip().lower())
            name = product.display_name if product else "that product"
        else:
            name = f"{len(ids)} products"
        size_code = catalogue.size_from_text(size) if size else None
        _report(ctx, "inventory", f"Checking stock for {name}{f' in size {size_code}' if size_code else ''}…")

    audit_args = {"mode": "by_description" if by_description else "by_id", "product_ids": list(product_ids or [])[:MAX_RESULTS],
                  "size": size, "query": safe_text(query), "category": category, "color": color}
    try:
        results = [inventory_for(pid, size) for pid in ids]
    except Exception as exc:
        _audit(ctx, "check_inventory", audit_args, "error", started, error=short_error(exc))
        raise
    ctx.deps.seen_product_ids.update(r.product_id for r in results if r.found)
    _audit(
        ctx, "check_inventory", audit_args,
        "no_candidates" if not results else "ok" if all(r.found for r in results) else "some_not_found", started,
        result={"inventory_records": [
            {"product_id": r.product_id, "found": True, "requested_size": r.requested_size,
             "quantity": r.requested_size_quantity, "status": r.requested_size_status}
            if r.found and r.requested_size else
            {"product_id": r.product_id, "found": True, "stock_by_size": {s.size: s.quantity for s in r.sizes}}
            if r.found else
            {"product_id": safe_text(r.product_id), "found": False}
            for r in results
        ]},
    )
    log.info(
        "tool check_inventory(product_ids=%r, size=%r, query=%r, category=%r, color=%r) -> %s in %.0f ms",
        product_ids, size, query, category, color,
        [
            (r.product_id, r.message or {s.size: s.quantity for s in r.sizes}) if r.found else (r.product_id, "NOT FOUND")
            for r in results
        ],
        (time.perf_counter() - started) * 1000,
    )
    if results:
        found = [r for r in results if r.found]
        what = found[0].name if len(found) == 1 else f"{len(found)} products"
        size_code = catalogue.size_from_text(size) if size else None
        _report(
            ctx,
            "reviewing",
            f"Checked stock for {what}{f' in size {size_code}' if size_code else ''} · putting your answer together…",
        )
    return results


TOOLS: list[Tool[AgentDeps]] = [
    Tool(search_products, prepare=_hide_for_small_talk),
    Tool(check_inventory, prepare=_hide_for_small_talk),
]
