/**
 * Lets any page open the shopping assistant (Problem 10). An optional draft is placed in the message box for the
 * shopper to edit or send; nothing is ever sent automatically.
 */
const OPEN_CHAT = "cc:open-chat";

export function openChat(draft?: string) {
  window.dispatchEvent(new CustomEvent<{ draft?: string }>(OPEN_CHAT, { detail: { draft } }));
}

export function onOpenChat(handler: (draft?: string) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent<{ draft?: string }>).detail?.draft);
  window.addEventListener(OPEN_CHAT, listener);
  return () => window.removeEventListener(OPEN_CHAT, listener);
}
