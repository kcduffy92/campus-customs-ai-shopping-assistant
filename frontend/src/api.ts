import type {
  CatalogueFilters,
  ChatHistory,
  ChatRequest,
  ConversationSummary,
  ChatResponse,
  LoginInput,
  ProductDetail,
  ProductList,
  RegisterInput,
  SortOption,
  User,
} from "./types";

export class ApiError extends Error {
  status: number;
  /** Per-field messages from the backend, e.g. { email: "This email is already registered." } */
  fields: Record<string, string>;
  constructor(status: number, message: string, fields: Record<string, string> = {}) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      credentials: "same-origin", // send the HttpOnly session cookie
      ...init,
      headers: { Accept: "application/json", ...(init.body ? { "Content-Type": "application/json" } : {}), ...init.headers },
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError(0, "We couldn't reach the store. Please check your connection and try again.");
  }
  if (!res.ok) throw await errorFrom(res);
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** Turn a failed response into an ApiError with the backend's plain-English message (if it sent one). */
async function errorFrom(res: Response): Promise<ApiError> {
  let detail = res.status >= 500 ? "Something went wrong on our end. Please try again." : "Something went wrong. Please try again.";
  let fields: Record<string, string> = {};
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") detail = body.detail;
    if (body?.fields && typeof body.fields === "object") fields = body.fields;
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(res.status, detail, fields);
}

const getJson = <T,>(path: string, signal?: AbortSignal) => request<T>(path, { signal });
const postJson = <T,>(path: string, body?: unknown, signal?: AbortSignal) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body), signal });

// ---------- Shopping assistant ----------

export const sendChat = (input: ChatRequest, signal?: AbortSignal) => postJson<ChatResponse>("/api/chat", input, signal);

/** What the assistant is doing right now, reported by the backend only when it actually happens. */
export interface ChatStatus {
  stage: "thinking" | "searching" | "inventory" | "reviewing";
  text: string;
}

/**
 * Like sendChat, but reads the streamed progress from /api/chat/stream (one JSON object per line) and reports each
 * status as it arrives. Resolves with the same ChatResponse; errors become ApiError like the rest of the API.
 */
export async function sendChatStream(
  input: ChatRequest,
  onStatus: (status: ChatStatus) => void,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  let res: Response;
  try {
    res = await fetch("/api/chat/stream", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/x-ndjson" },
      body: JSON.stringify(input),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError(0, "We couldn't reach the store. Please check your connection and try again.");
  }
  if (!res.ok) throw await errorFrom(res);
  if (!res.body) throw new ApiError(0, "We couldn't reach the store. Please check your connection and try again.");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    let newline: number;
    while ((newline = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (!line) continue;
      const event = JSON.parse(line);
      if (event.type === "status") onStatus({ stage: event.stage, text: event.text });
      else if (event.type === "result") return event.data as ChatResponse;
      else if (event.type === "error") throw new ApiError(event.status ?? 503, event.detail ?? "Something went wrong.");
    }
    if (done) break;
  }
  throw new ApiError(502, "The connection to our shopping assistant was interrupted. Please try again.");
}

/**
 * A page of one of the signed-in customer's own conversations (identity comes from the session cookie, never a
 * parameter). Without a conversation id, the backend returns the most recently active conversation.
 */
export function fetchChatHistory(options: { conversationId?: number | null; beforeId?: number } = {}, signal?: AbortSignal) {
  const qs = new URLSearchParams({ limit: "30" });
  if (options.conversationId) qs.set("conversation_id", String(options.conversationId));
  if (options.beforeId) qs.set("before_id", String(options.beforeId));
  return getJson<ChatHistory>(`/api/chat/history?${qs}`, signal);
}

export const fetchConversations = (signal?: AbortSignal) =>
  getJson<{ conversations: ConversationSummary[] }>("/api/chat/conversations", signal);

// ---------- Accounts ----------

export const fetchCurrentUser = (signal?: AbortSignal) => getJson<User | null>("/api/auth/me", signal);
export const login = (input: LoginInput) => postJson<User>("/api/auth/login", input);
export const register = (input: RegisterInput) => postJson<User>("/api/auth/register", input);
export const logout = () => postJson<void>("/api/auth/logout");

export interface ProductQuery {
  category?: string;
  color?: string;
  q?: string;
  inStock?: boolean;
  sort?: SortOption;
}

export function fetchProducts(query: ProductQuery = {}, signal?: AbortSignal) {
  const params = new URLSearchParams();
  if (query.category) params.set("category", query.category);
  if (query.color) params.set("color", query.color);
  if (query.q) params.set("q", query.q);
  if (query.inStock) params.set("in_stock", "true");
  if (query.sort && query.sort !== "name") params.set("sort", query.sort);
  const qs = params.toString();
  return getJson<ProductList>(`/api/products${qs ? `?${qs}` : ""}`, signal);
}

export function fetchProduct(productId: string, signal?: AbortSignal) {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`, signal);
}

export function fetchFilters(signal?: AbortSignal) {
  return getJson<CatalogueFilters>("/api/filters", signal);
}
