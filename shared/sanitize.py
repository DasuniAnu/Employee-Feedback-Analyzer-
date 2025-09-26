import re

SCRIPT_TAG = re.compile(r"<\\s*script[^>]*>(.*?)<\\s*/\\s*script>", re.IGNORECASE | re.DOTALL)
JS_URL = re.compile(r"javascript:\\S+", re.IGNORECASE)
SQL_INJECTION = re.compile(r"(;|--)|(/\\*)|(\\*/)|\\x00|\\x1a")


def sanitize_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = SCRIPT_TAG.sub("", s)
    s = JS_URL.sub("", s)
    s = SQL_INJECTION.sub("", s)
    return s.strip()
