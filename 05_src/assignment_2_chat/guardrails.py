# Include guardrails

import re

# Identify keywords for each of the restricted topics

_CATS_DOGS = re.compile(
    r"\b(cats?|kittens?|dogs?|puppy|puppies)\b", re.I
)

_HOROSCOPE = re.compile(
    r"\b(horoscopes?|zodiac|astrolog\w*|capricorn|aquarius|pisces|aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius)\b", re.I,
)

_TAYLOR_SWIFT = re.compile(r"\b(taylor\s*swift|t-?swift)\b", re.I)

# System prompt attacks
# --- System-prompt attacks -------------------------------------------------
_PROMPT_NOUNS = (
    r"(system\s*prompt|"
    r"system\s*message|"
    r"system\s+instruction\w*|"
    r"developer\s*message|"
    r"developer\s+instruction\w*|"
    r"developer\s+prompt|"
    r"hidden\s+(prompt|instruction|message|rule\w*)|"
    r"initial\s+prompt|"
    r"original\s+prompt|"
    r"base\s+prompt|"
    r"underlying\s+prompt|"
    r"secret\s+(prompt|instruction|message|rule\w*)|"
    r"internal\s+(prompt|instruction|message|rule\w*)|"
    r"private\s+(prompt|instruction|message|rule\w*)|"
    r"the\s+prompt|"
    r"your\s+prompt|"
    r"your\s+instruction\w*|"
    r"your\s+rule\w*|"
    r"your\s+constraint\w*|"
    r"your\s+policy\w*|"
    r"your\s+guardrail\w*|"
    r"configuration\s+prompt)"
)

_PROMPT_VERBS = (
    r"(reveal|"
    r"show|"
    r"display|"
    r"print|"
    r"output|"
    r"provide|"
    r"share|"
    r"tell|"
    r"give|"
    r"list|"
    r"copy|"
    r"repeat|"
    r"recite|"
    r"quote|"
    r"extract|"
    r"expose|"
    r"leak|"
    r"dump|"
    r"retrieve|"
    r"recover|"
    r"access|"
    r"find|"
    r"locate|"
    r"ignore|"
    r"disregard|"
    r"forget|"
    r"drop|"
    r"remove|"
    r"disable|"
    r"turn\s+off|"
    r"override|"
    r"overwrite|"
    r"bypass|"
    r"circumvent|"
    r"modify|"
    r"change|"
    r"edit|"
    r"rewrite|"
    r"replace|"
    r"update|"
    r"reset|"
    r"delete)"
)

_PROMPT_ATTACK = re.compile(
    rf"{_PROMPT_VERBS}[\w\s,'\"-]*{_PROMPT_NOUNS}|" #requests to reveal prompt
    rf"{_PROMPT_NOUNS}[\w\s,'\"-]*{_PROMPT_VERBS}|" #prompt noun followed by request/action
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts?)|" #attempts to override previous instructions
    r"repeat\s+(the\s+)?(words|text|everything)\s+above|" #attempts to extract previous context
    r"what\s+(were|are)\s+you\s+(told|instructed)", #attempts to discover hidden instructions indirectly
    re.I,
)

_REFUSAL_TOPIC = (
    "Sorry, I focus on helping identify and compare livable cities. "
    "I do not chat about cats, dogs, horoscopes, or Taylor Swift. "
    "However, I can help with topics like quality of life, safety, healthcare, "
    "cost of living, climate, and other city features. "
    "Ask me about a city or what makes a destination a great place to live!"
)
_REFUSAL_PROMPT = (
    "My internal instructions stay private, but I can help you discover "
    "great places to live. Ask me about livability rankings, city features, "
    "or comparisons between destinations!"
)


def check_input(text: str):
    """Return a refusal string if the message must be blocked, else None."""
    if _PROMPT_ATTACK.search(text):
        return _REFUSAL_PROMPT
    if _CATS_DOGS.search(text) or _HOROSCOPE.search(text) or _TAYLOR_SWIFT.search(text):
        return _REFUSAL_TOPIC
    return None