"""Pydantic models shared by the API (main.py) and, later, the agent tools (tools.py)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

StockStatus = Literal["in_stock", "low_stock", "sold_out"]


class SizeStock(BaseModel):
    size: str
    quantity: int = Field(ge=0)
    status: StockStatus


class Category(BaseModel):
    slug: str
    label: str


class ColorInfo(BaseModel):
    name: str = Field(description="Original color name from the database")
    family: str = Field(description="Normalized color family slug")


class ProductSummary(BaseModel):
    """What a product card needs. Every value comes from the catalogue and inventory tables."""

    product_id: str
    name: str = Field(description="Name exactly as stored in the catalogue table")
    display_name: str = Field(description="Name with light punctuation clean-up for display (e.g. '1 4 Zip' -> '1/4 Zip')")
    garment_type: str = Field(description="Original garment_type label from the database")
    category: Category = Field(description="Normalized category derived from garment_type")
    colors: list[str] = Field(description="Original color names from the database")
    color_families: list[str] = Field(description="Normalized color groups used for filtering")
    price: float
    image_url: str
    sizes: list[SizeStock]
    total_stock: int
    in_stock: bool


class ProductDetail(ProductSummary):
    color_details: list[ColorInfo]
    description: str
    search_tags: list[str]


class FilterOption(BaseModel):
    slug: str
    label: str
    count: int
    image_url: str | None = None


class CatalogueFilters(BaseModel):
    categories: list[FilterOption]
    colors: list[FilterOption]
    price_min: float
    price_max: float
    total_products: int


class ProductList(BaseModel):
    total: int
    products: list[ProductSummary]


# ---------- Accounts ----------

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PASSWORD_MIN = 8
PASSWORD_MAX = 128


class UserPublic(BaseModel):
    """Account details safe to send to the browser. Never includes the password hash."""

    id: int
    email: str
    first_name: str
    last_name: str
    name: str
    created_at: str


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=254, pattern=EMAIL_PATTERN)
    # Passwords are kept exactly as typed (no whitespace stripping), so they are declared with their own config.
    password: Annotated[str, StringConstraints(strip_whitespace=False, min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)]
    confirm_password: Annotated[str, StringConstraints(strip_whitespace=False, max_length=PASSWORD_MAX)]


class LoginRequest(BaseModel):
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=254)]
    password: str = Field(min_length=1, max_length=PASSWORD_MAX)


# ---------- Shopping assistant (Problem 5) ----------

CHAT_MESSAGE_MAX = 1000  # characters a shopper can type in one message
CHAT_TURN_MAX = 4000  # characters per earlier turn sent back as context (assistant replies can be longer)
CHAT_HISTORY_MAX = 20  # earlier turns kept as context for each request

ChatRole = Literal["user", "assistant"]


CHAT_CARDS_MAX = 6  # product cards shown under one assistant message

ProductIdStr = Annotated[str, StringConstraints(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")]


class ChatTurn(BaseModel):
    """One earlier message in the conversation, sent by the browser so the assistant has context."""

    role: ChatRole
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CHAT_TURN_MAX)]
    # Products shown as cards under an earlier assistant message, so follow-ups ("tell me about the second one")
    # can refer to them. Only ids are sent; everything else is looked up again from the database.
    product_ids: list[ProductIdStr] = Field(default_factory=list, max_length=CHAT_CARDS_MAX)


class PageContext(BaseModel):
    """Which page the customer is looking at when they send a message (Problem 8). Treated as a hint only: the
    backend re-checks the product id against the catalogue and derives everything else itself."""

    path: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] = "/"
    product_id: ProductIdStr | None = None


class ChatRequest(BaseModel):
    """POST /api/chat body.

    - Signed-out visitors: `history` (the conversation on screen) is the only context; nothing is saved.
    - Signed-in customers: `history` is ignored. `conversation_id` picks which of THEIR saved conversations to
      continue (checked against the session's account); null starts a new conversation. Context comes from that
      conversation's saved messages only.
    """

    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CHAT_MESSAGE_MAX)]
    history: list[ChatTurn] = Field(default_factory=list, max_length=CHAT_HISTORY_MAX)
    page: PageContext | None = None
    conversation_id: int | None = Field(default=None, ge=1)


class ProductCard(BaseModel):
    """A product card shown in the chat (Problem 7). Built by the backend from the catalogue + inventory rows for a
    product id the agent chose. The model never supplies names, prices, images or stock."""

    product_id: str
    name: str
    category: str
    price: float
    image_url: str
    url: str = Field(description="Product page path, e.g. /products/<id>")
    colors: list[str]
    in_stock: bool
    available_sizes: list[str]
    size: str | None = Field(default=None, description="Size the customer asked about, if any (e.g. 'M')")
    size_quantity: int | None = None
    size_status: StockStatus | None = None


class ChatResponse(BaseModel):
    """POST /api/chat response."""

    reply: str = Field(description="The assistant's message, plain text with light Markdown (bold, bullet lists)")
    products: list[ProductCard] = Field(default_factory=list, description="Verified product cards (0-6)")
    saved: bool = Field(default=False, description="True when the exchange was saved to the customer's history")
    conversation_id: int | None = Field(default=None, description="Conversation this exchange was saved in")
    user_message_id: int | None = None
    message_id: int | None = Field(default=None, description="Saved id of this assistant message")


class SavedMessage(BaseModel):
    """One message from the signed-in customer's saved history, with cards rebuilt from the current database."""

    id: int
    role: ChatRole
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


class ChatHistory(BaseModel):
    """GET /api/chat/history response: a page of one of the signed-in customer's own conversations, oldest first."""

    conversation_id: int | None = Field(description="Conversation shown (null if the customer has none yet)")
    messages: list[SavedMessage]
    has_more: bool = Field(description="True if older messages exist (request them with before_id)")


class ConversationSummary(BaseModel):
    id: int
    title: str = Field(description="First message that isn't small talk (shortened), or a fallback from its topics")
    topics: list[str] = Field(default_factory=list, description="Up to 3 product categories shown in the conversation")
    preview: str = Field(default="", description="Start of the latest assistant reply")
    started_at: str
    updated_at: str
    message_count: int


class ConversationList(BaseModel):
    """GET /api/chat/conversations: the signed-in customer's conversations, most recently active first."""

    conversations: list[ConversationSummary]


class AgentReply(BaseModel):
    """The agent's structured output: its message plus which products to show as cards."""

    message: str = Field(
        description=(
            "Your reply to the customer (plain text, light Markdown). When cards are shown, introduce them briefly and "
            "say why they fit, using only facts from the tool results. Don't list every card's name and price again."
        )
    )
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id values (exact, from search_products or check_inventory results in this conversation) to show "
            "as product cards, most relevant first, at most 6. Empty when no products should be shown."
        ),
    )
    size: str | None = Field(
        default=None,
        description="The size the customer asked about (XS, S, M, L, XL or XXL), if any; cards then show stock for it",
    )


class AgentDeps(BaseModel):
    """Per-request context handed to the agent and its tools. Contains no secrets."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    customer_first_name: str | None = None
    # Problem 9: the message is pure small talk ("thanks!"), so the database tools are not offered for this turn.
    small_talk: bool = False
    # Problem 9: callback the tools use to report what they are ACTUALLY doing (shown to the shopper while waiting).
    progress: Callable[[dict], None] | None = Field(default=None, exclude=True)
    signed_in: bool = False
    # Plain-English description of the page the customer is on, built by the backend (never raw browser text).
    page_description: str | None = None
    # Product on the current page, verified against the catalogue.
    page_product_id: str | None = None
    page_product_name: str | None = None
    # Signed-in customers: True when this message starts a brand-new conversation (no earlier context).
    new_conversation: bool = False
    # When context came from a saved conversation: how many of its messages, and the dates they span.
    saved_turns: int = 0
    saved_from: str | None = None
    saved_to: str | None = None
    # Every product id a tool returned (or that was shown in an earlier card) during this conversation. Cards are
    # only built for ids in this set, so the model can't introduce a product the tools didn't produce.
    seen_product_ids: set[str] = Field(default_factory=set)
    # Problem 12: audit.AuditRecord for this request (tools add their calls to it). Not sent to the model.
    audit: Any = Field(default=None, exclude=True)

# ---------- Assistant tool results (Problem 6) ----------
# Everything in these models comes straight from the catalogue and inventory tables via catalogue.py.


class ProductInfo(BaseModel):
    """One product as returned by the search_products tool (catalogue table only; stock comes from check_inventory)."""

    product_id: str = Field(description="Use this exact id with check_inventory")
    name: str = Field(description="Customer-facing product name")
    category: str = Field(description="Normalized category, e.g. 'Hoodies'")
    garment_type: str = Field(description="Original garment type wording from the database")
    colors: list[str]
    price: float = Field(description="Price in US dollars")
    description: str
    tags: list[str]
    page: str = Field(description="Product page path on the website")


class ProductSearchResult(BaseModel):
    query: str
    filters_applied: list[str] = Field(description="Category / color / price filters that were applied")
    exact_match: bool = Field(
        description="False if no product matched every word, so `products` lists the closest partial matches"
    )
    total_matches: int
    products: list[ProductInfo] = Field(description="Best matches first; at most `limit` items")
    note: str = ""


class SizeAvailability(BaseModel):
    size: str
    quantity: int = Field(ge=0)
    status: StockStatus


class InventoryResult(BaseModel):
    """Result of the check_inventory tool (inventory table, joined to the product's catalogue name)."""

    found: bool
    product_id: str
    name: str | None = None
    price: float | None = None
    requested_size: str | None = Field(default=None, description="Normalized size code, e.g. 'M'")
    requested_size_quantity: int | None = None
    requested_size_status: StockStatus | None = None
    sizes: list[SizeAvailability] = Field(default_factory=list)
    available_sizes: list[str] = Field(default_factory=list)
    sold_out_sizes: list[str] = Field(default_factory=list)
    total_in_stock: int = 0
    suggestions: list[str] = Field(default_factory=list, description="'product_id: name' pairs when not found")
    message: str = ""