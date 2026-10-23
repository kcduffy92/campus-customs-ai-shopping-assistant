"""Recognize pure small talk ("hi", "thanks!", "ok great, bye") so the assistant doesn't search the catalogue for it.

Deliberately conservative: a message counts as small talk only if EVERY word is a greeting/thanks/acknowledgement/
goodbye word (plus punctuation and emoji) and it's short. Anything else, including any product, size, price or
question word, is not small talk, so the agent keeps full access to its database tools. A false "no" only costs a
little time; a false "yes" could cost accuracy, so the list stays narrow.

Used by agent.py (hide the tools for small talk) and chat_history.py (skip small talk when titling conversations).
"""

from __future__ import annotations

import re

_SMALL_TALK_WORDS = {
    # greetings
    "hi", "hii", "hiya", "hello", "hey", "heya", "howdy", "yo", "greetings", "good", "morning", "afternoon", "evening",
    "there", "everyone", "all",
    # thanks
    "thanks", "thank", "you", "thx", "ty", "tysm", "much", "so", "very", "appreciate", "it", "appreciated", "cheers",
    # acknowledgements (only count together with a greeting/thanks/goodbye word; see _ANCHORS)
    "ok", "okay", "cool", "great", "awesome", "perfect", "nice", "got", "gotcha", "alright", "that", "that's",
    "thats", "helpful", "helps", "amazing", "wonderful", "lovely", "excellent", "fantastic", "understood", "a", "lot",
    "the", "help", "for", "your", "is", "was", "really", "just", "oh", "ah", "wow", "haha", "lol",
    # goodbyes
    "bye", "goodbye", "later", "see", "ya", "cya", "talk", "soon", "have", "day", "night", "take", "care",
}
# A message must contain at least one of these. Agreement words alone ("yes", "sure", "ok", "sounds good") are NOT
# small talk: they often answer the assistant's own offer ("Want me to check medium?" -> "yes") and need the tools.
_ANCHORS = {
    "hi", "hii", "hiya", "hello", "hey", "heya", "howdy", "greetings", "morning", "afternoon", "evening",
    "thanks", "thank", "thx", "ty", "tysm", "appreciate", "appreciated", "cheers",
    "bye", "goodbye", "later", "cya", "care",
}
_MAX_WORDS = 10
_WORD_RE = re.compile(r"[a-z']+")


def is_small_talk(message: str) -> bool:
    """True only for short messages made entirely of greeting/thanks/acknowledgement/goodbye words."""
    text = (message or "").strip().lower()
    if not text or "?" in text or any(ch.isdigit() for ch in text):
        return False
    words = _WORD_RE.findall(text.replace("’", "'"))
    if not words or len(words) > _MAX_WORDS:
        return False
    # Anything left after removing the words, punctuation, whitespace and emoji means real content.
    leftovers = _WORD_RE.sub("", text.replace("’", "'"))
    if re.search(r"[a-z0-9$#@%&*+=/\\<>\[\]{}|~^]", leftovers):
        return False
    return all(w in _SMALL_TALK_WORDS for w in words) and any(w in _ANCHORS for w in words)
