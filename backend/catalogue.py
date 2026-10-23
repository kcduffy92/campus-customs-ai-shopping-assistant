"""Catalogue and inventory queries plus label normalization. The database is only read here, never changed.

The raw data has 22 garment_type spellings and 22 color names (output/design.md, section 1.7). Rather than edit the
database, each product gets a derived `category` and `color_families`; the original values are returned unchanged
alongside them. These functions are reused by the API now and by the agent tools in later problems.
"""

from __future__ import annotations

import json
import re
import sqlite3

from config import MEDIA_URL
from db import connect
from models import CatalogueFilters, Category, ColorInfo, FilterOption, ProductDetail, ProductSummary, SizeStock

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK_MAX = 5  # 1-5 units left counts as "low stock"

# (slug, label, keywords). The first matching rule wins, so more specific rules come first.
CATEGORY_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("quarter-zips", "Quarter-Zips", ("quarter-zip", "1/4 zip")),
    ("hoodies", "Hoodies", ("hoodie", "hooded")),
    ("jackets", "Jackets & Fleece", ("jacket", "fleece")),
    ("sweatshirts", "Crewnecks & Sweatshirts", ("crewneck", "mockneck", "sweatshirt")),
    ("long-sleeve", "Long Sleeve", ("long-sleeve", "long sleeve")),
    ("t-shirts", "T-Shirts", ("t-shirt", "tee")),
]
OTHER_CATEGORY = ("other", "Other")

# (slug, label, keywords) checked in order against each lower-cased color name.
COLOR_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("navy", "Navy", ("navy",)),
    ("gray", "Gray", ("gray", "grey", "charcoal")),
    ("blue", "Blue", ("blue",)),
    ("white", "White & Cream", ("white", "cream", "ivory")),
    ("black", "Black", ("black",)),
    ("red", "Red & Coral", ("red", "coral")),
    ("yellow", "Yellow & Gold", ("yellow", "gold")),
    ("green", "Green", ("green",)),
    ("multicolor", "Multicolor", ("multi",)),
]
CATEGORY_SLUGS = {slug for slug, _, _ in CATEGORY_RULES} | {OTHER_CATEGORY[0]}
COLOR_SLUGS = {slug for slug, _, _ in COLOR_RULES} | {"other"}
COLOR_LABELS = {slug: label for slug, label, _ in COLOR_RULES} | {"other": "Other"}

_CATALOGUE_COLUMNS = "product_id, name, garment_type, description, colors, search_tags, image_file_path, price"


def categorize(garment_type: str) -> Category:
    text = garment_type.lower()
    for slug, label, keywords in CATEGORY_RULES:
        if any(k in text for k in keywords):
            return Category(slug=slug, label=label)
    return Category(slug=OTHER_CATEGORY[0], label=OTHER_CATEGORY[1])


def color_family(color: str) -> str:
    text = color.lower()
    for slug, _, keywords in COLOR_RULES:
        if any(k in text for k in keywords):
            return slug
    return "other"


def display_name(name: str) -> str:
    """Tidy names that were generated from URL slugs; product data itself is unchanged."""
    name = re.sub(r"\b1 4 Zip\b", "1/4 Zip", name)
    name = re.sub(r"\bT Shirt\b", "T-Shirt", name)
    return re.sub(r"\bVs\b", "vs.", name)


def stock_status(quantity: int) -> str:
    if quantity <= 0:
        return "sold_out"
    return "low_stock" if quantity <= LOW_STOCK_MAX else "in_stock"


def image_url(image_file_path: str) -> str:
    # Stored as "products/<file>.jpg" relative to data/; served at /media/products/<file>.jpg.
    return f"{MEDIA_URL}/{image_file_path.lstrip('/')}"


def _json_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(v) for v in value] if isinstance(value, list) else []


def _sizes_by_product(conn: sqlite3.Connection, product_ids: list[str] | None = None) -> dict[str, list[SizeStock]]:
    if product_ids is None:
        rows = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    else:
        placeholders = ",".join("?" * len(product_ids))
        rows = conn.execute(
            f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({placeholders})", product_ids
        ).fetchall()
    sizes: dict[str, list[SizeStock]] = {}
    for r in rows:
        sizes.setdefault(r["product_id"], []).append(
            SizeStock(size=r["size"], quantity=r["quantity"], status=stock_status(r["quantity"]))
        )
    rank = {s: i for i, s in enumerate(SIZE_ORDER)}
    for lst in sizes.values():
        lst.sort(key=lambda s: rank.get(s.size, len(SIZE_ORDER)))
    return sizes


def _summary_fields(row: sqlite3.Row, sizes: list[SizeStock]) -> dict:
    colors = _json_list(row["colors"])
    families = list(dict.fromkeys(color_family(c) for c in colors))
    total = sum(s.quantity for s in sizes)
    return dict(
        product_id=row["product_id"],
        name=row["name"],
        display_name=display_name(row["name"]),
        garment_type=row["garment_type"],
        category=categorize(row["garment_type"]),
        colors=colors,
        color_families=families,
        price=row["price"],
        image_url=image_url(row["image_file_path"]),
        sizes=sizes,
        total_stock=total,
        in_stock=total > 0,
    )


def list_products(search: str | None = None) -> list[ProductSummary]:
    """All products (optionally narrowed by a text search), each with its per-size inventory."""
    sql = f"SELECT {_CATALOGUE_COLUMNS} FROM catalogue"
    params: list[str] = []
    if search:
        like = f"%{search.lower()}%"
        sql += (
            " WHERE lower(name) LIKE ? OR lower(description) LIKE ? OR lower(garment_type) LIKE ?"
            " OR lower(colors) LIKE ? OR lower(search_tags) LIKE ?"
        )
        params = [like] * 5
    sql += " ORDER BY name"
    with connect(readonly=True) as conn:
        rows = conn.execute(sql, params).fetchall()
        sizes = _sizes_by_product(conn)
    return [ProductSummary(**_summary_fields(r, sizes.get(r["product_id"], []))) for r in rows]


def get_product(product_id: str) -> ProductDetail | None:
    with connect(readonly=True) as conn:
        row = conn.execute(f"SELECT {_CATALOGUE_COLUMNS} FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        sizes = _sizes_by_product(conn, [product_id]).get(product_id, [])
    fields = _summary_fields(row, sizes)
    return ProductDetail(
        **fields,
        color_details=[ColorInfo(name=c, family=color_family(c)) for c in fields["colors"]],
        description=row["description"],
        search_tags=_json_list(row["search_tags"]),
    )


def catalogue_filters() -> CatalogueFilters:
    products = list_products()
    categories: dict[str, FilterOption] = {}
    for slug, label, _ in [*CATEGORY_RULES, (*OTHER_CATEGORY, ())]:
        categories[slug] = FilterOption(slug=slug, label=label, count=0)
    colors = {slug: FilterOption(slug=slug, label=COLOR_LABELS[slug], count=0) for slug in COLOR_LABELS}
    for p in products:
        cat = categories[p.category.slug]
        cat.count += 1
        if cat.image_url is None and p.in_stock:
            cat.image_url = p.image_url
        for fam in p.color_families:
            colors[fam].count += 1
    prices = [p.price for p in products]
    return CatalogueFilters(
        categories=[c for c in categories.values() if c.count],
        colors=sorted((c for c in colors.values() if c.count), key=lambda c: -c.count),
        price_min=min(prices, default=0),
        price_max=max(prices, default=0),
        total_products=len(products),
    )


# ---------- Natural-language product search (used by the assistant's tools) ----------

# Words shoppers use, mapped to the normalized category slugs above. Broader than CATEGORY_RULES (which only has to
# cover the database's own garment_type labels) because customers write "quarter zip", "tee", "crew", "hoody"...
CATEGORY_SYNONYMS: list[tuple[str, tuple[str, ...]]] = [
    ("quarter-zips", ("quarter zip", "quarter-zip", "1/4 zip", "1 4 zip", "qtr zip", "quarterzip", "half zip")),
    ("hoodies", ("hoodie", "hoody", "hooded", "hood")),
    ("jackets", ("jacket", "fleece", "bomber", "coat")),
    ("long-sleeve", ("long sleeve", "long-sleeve", "longsleeve", "l/s", "performance shirt")),
    ("t-shirts", ("t-shirt", "t shirt", "tshirt", "tee", "short sleeve")),
    ("sweatshirts", ("crewneck", "crew neck", "crew", "sweatshirt", "sweater", "mockneck", "mock neck", "pullover")),
]

# Extra color words customers use that the database spells differently (or doesn't use at all).
COLOR_SYNONYMS: dict[str, str] = {
    "yale blue": "navy",
    "dark blue": "navy",
    "grey": "gray",
    "silver": "gray",
    "heather": "gray",
    "charcoal": "gray",
    "off white": "white",
    "off-white": "white",
    "cream": "white",
    "ivory": "white",
    "maroon": "red",
    "crimson": "red",
    "burgundy": "red",
    "coral": "red",
    "pink": "red",
    "gold": "yellow",
    "royal blue": "blue",
    "light blue": "blue",
    "sky blue": "blue",
}

SIZE_ALIASES: dict[str, str] = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "sm": "S", "small": "S",
    "m": "M", "med": "M", "medium": "M",
    "l": "L", "lg": "L", "large": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "double xl": "XXL", "double extra large": "XXL",
}

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "for", "with", "in", "on", "to", "do", "does", "you", "your", "we", "i",
    "me", "my", "have", "has", "got", "any", "some", "is", "are", "it", "that", "this", "these", "those", "what",
    "which", "show", "find", "looking", "look", "want", "need", "like", "would", "could", "can", "please", "item",
    "items", "product", "products", "one", "ones", "kind", "kinds", "type", "types", "something", "anything",
    "size", "sizes", "color", "colors", "colour", "available", "stock", "price", "cost", "much", "how", "many",
    "campus", "customs", "store", "shop", "sell", "selling", "there", "s", "m", "l", "xl", "xs", "xxl", "small",
    "medium", "large", "extra", "between", "under", "over", "below", "above", "less", "more", "than", "around",
    "about", "cheap", "cheaper", "cheapest", "budget", "dollar", "dollars", "usd", "priced", "affordable",
}


def size_from_text(text: str) -> str | None:
    """Map 'medium', 'M', 'x-large', '2XL'... to the database's size codes, or None if unrecognized."""
    return SIZE_ALIASES.get(re.sub(r"\s+", " ", text.strip().lower()))


def _has_phrase(text: str, phrase: str) -> bool:
    """Whole-word (optionally plural) match, so 'tee' doesn't match 'between' and 'red' doesn't match 'hundred'."""
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?:e?s)?(?![a-z0-9])", text) is not None


def category_from_text(text: str) -> str | None:
    """Map shopper wording ('sweatshirt', 'quarter zip', 'tees', a category label or slug) to a category slug."""
    t = text.strip().lower()
    if t in CATEGORY_SLUGS:
        return t
    for slug, label, _ in CATEGORY_RULES:
        if t == label.lower():
            return slug
    for slug, words in CATEGORY_SYNONYMS:
        if any(_has_phrase(t, w) for w in words):
            return slug
    return None


def color_from_text(text: str) -> str | None:
    """Map shopper wording ('grey', 'Yale blue', 'navy blue', a family slug) to a color family slug."""
    t = text.strip().lower()
    if t in COLOR_SLUGS:
        return t
    for phrase, slug in COLOR_SYNONYMS.items():
        if _has_phrase(t, phrase):
            return slug
    for slug, _, keywords in COLOR_RULES:
        if any(_has_phrase(t, k) for k in keywords):
            return slug
    return None


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _stem(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("es") and word[-3] in "sxz":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _search_text(p: ProductDetail) -> tuple[str, set[str]]:
    """Normalized searchable text for one product, plus its set of stemmed words."""
    parts = [p.name, p.display_name, p.garment_type, p.category.label, p.description, " ".join(p.colors),
             " ".join(p.search_tags), " ".join(p.color_families)]
    text = _norm(" ".join(parts))
    return text, {_stem(w) for w in text.split()}


def all_product_details() -> list[ProductDetail]:
    """Every product with description, tags and per-size inventory (one catalogue query + one inventory query)."""
    with connect(readonly=True) as conn:
        rows = conn.execute(f"SELECT {_CATALOGUE_COLUMNS} FROM catalogue ORDER BY name").fetchall()
        sizes = _sizes_by_product(conn)
    out = []
    for row in rows:
        fields = _summary_fields(row, sizes.get(row["product_id"], []))
        out.append(
            ProductDetail(
                **fields,
                color_details=[ColorInfo(name=c, family=color_family(c)) for c in fields["colors"]],
                description=row["description"],
                search_tags=_json_list(row["search_tags"]),
            )
        )
    return out


def search_products(
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
) -> tuple[list[ProductDetail], bool]:
    """Rank products for a natural-language query. Returns (matches best-first, exact) where exact=False means no
    product matched every query word, so the list holds the closest partial matches instead.

    - category / color accept slugs or shopper wording ('sweatshirt', 'grey'); they filter on the normalized
      fields, so the database's inconsistent labels don't matter.
    - Words in the query that name a category or color are also applied as filters when no explicit filter is given.
    """
    products = all_product_details()
    q = _norm(query)

    cat = category_from_text(category) if category else None
    col = color_from_text(color) if color else None
    if not cat and q:
        cat = category_from_text(q)
    if not col and q:
        col = color_from_text(q)

    # Phrases handled by the category/color filters are removed from the free-text part of the query.
    remaining = f" {q} "
    if cat:
        for slug, words in CATEGORY_SYNONYMS:
            if slug == cat:
                for w in sorted(words, key=len, reverse=True):
                    remaining = remaining.replace(f" {_norm(w)} ", " ")
                    remaining = re.sub(rf" {re.escape(_norm(w))}s ", " ", remaining)
    if col:
        for phrase, slug in COLOR_SYNONYMS.items():
            if slug == col:
                remaining = remaining.replace(f" {_norm(phrase)} ", " ")
        remaining = remaining.replace(f" {col} ", " ")
    tokens = [_stem(w) for w in remaining.split() if w not in _STOPWORDS and _stem(w) not in _STOPWORDS]

    def passes_filters(p: ProductDetail) -> bool:
        if cat and p.category.slug != cat:
            return False
        if col and col not in p.color_families:
            return False
        if max_price is not None and p.price > max_price:
            return False
        if min_price is not None and p.price < min_price:
            return False
        return True

    candidates = [p for p in products if passes_filters(p)]
    if not tokens:
        return candidates, True

    scored: list[tuple[int, int, ProductDetail]] = []
    for p in candidates:
        text, words = _search_text(p)
        name_words = {_stem(w) for w in _norm(p.name).split()}
        hits = name_hits = 0
        for t in tokens:
            if t in words or (len(t) >= 4 and any(w.startswith(t) for w in words)) or f" {t} " in f" {text} ":
                hits += 1
                if t in name_words or any(w.startswith(t) for w in name_words if len(t) >= 4):
                    name_hits += 1
        if hits:
            scored.append((hits, name_hits, p))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2].name))
    exact = [p for h, _, p in scored if h == len(tokens)]
    if exact:
        return exact, True
    return [p for _, _, p in scored], False