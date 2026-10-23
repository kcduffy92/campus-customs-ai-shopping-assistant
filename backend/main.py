"""Campus Customs FastAPI backend.

Run from hw4/backend/ with the project virtual environment active (the frontend dev server proxies /api and /media):
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import agent
import audit
import auth
import catalogue
import chat_history
import users
from config import COOKIE_SECURE, FRONTEND_ORIGINS, MEDIA_URL, PRODUCTS_DIR, SESSION_SECRET_IS_TEMPORARY
from db import DatabaseUnavailable
from models import (
    CHAT_MESSAGE_MAX,
    PASSWORD_MAX,
    PASSWORD_MIN,
    AgentDeps,
    CatalogueFilters,
    ChatHistory,
    ChatRequest,
    ChatResponse,
    ConversationList,
    ConversationSummary,
    SavedMessage,
    LoginRequest,
    ProductDetail,
    ProductList,
    RegisterRequest,
    UserPublic,
)

log = logging.getLogger("campus_customs")
# App logs (including every assistant tool call) go to the console next to uvicorn's own output.
if not log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s:     [%(name)s] %(message)s"))
    log.addHandler(_handler)
    log.setLevel(logging.INFO)
    log.propagate = False

@asynccontextmanager
async def lifespan(_: FastAPI):
    # One-time, idempotent schema update for separate conversations (backs up the database before changing it).
    try:
        chat_history.ensure_schema()
    except DatabaseUnavailable as exc:
        log.error("Database unavailable at startup: %s", exc)
    yield


app = FastAPI(title="Campus Customs API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=True,
)

# Product images stay in hw4/data/products (git-ignored) and are served from there, e.g. /media/products/<file>.jpg.
if PRODUCTS_DIR.is_dir():
    app.mount(f"{MEDIA_URL}/products", StaticFiles(directory=PRODUCTS_DIR), name="product-images")

if SESSION_SECRET_IS_TEMPORARY:
    log.warning("SESSION_SECRET is not set in .env; using a temporary key (sign-ins reset when the server restarts).")


# ---------- Error handling: shoppers see plain-English messages, never stack traces ----------

FIELD_MESSAGES = {
    "first_name": "Please enter your first name (up to 50 characters).",
    "last_name": "Please enter your last name (up to 50 characters).",
    "email": "Please enter a valid email address, like name@example.com.",
    "password": f"Your password must be {PASSWORD_MIN}–{PASSWORD_MAX} characters.",
    "confirm_password": "Please confirm your password.",
    "message": f"Please type a message (up to {CHAT_MESSAGE_MAX:,} characters).",
    "history": "The conversation is too long to continue here. Please start a new chat.",
}


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: dict[str, str] = {}
    for err in exc.errors():
        loc = [p for p in err.get("loc", ()) if isinstance(p, str) and p not in ("body", "query", "path")]
        name = loc[0] if loc else ""
        if name and name not in fields:
            if request.url.path == "/api/auth/login" and name in ("email", "password"):
                fields[name] = f"Please enter your {name}."
            else:
                fields[name] = FIELD_MESSAGES.get(name, "Please check this value.")
    detail = "Please check the highlighted fields." if fields else "We couldn't read that request. Please try again."
    if request.url.path.startswith("/api/chat"):
        # Audit: an invalid chat request was stopped before reaching the assistant. Only field names are recorded.
        try:
            user = current_user(request)
        except Exception:
            user = None
        audit.simple_event("chat_request_rejected", request.url.path, user_id=user.id if user else None, status="blocked",
                           category=audit.VALIDATION_ERROR, http_status=422, detail={"invalid_fields": sorted(fields) or ["body"]})
    return JSONResponse(status_code=422, content={"detail": detail, "fields": fields})


class FormError(Exception):
    """A problem with what the shopper entered: a friendly summary plus per-field messages."""

    def __init__(self, status_code: int, detail: str, fields: dict[str, str] | None = None):
        self.status_code, self.detail, self.fields = status_code, detail, fields or {}


@app.exception_handler(FormError)
async def form_error(_: Request, exc: FormError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "fields": exc.fields})


@app.exception_handler(DatabaseUnavailable)
async def database_unavailable(_: Request, exc: DatabaseUnavailable) -> JSONResponse:
    log.error("Database unavailable: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "The store is temporarily unavailable. Please try again shortly."})


@app.exception_handler(Exception)
async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our end. Please try again."})


ProductId = Annotated[str, Path(min_length=1, max_length=120, pattern=r"^[a-z0-9-]+$")]
SortOption = Literal["name", "price_asc", "price_desc"]


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"service": "Campus Customs API", "docs": "/docs", "health": "/api/health"}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "products_dir": PRODUCTS_DIR.is_dir()}


@app.get("/api/products", response_model=ProductList)
def list_products(
    category: Annotated[str | None, Query(max_length=40, description="Category slug from /api/filters")] = None,
    color: Annotated[str | None, Query(max_length=40, description="Color family slug from /api/filters")] = None,
    q: Annotated[str | None, Query(max_length=100, description="Text search across name, description, tags, colors")] = None,
    in_stock: Annotated[bool, Query(description="Only products with at least one size in stock")] = False,
    sort: SortOption = "name",
) -> ProductList:
    if category and category not in catalogue.CATEGORY_SLUGS:
        raise HTTPException(status_code=422, detail=f"Unknown category '{category}'.")
    if color and color not in catalogue.COLOR_SLUGS:
        raise HTTPException(status_code=422, detail=f"Unknown color '{color}'.")

    products = catalogue.list_products(search=(q or "").strip() or None)
    if category:
        products = [p for p in products if p.category.slug == category]
    if color:
        products = [p for p in products if color in p.color_families]
    if in_stock:
        products = [p for p in products if p.in_stock]
    if sort == "price_asc":
        products.sort(key=lambda p: (p.price, p.name))
    elif sort == "price_desc":
        products.sort(key=lambda p: (-p.price, p.name))
    return ProductList(total=len(products), products=products)


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: ProductId) -> ProductDetail:
    product = catalogue.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@app.get("/api/filters", response_model=CatalogueFilters)
def get_filters() -> CatalogueFilters:
    return catalogue.catalogue_filters()


# ---------- Accounts ----------


def _start_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        auth.SESSION_COOKIE,
        auth.create_session_token(user_id),
        max_age=auth.SESSION_MAX_AGE,
        httponly=True,  # not readable by JavaScript
        samesite="lax",  # not sent on cross-site form posts
        secure=COOKIE_SECURE,
        path="/",
    )


def current_user(request: Request) -> UserPublic | None:
    user_id = auth.read_session_token(request.cookies.get(auth.SESSION_COOKIE))
    return users.get_user(user_id) if user_id is not None else None


@app.post("/api/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, response: Response) -> UserPublic:
    if body.password != body.confirm_password:
        raise FormError(422, "Your passwords don't match.", {"confirm_password": "Passwords don't match."})
    try:
        user = users.create_user(body.first_name, body.last_name, body.email, auth.hash_password(body.password))
    except users.EmailAlreadyRegistered:
        raise FormError(
            409,
            "An account with this email already exists. Try signing in instead.",
            {"email": "This email is already registered."},
        )
    _start_session(response, user.id)
    return user


@app.post("/api/auth/login", response_model=UserPublic)
def login(body: LoginRequest, response: Response) -> UserPublic:
    record = users.get_login_record(body.email)
    if record is None:
        auth.burn_equivalent_time(body.password)  # same response time as a wrong password
    elif auth.verify_password(body.password, record[1]):
        _start_session(response, record[0].id)
        return record[0]
    # One message for unknown email and wrong password, so the form doesn't reveal which emails have accounts.
    raise FormError(401, "That email and password don't match our records. Please try again.")


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(auth.SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=COOKIE_SECURE)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


ASSISTANT_UNAVAILABLE = "Our shopping assistant is unavailable right now. Please try again in a moment."


def _prepare_chat(body: ChatRequest, user: UserPublic | None) -> tuple[AgentDeps, list, int | None]:
    """Shared by /api/chat and /api/chat/stream: verified page context, identity, and which history to use.

    Identity comes only from the signed session cookie (current_user). Signed-in customers get the chosen
    conversation's saved messages as context (ownership-checked); signed-out visitors use the browser's history.
    """
    page_description, page_product = agent.describe_page(
        body.page.path if body.page else None, body.page.product_id if body.page else None
    )
    deps = AgentDeps(
        customer_first_name=user.first_name if user else None,
        signed_in=user is not None,
        page_description=page_description,
        page_product_id=page_product.product_id if page_product else None,
        page_product_name=page_product.display_name if page_product else None,
    )
    if page_product:
        deps.seen_product_ids.add(page_product.product_id)  # the verified page product may be shown as a card

    conversation_id = body.conversation_id if user else None
    if user and conversation_id is not None:
        # Continue one of THIS customer's conversations; an id that isn't theirs is treated as not found.
        if not chat_history.owns_conversation(user.id, conversation_id):
            raise FormError(404, "That conversation couldn't be found. Please start a new chat.")
        history, deps.saved_from, deps.saved_to = chat_history.context_turns(user.id, conversation_id)
        deps.saved_turns = len(history)
    elif user:
        history = []  # New conversation: no earlier context.
        deps.new_conversation = True
    else:
        history = body.history
    return deps, history, conversation_id


def _start_chat(endpoint: str, body: ChatRequest, request: Request) -> tuple[UserPublic | None, AgentDeps, list, int | None]:
    """Problem 12: open the audit record as soon as a chat message arrives, then prepare the request.

    Requests stopped here (someone else's conversation, database down) are recorded as blocked/failed.
    """
    record = audit.AuditRecord(endpoint, message=body.message)
    try:
        user = current_user(request)
        record.set_customer(user.id if user else None)
        deps, history, conversation_id = _prepare_chat(body, user)
    except FormError as exc:
        record.finish("blocked", http_status=exc.status_code, category=audit.CONVERSATION_NOT_OWNED, error=exc.detail)
        raise
    except Exception as exc:
        record.finish("failed", http_status=503, category=audit.classify(exc), error=audit.short_error(exc))
        raise
    deps.audit = record
    record.set_context(
        conversation_id=conversation_id,
        new_conversation=bool(user and conversation_id is None),
        context_messages=len(history),
        page_path=body.page.path if body.page else None,
        page_product_id=deps.page_product_id,
    )
    return user, deps, history, conversation_id


async def _run_chat(body: ChatRequest, user: UserPublic | None, deps: AgentDeps, history: list, conversation_id: int | None) -> ChatResponse:
    """Run the agent and save the exchange for signed-in customers. Raises FormError(503) if the assistant fails."""
    record: audit.AuditRecord = deps.audit
    try:
        response = await agent.reply(body.message, history, deps)
    except agent.AssistantUnavailable as exc:
        log.error("Assistant unavailable [%s] (%s): %s", exc.category, record.request_id, exc)
        record.finish("failed", http_status=503, category=exc.category, error=audit.short_error(exc))
        raise FormError(503, ASSISTANT_UNAVAILABLE)
    except Exception as exc:
        category = audit.classify(exc)
        log.exception("Unexpected assistant error [%s] (%s)", category, record.request_id)
        record.finish("failed", http_status=503, category=category, error=audit.short_error(exc))
        raise FormError(503, ASSISTANT_UNAVAILABLE)

    save_error = None
    if user:
        try:
            response.conversation_id, response.user_message_id, response.message_id = chat_history.save_exchange(
                user.id, conversation_id, body.message, response.reply, response.products
            )
            response.saved = True
            record.data["conversation"]["conversation_ref"] = audit.conversation_ref(response.conversation_id)
        except Exception as exc:
            # The customer still gets the answer; it just isn't in their saved history.
            log.exception("Could not save chat messages (%s)", record.request_id)
            save_error = f"history not saved [{audit.classify(exc)}]: {audit.short_error(exc)}"
    record.finish(
        "blocked" if record.blocked_by else "success",
        http_status=200,
        category=record.blocked_by,
        reply_chars=len(response.reply),
        cards=len(response.products),
        saved=response.saved if user else None,
        error=save_error,
    )
    return response


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """One turn with the shopping assistant (single JSON response)."""
    user, deps, history, conversation_id = _start_chat("/api/chat", body, request)
    return await _run_chat(body, user, deps, history, conversation_id)


@app.post("/api/chat/stream")
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    """Same as /api/chat, but streams newline-delimited JSON so the shopper sees what the assistant is doing:

        {"type": "status", "stage": "thinking" | "searching" | "inventory" | "reviewing", "text": "..."}   (0 or more)
        {"type": "result", "data": <ChatResponse>}                                                       (last line)
        {"type": "error", "status": 503, "detail": "..."}                                                (instead)

    Status lines come only from code that is actually running (the agent starting, a tool starting or finishing),
    so the interface never claims to check stock unless check_inventory is really running. Validation, sign-in and
    conversation ownership are checked before streaming starts and return normal JSON errors.
    """
    user, deps, history, conversation_id = _start_chat("/api/chat/stream", body, request)
    queue: asyncio.Queue[dict] = asyncio.Queue()
    deps.progress = lambda event: queue.put_nowait({"type": "status", **event})

    async def run() -> None:
        try:
            response = await _run_chat(body, user, deps, history, conversation_id)
            queue.put_nowait({"type": "result", "data": response.model_dump()})
        except FormError as exc:
            queue.put_nowait({"type": "error", "status": exc.status_code, "detail": exc.detail})
        except Exception as exc:
            log.exception("Unexpected streaming error")
            deps.audit.finish("failed", http_status=503, category=audit.classify(exc), error=audit.short_error(exc))
            queue.put_nowait({"type": "error", "status": 503, "detail": ASSISTANT_UNAVAILABLE})

    # The answer is produced (and saved) even if the shopper closes the page mid-way, same as /api/chat.
    task = asyncio.create_task(run())

    async def events():
        while True:
            event = await queue.get()
            yield json.dumps(event) + "\n"
            if event["type"] in ("result", "error"):
                break
        await task

    return StreamingResponse(
        events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.get("/api/chat/conversations", response_model=ConversationList)
def get_conversations(request: Request) -> ConversationList:
    """The signed-in customer's own conversations, most recently active first."""
    user = current_user(request)
    if user is None:
        raise FormError(401, "Sign in to see your saved conversations.")
    return ConversationList(conversations=[ConversationSummary(**c) for c in chat_history.list_conversations(user.id)])


@app.get("/api/chat/history", response_model=ChatHistory)
def get_chat_history(
    request: Request,
    conversation_id: Annotated[int | None, Query(ge=1, description="Conversation to show; default: most recent")] = None,
    before_id: Annotated[int | None, Query(ge=1, description="Return messages older than this id")] = None,
    limit: Annotated[int, Query(ge=1, le=chat_history.PAGE_MAX)] = 30,
) -> ChatHistory:
    """A page of one of the signed-in customer's conversations (oldest-to-newest within the page).

    There is deliberately no user id parameter: the account comes only from the session cookie, and every query
    filters on it, so changing request parameters can't reveal another customer's messages. A conversation id that
    belongs to someone else is reported as not found.
    """
    user = current_user(request)
    if user is None:
        raise FormError(401, "Sign in to see your saved conversations.")
    if conversation_id is None:
        conversation_id = chat_history.latest_conversation_id(user.id)
        if conversation_id is None:
            return ChatHistory(conversation_id=None, messages=[], has_more=False)
    elif not chat_history.owns_conversation(user.id, conversation_id):
        audit.simple_event("conversation_access_denied", "/api/chat/history", user_id=user.id, status="blocked",
                           category=audit.CONVERSATION_NOT_OWNED, http_status=404)
        raise FormError(404, "That conversation couldn't be found.")
    rows, has_more = chat_history.history_page(user.id, conversation_id, before_id, limit)
    messages = []
    for r in rows:
        ids, size = chat_history.product_ids_and_size(r["products_json"]) if r["role"] == "assistant" else ([], None)
        messages.append(
            SavedMessage(
                id=r["id"],
                role=r["role"],
                content=r["content"],
                products=agent.restored_cards(ids, size),
                created_at=r["created_at"],
            )
        )
    return ChatHistory(conversation_id=conversation_id, messages=messages, has_more=has_more)


@app.get("/api/auth/me", response_model=UserPublic | None)
def me(request: Request) -> UserPublic | None:
    """The signed-in shopper, or null when nobody is signed in (a normal state, so not an error)."""
    return current_user(request)
