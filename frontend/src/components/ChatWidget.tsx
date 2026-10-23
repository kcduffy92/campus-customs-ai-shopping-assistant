import { useCallback, useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { useLocation } from "react-router";
import { brand } from "../brand/brand.ts";
import { ApiError, fetchChatHistory, fetchConversations, sendChatStream, type ChatStatus } from "../api.ts";
import { useAuth } from "../auth/AuthContext.tsx";
import type { ChatProductCard, ChatTurn, ConversationSummary, PageContext, SavedChatMessage } from "../types.ts";
import ChatMarkdown from "./ChatMarkdown.tsx";
import ChatProductCards from "./ChatProductCards.tsx";
import { DanActivity, DanFoundIt, DanMedallion, danModeForStage } from "./DanMascot.tsx";
import { preloadDanSprites } from "../brand/dan.ts";
import { onOpenChat } from "../chatEvents.ts";

type MessageKind = "user" | "assistant" | "error" | "notice";

interface ChatMessage {
  id: string;
  kind: MessageKind;
  content: string;
  /** For assistant messages: product cards built by the backend from database records. */
  products?: ChatProductCard[];
  /** Id in the customer's saved history (signed-in customers only). */
  savedId?: number;
  /** True only for a LIVE reply that came back with product cards: shows Dan's cookie pop-up once. */
  celebrate?: boolean;
  /** For error messages: the shopper message to resend when they press "Try again". */
  retryText?: string;
}

const MAX_LENGTH = 1000; // matches CHAT_MESSAGE_MAX in backend/models.py
const HISTORY_TURNS = 20; // matches CHAT_HISTORY_MAX
const HISTORY_TURN_CHARS = 4000; // matches CHAT_TURN_MAX
const REQUEST_TIMEOUT_MS = 60_000;
const STATUS_MIN_MS = 700; // each progress message stays readable for at least this long

const GREETING =
  "I'm Handsome Dan, the Campus Customs shopping assistant (an AI). I can sniff out the right hoodie, crewneck, quarter-zip or tee, check sizes and stock, and suggest ideas for game day or gifting.";

function welcome(firstName: string | null, mode: "new" | "restored"): ChatMessage {
  let content: string;
  if (!firstName) content = `Hi, and welcome to Campus Customs! ${GREETING} What are you looking for today?`;
  else if (mode === "restored")
    content = `Welcome back, ${firstName}! Here's your most recent conversation, so you can pick up where you left off. Start a **New chat** any time, or open an older one from **Chats**.`;
  else content = `Hi ${firstName}! This is a new conversation. ${GREETING} What can I help you find?`;
  return { id: "welcome", kind: "assistant", content };
}

function fromSaved(m: SavedChatMessage): ChatMessage {
  return { id: `saved-${m.id}`, kind: m.role, content: m.content, products: m.products, savedId: m.id };
}

/** Signed-out visitors: the conversation on screen is the assistant's only context. */
function toHistory(messages: ChatMessage[]): ChatTurn[] {
  return messages
    .filter((m) => m.id !== "welcome" && (m.kind === "user" || m.kind === "assistant"))
    .slice(-HISTORY_TURNS)
    .map((m) => ({
      role: m.kind === "user" ? "user" : "assistant",
      content: m.content.slice(0, HISTORY_TURN_CHARS),
      ...(m.products?.length ? { product_ids: m.products.map((p) => p.product_id) } : {}),
    }));
}

/** The page the customer is on, sent with each message. The backend verifies the product id itself. */
function pageContext(pathname: string, search: string): PageContext {
  const match = pathname.match(/^\/products\/([a-z0-9-]+)\/?$/);
  return { path: `${pathname}${search}`.slice(0, 300), product_id: match ? match[1] : null };
}

/** Saved times are UTC text ("YYYY-MM-DD HH:MM:SS"); read them in the shopper's time zone. */
function parseUtc(utc: string): Date {
  return new Date(utc.replace(" ", "T") + "Z");
}

function formatWhen(utc: string): string {
  const d = parseUtc(utc);
  if (Number.isNaN(d.getTime())) return utc;
  const sameDay = d.toDateString() === new Date().toDateString();
  return sameDay
    ? d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
    : d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: d.getFullYear() === new Date().getFullYear() ? undefined : "numeric" });
}

/** "Today", "Yesterday", "Previous 7 days" or "Earlier", for grouping the conversation list. */
function dateGroup(utc: string): string {
  const d = parseUtc(utc);
  if (Number.isNaN(d.getTime())) return "Earlier";
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  const days = Math.floor((startOfToday.getTime() - new Date(d).setHours(0, 0, 0, 0)) / 86_400_000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return "Previous 7 days";
  return "Earlier";
}

/** Short header status for each stage; the full wording from the backend goes in the typing bubble. */
const STAGE_LABEL: Record<ChatStatus["stage"], string> = {
  thinking: "Thinking…",
  searching: "Searching products…",
  inventory: "Checking stock…",
  reviewing: "Writing a reply…",
};

function friendlyError(err: unknown): string {
  if (err instanceof DOMException && err.name === "AbortError") {
    return "That took longer than expected. Please try again.";
  }
  if (err instanceof ApiError) {
    // 4xx and 503 carry a plain-English message from the backend; other failures (server down, proxy errors) don't.
    // The chat has no form fields to highlight, so show the specific field message when there is one.
    if (err.status >= 400 && err.status < 500) return err.fields.message ?? err.fields.history ?? err.message;
    if (err.status === 503) return err.message;
    if (err.status >= 500) return "Our shopping assistant is unavailable right now. Please try again in a moment.";
  }
  return "We couldn't reach our shopping assistant. Please check your connection and try again.";
}

/** Handsome Dan's head on a cream disc; falls back to the "CC" monogram if the image can't load. */
function Avatar({ size }: { size?: "sm" | "lg" }) {
  const [failed, setFailed] = useState(false);
  const cls = `chat-avatar${size ? ` chat-avatar--${size}` : ""}`;
  return brand.mascot.chatAvatar && !failed ? (
    <img className={cls} src={brand.mascot.chatAvatar} alt="" onError={() => setFailed(true)} draggable={false} />
  ) : (
    <span className={`${cls} chat-avatar--placeholder`} aria-hidden="true">
      CC
    </span>
  );
}

/**
 * Floating chat widget connected to the Campus Customs shopping assistant.
 * - Signed-in customers have separate saved conversations (stored on the server, so they follow the account across
 *   devices). The most recent one opens automatically; "New chat" starts a fresh one; "Chats" lists older ones.
 * - Signed-out visitors: the conversation lives only on this page.
 * - The widget resets whenever the signed-in account changes, so one customer never sees another's messages.
 */
export default function ChatWidget() {
  const { user, checking } = useAuth();
  const { pathname, search } = useLocation();
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<"chat" | "conversations">("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([welcome(null, "new")]);
  /** Saved conversation shown (signed-in customers). null = a new conversation that hasn't been saved yet. */
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [hasMoreSaved, setHasMoreSaved] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [conversations, setConversations] = useState<ConversationSummary[] | null>(null);
  const [conversationsError, setConversationsError] = useState<string | null>(null);
  const [conversationFilter, setConversationFilter] = useState("");
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  /** Latest progress reported by the backend while a reply is being prepared (null = nothing reported yet). */
  const [status, setStatus] = useState<ChatStatus | null>(null);
  const [waitSeconds, setWaitSeconds] = useState(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const inFlight = useRef<AbortController | null>(null);
  const conversation = useRef(0); // bumped whenever the shown conversation changes, so late replies are dropped
  const statusQueue = useRef<{ items: ChatStatus[]; shownAt: number; timer: number | null }>({ items: [], shownAt: 0, timer: null });
  const skipAutoScroll = useRef(false);
  const panelId = useId();
  const titleId = useId();
  const userId = user?.id ?? null;
  const firstName = user?.first_name ?? null;
  const onProductPage = /^\/products\/[a-z0-9-]+\/?$/.test(pathname);

  /** Stop anything in flight and mark a new conversation on screen. Returns the new conversation token. */
  const resetConversation = useCallback(() => {
    conversation.current += 1;
    inFlight.current?.abort();
    inFlight.current = null;
    setPending(false);
    if (statusQueue.current.timer !== null) window.clearTimeout(statusQueue.current.timer);
    statusQueue.current = { items: [], shownAt: 0, timer: null };
    setStatus(null);
    setHasMoreSaved(false);
    return conversation.current;
  }, []);

  /** Show one of the signed-in customer's saved conversations (the most recent one if no id is given). */
  const loadConversation = useCallback(
    async (name: string, id?: number) => {
      const token = resetConversation();
      setView("chat");
      setLoadingHistory(true);
      setMessages([welcome(name, id ? "restored" : "new")]);
      try {
        const page = await fetchChatHistory({ conversationId: id });
        if (token !== conversation.current) return;
        setConversationId(page.conversation_id);
        setHasMoreSaved(page.has_more);
        const restored = page.messages.map(fromSaved);
        setMessages([welcome(name, restored.length ? "restored" : "new"), ...restored]);
      } catch (err) {
        if (token !== conversation.current) return;
        setConversationId(null);
        setMessages([
          welcome(name, "new"),
          {
            id: "history-error",
            kind: "notice",
            content:
              err instanceof ApiError && err.status === 404
                ? "That conversation couldn't be found"
                : "Couldn't load your conversation. You can still start a new chat",
          },
        ]);
      } finally {
        if (token === conversation.current) setLoadingHistory(false);
      }
    },
    [resetConversation],
  );

  // Reset whenever the account changes (sign in, sign out, switch customer) so nothing carries over between people.
  useEffect(() => {
    if (checking) return;
    resetConversation();
    setDraft("");
    setView("chat");
    setConversations(null);
    setConversationId(null);
    setMessages([welcome(firstName, "new")]);
    // Problem 8's first version kept a per-browser "New chat" marker; conversations now live on the server.
    Object.keys(localStorage)
      .filter((k) => k.startsWith("cc_chat_view_after_"))
      .forEach((k) => localStorage.removeItem(k));
    if (userId !== null && firstName !== null) void loadConversation(firstName);
  }, [checking, userId, firstName, loadConversation, resetConversation]);

  useEffect(() => {
    if (open && view === "chat") inputRef.current?.focus();
  }, [open, view]);

  // Start downloading Dan's two animation strips the first time the chat opens (not on every page load).
  useEffect(() => {
    if (open) preloadDanSprites();
  }, [open]);

  // Other parts of the site (homepage, product pages) can open the chat, optionally with an editable draft.
  useEffect(
    () =>
      onOpenChat((suggested) => {
        setOpen(true);
        setView("chat");
        if (suggested) setDraft((current) => (current.trim() ? current : suggested));
        window.setTimeout(() => inputRef.current?.focus(), 50);
      }),
    [],
  );

  useEffect(() => {
    if (skipAutoScroll.current) {
      skipAutoScroll.current = false;
      return;
    }
    // Jump (not animate) to the newest message so the latest reply is always visible. The DOM is already updated
    // here; the second jump after the next frame covers any late layout (e.g. a card row finishing its layout).
    const toBottom = () => {
      const log = logRef.current;
      if (log) log.scrollTop = log.scrollHeight;
    };
    toBottom();
    const frame = requestAnimationFrame(toBottom);
    return () => cancelAnimationFrame(frame);
  }, [messages, pending, open, view]);

  // Cancel a request still waiting when the widget unmounts.
  useEffect(() => () => inFlight.current?.abort(), []);

  const close = () => {
    setOpen(false);
    launcherRef.current?.focus();
  };

  // Opening a product from a card: on phones the panel covers the page, so tuck it away (the conversation is kept
  // and reopens with the launcher). On larger screens the chat stays open beside the product page.
  const onCardOpen = () => {
    if (window.matchMedia("(max-width: 640px)").matches) setOpen(false);
  };

  /**
   * Show each progress update for at least STATUS_MIN_MS so quick steps (a 10 ms stock lookup) are readable. This
   * only paces the status text; the reply itself is shown the moment it arrives.
   */
  const showStatus = useCallback((s: ChatStatus) => {
    const q = statusQueue.current;
    q.items.push(s);
    const next = () => {
      q.timer = null;
      const item = q.items.shift();
      if (!item) return;
      setStatus(item);
      q.shownAt = Date.now();
      if (q.items.length) q.timer = window.setTimeout(next, STATUS_MIN_MS);
    };
    if (q.timer === null) {
      const wait = Math.max(0, STATUS_MIN_MS - (Date.now() - q.shownAt));
      q.timer = window.setTimeout(next, q.shownAt ? wait : 0);
    }
  }, []);
  const clearStatus = useCallback(() => {
    const q = statusQueue.current;
    if (q.timer !== null) window.clearTimeout(q.timer);
    statusQueue.current = { items: [], shownAt: 0, timer: null };
    setStatus(null);
  }, []);

  async function ask(text: string, prior: ChatMessage[], userMessageLocalId: string) {
    setPending(true);
    clearStatus();
    const token = conversation.current;
    const controller = new AbortController();
    inFlight.current = controller;
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const res = await sendChatStream(
        {
          message: text,
          history: userId === null ? toHistory(prior) : [],
          page: pageContext(pathname, search),
          conversation_id: userId === null ? null : conversationId,
        },
        // Only show progress for this conversation's own request.
        (s) => {
          if (token === conversation.current) showStatus(s);
        },
        controller.signal,
      );
      if (token !== conversation.current) return;
      if (res.conversation_id) {
        setConversationId(res.conversation_id);
        setConversations(null); // list is stale now; reloaded next time it's opened
      }
      setMessages((m) => [
        ...m.map((msg) => (msg.id === userMessageLocalId && res.user_message_id ? { ...msg, savedId: res.user_message_id } : msg)),
        {
          id: res.message_id ? `saved-${res.message_id}` : crypto.randomUUID(),
          kind: "assistant",
          content: res.reply,
          products: res.products ?? [],
          savedId: res.message_id ?? undefined,
          // Celebrate only when this live reply really came back with verified product cards.
          celebrate: (res.products ?? []).length > 0,
        },
      ]);
    } catch (err) {
      if (token !== conversation.current) return;
      setMessages((m) => [...m, { id: crypto.randomUUID(), kind: "error", content: friendlyError(err), retryText: text }]);
    } finally {
      clearTimeout(timer);
      if (inFlight.current === controller) {
        inFlight.current = null;
        setPending(false);
        clearStatus();
      }
    }
  }

  // Count the seconds while waiting, so a long lookup visibly keeps progressing instead of looking frozen.
  useEffect(() => {
    if (!pending) {
      setWaitSeconds(0);
      return;
    }
    const started = Date.now();
    const interval = setInterval(() => setWaitSeconds(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(interval);
  }, [pending]);

  const send = (e?: FormEvent) => {
    e?.preventDefault();
    const text = draft.trim();
    if (!text || pending || loadingHistory) return;
    const prior = messages;
    const localId = crypto.randomUUID();
    setMessages([...prior, { id: localId, kind: "user", content: text }]);
    setDraft("");
    void ask(text, prior, localId);
  };

  const retry = (errorId: string, text: string) => {
    if (pending) return;
    // Drop the error notice; the shopper's original message is already in the conversation (and wasn't saved,
    // because messages are only saved together with a successful reply).
    const remaining = messages.filter((m) => m.id !== errorId);
    setMessages(remaining);
    const userMsg = [...remaining].reverse().find((m) => m.kind === "user");
    void ask(text, remaining.slice(0, -1), userMsg?.id ?? "");
  };

  /** Start a fresh conversation. Nothing is deleted: earlier conversations stay under "Chats". */
  const startNew = () => {
    resetConversation();
    setConversationId(null);
    setView("chat");
    setMessages([welcome(firstName, "new")]);
    setDraft("");
    inputRef.current?.focus();
  };

  const openConversationList = async () => {
    setView("conversations");
    setConversationFilter("");
    setConversationsError(null);
    try {
      const res = await fetchConversations();
      setConversations(res.conversations);
    } catch {
      setConversationsError("We couldn't load your conversations. Please try again.");
    }
  };

  const openConversation = (id: number) => {
    if (firstName === null) return;
    if (id === conversationId) {
      setView("chat");
      return;
    }
    void loadConversation(firstName, id);
  };

  /** Load older messages of the conversation that's open. */
  const showEarlier = async () => {
    if (userId === null || conversationId === null || loadingHistory) return;
    const oldest = messages.find((m) => m.savedId)?.savedId;
    if (!oldest) return;
    const token = conversation.current;
    skipAutoScroll.current = true;
    setLoadingHistory(true);
    try {
      const page = await fetchChatHistory({ conversationId, beforeId: oldest });
      if (token !== conversation.current) return;
      const [first, ...rest] = messages;
      setMessages([first, ...page.messages.map(fromSaved), ...rest]);
      setHasMoreSaved(page.has_more);
    } catch {
      /* keep what is shown; the button stays available */
    } finally {
      if (token === conversation.current) setLoadingHistory(false);
    }
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const lastError = [...messages].reverse().find((m) => m.kind === "error");
  const signedIn = userId !== null;
  const showNewChat = view === "chat" && (messages.length > 1 || conversationId !== null);

  return (
    <div className="chat" data-open={open} onKeyDown={(e) => e.key === "Escape" && open && close()}>
      {open && (
        <section id={panelId} className="chat__panel" role="dialog" aria-modal="false" aria-labelledby={titleId}>
          <header className="chat__header">
            <Avatar size="lg" />
            <div className="chat__header-text">
              <h2 id={titleId} className="chat__title">{brand.assistantName}</h2>
              <p className="chat__status">
                <span className="chat__status-dot" data-busy={pending || undefined} aria-hidden="true" />
                {pending ? (
                  status ? STAGE_LABEL[status.stage] : "Thinking…"
                ) : (
                  "Shopping assistant"
                )}
              </p>
            </div>
            <div className="chat__header-actions">
              {signedIn && (
                <button
                  type="button"
                  className="chat__restart"
                  onClick={() => (view === "conversations" ? setView("chat") : void openConversationList())}
                  aria-pressed={view === "conversations"}
                >
                  Chats
                </button>
              )}
              {showNewChat && (
                <button type="button" className="chat__restart" onClick={startNew}>
                  New chat
                </button>
              )}
            </div>
            <button type="button" className="chat__close" onClick={close} aria-label="Close chat">
              <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </button>
          </header>

          {view === "conversations" ? (
            <div className="chat__convos" aria-label="Your conversations">
              <div className="chat__convos-head">
                <h3 className="chat__convos-title">Your conversations</h3>
                <button type="button" className="button button--primary button--small" onClick={startNew}>
                  + New chat
                </button>
              </div>
              {conversationsError && <p className="chat__convos-empty">{conversationsError}</p>}
              {!conversations && !conversationsError && <p className="chat__convos-empty">Loading…</p>}
              {conversations && conversations.length === 0 && (
                <p className="chat__convos-empty">No saved conversations yet. Messages you send are saved here.</p>
              )}
              {conversations && conversations.length > 5 && (
                <div className="chat__convo-search">
                  <label htmlFor={`${panelId}-convo-search`} className="sr-only">
                    Search your conversations
                  </label>
                  <input
                    id={`${panelId}-convo-search`}
                    type="search"
                    className="input"
                    placeholder="Search your chats (e.g. hoodies, Davenport)"
                    value={conversationFilter}
                    onChange={(e) => setConversationFilter(e.target.value)}
                  />
                </div>
              )}
              {conversations && conversations.length > 0 && (() => {
                const q = conversationFilter.trim().toLowerCase();
                const shown = q
                  ? conversations.filter((c) => [c.title, c.preview, ...c.topics].join(" ").toLowerCase().includes(q))
                  : conversations;
                if (!shown.length) return <p className="chat__convos-empty">No chats match “{conversationFilter}”.</p>;
                const groups = new Map<string, ConversationSummary[]>();
                for (const c of shown) {
                  const g = dateGroup(c.updated_at);
                  groups.set(g, [...(groups.get(g) ?? []), c]);
                }
                return [...groups.entries()].map(([group, items]) => (
                  <section key={group} className="chat__convo-group" aria-label={group}>
                    <h4 className="chat__convo-group-title">{group}</h4>
                    <ul className="chat__convo-list">
                      {items.map((c) => (
                        <li key={c.id}>
                          <button
                            type="button"
                            className="chat__convo"
                            aria-current={c.id === conversationId ? "true" : undefined}
                            onClick={() => openConversation(c.id)}
                          >
                            <span className="chat__convo-title">{c.title}</span>
                            {c.preview && <span className="chat__convo-preview">{c.preview}</span>}
                            <span className="chat__convo-meta">
                              {c.topics.map((t) => (
                                <span key={t} className="chat__convo-topic">
                                  {t}
                                </span>
                              ))}
                              <span>
                                {formatWhen(c.updated_at)} · {c.message_count} messages
                              </span>
                              {c.id === conversationId && <span className="chat__convo-badge">Open</span>}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </section>
                ));
              })()}
              <p className="chat__convos-note">Conversations are saved to your account and never deleted when you start a new chat.</p>
            </div>
          ) : (
            <>
              <div ref={logRef} className="chat__log" role="log" aria-live="polite" aria-label="Conversation" aria-busy={loadingHistory}>
                {signedIn && conversationId !== null && hasMoreSaved && (
                  <button type="button" className="chat__earlier" onClick={showEarlier} disabled={loadingHistory}>
                    {loadingHistory ? "Loading…" : "Show earlier messages"}
                  </button>
                )}
                {/* Idle: sitting Dan welcomes a fresh conversation (not shown once the chat has messages). */}
                {messages.length === 1 && !loadingHistory && !pending && (
                  <div className="chat__intro" aria-hidden="true">
                    <DanMedallion pose="sitting" size={104} />
                  </div>
                )}
                {messages.map((m) =>
                  m.kind === "error" ? (
                    <div key={m.id} className="chat-msg chat-msg--error" role="alert">
                      <div className="chat-msg__bubble">
                        <p>{m.content}</p>
                        {m.retryText && m.id === lastError?.id && (
                          <button type="button" className="chat-msg__retry" onClick={() => retry(m.id, m.retryText!)} disabled={pending}>
                            Try again
                          </button>
                        )}
                      </div>
                    </div>
                  ) : m.kind === "notice" ? (
                    <p key={m.id} className="chat__divider">{m.content}</p>
                  ) : (
                    <div key={m.id} className="chat-turn">
                      <div className={`chat-msg chat-msg--${m.kind}`}>
                        {m.kind === "assistant" && <Avatar />}
                        <div className="chat-msg__bubble">
                          <span className="sr-only">{m.kind === "user" ? "You said: " : `${brand.assistantName} said: `}</span>
                          {m.kind === "assistant" ? <ChatMarkdown text={m.content} /> : m.content}
                        </div>
                      </div>
                      {m.celebrate && m.products && m.products.length > 0 && <DanFoundIt count={m.products.length} />}
                      {m.products && m.products.length > 0 && <ChatProductCards cards={m.products} onOpen={onCardOpen} />}
                    </div>
                  ),
                )}
                {loadingHistory && messages.length <= 1 && <p className="chat__divider">Loading your conversation…</p>}
                {pending && (
                  <div className="chat-msg chat-msg--assistant chat-msg--typing" data-stage={status?.stage ?? "thinking"}>
                    <div className="chat-msg__bubble chat-progress">
                      {/* Dan's activity follows the backend's real progress events (see danModeForStage). */}
                      <DanActivity mode={danModeForStage(status?.stage)} />
                      <span className="chat-progress__body">
                        {/* Status text comes from the backend and only describes steps that are really running. */}
                        <span className="chat-progress__text" role="status">
                          {status?.text ?? "Thinking…"}
                        </span>
                        {waitSeconds >= 8 && (
                          <span className="chat-progress__wait">Still working, thanks for waiting ({waitSeconds}s)</span>
                        )}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <form className="chat__form" onSubmit={send}>
                <label htmlFor={`${panelId}-input`} className="sr-only">
                  Message the shopping assistant
                </label>
                <textarea
                  id={`${panelId}-input`}
                  ref={inputRef}
                  className="chat__input"
                  rows={1}
                  maxLength={MAX_LENGTH}
                  placeholder={
                    pending ? "You can keep typing…" : onProductPage ? "Ask about this product…" : "Ask about styles, gifts or game day…"
                  }
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={onKeyDown}
                />
                <button
                  type="submit"
                  className="chat__send"
                  disabled={!draft.trim() || pending || loadingHistory}
                  aria-label={pending ? "Waiting for the assistant" : "Send message"}
                >
                  <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
                    <path d="M4 12l16-8-6 16-2.5-6.5L4 12z" fill="currentColor" />
                  </svg>
                </button>
              </form>
              <p className="chat__disclaimer">
                {signedIn
                  ? "AI assistant. Chats are saved to your account. Check product pages for current prices and stock."
                  : "AI assistant. Sign in to save your chats. Check product pages for current prices and stock."}
              </p>
            </>
          )}
        </section>
      )}

      <button
        ref={launcherRef}
        type="button"
        className="chat__launcher"
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        onClick={() => (open ? close() : setOpen(true))}
      >
        {open ? (
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
        ) : (
          <Avatar size="sm" />
        )}
        <span className="chat__launcher-label">{open ? "Close chat" : `Ask ${brand.mascotName}`}</span>
      </button>
    </div>
  );
}
