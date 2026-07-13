"""
Short-term memory management.

The chat keeps the running conversation as a list of simple {role, content}
messages. Full coverage of the whole history is not required, so when the
conversation grows past a threshold we summarize the oldest messages into a
single running summary and keep only the most recent turns verbatim. This mirrors
the "manage short-term memory" idea from LangGraph: trim old messages so we never
overflow the context window, while preserving the gist in a summary.
"""

from config import MODEL, client

MAX_HISTORY_MESSAGES = 12   # summarize once history grows beyond this
KEEP_RECENT = 6             # number of recent messages kept verbatim


def _summarize(older_messages, previous_summary):
    """Compress older messages (and any prior summary) into one paragraph."""
    convo = ""
    if previous_summary:
        convo += f"Summary so far: {previous_summary}\n\n"
    for m in older_messages:
        convo += f"{m['role'].capitalize()}: {m['content']}\n"

    resp = client.responses.create(
        model=MODEL,
        instructions=(
            "Summarize the following conversation between a user and a travel "
            "assistant into a short paragraph. Keep the user's preferences, "
            "destinations discussed, and any decisions. Be concise."
        ),
        input=[{"role": "user", "content": convo}],
        max_output_tokens=250,
        temperature=0.3,
    )
    return resp.output_text.strip()


def manage_memory(history, summary):
    """Return (trimmed_history, updated_summary).

    If the history is short, nothing changes. Otherwise the oldest messages are
    folded into `summary` and only the last KEEP_RECENT messages are kept.
    """
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history, summary

    older = history[:-KEEP_RECENT]
    recent = history[-KEEP_RECENT:]
    new_summary = _summarize(older, summary)
    return recent, new_summary