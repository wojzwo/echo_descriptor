# echo_desc/reports/templating.py
from __future__ import annotations
from typing import Dict, Any
import re

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)(?::([^}]+))?\}")

class TemplateRenderer:
    """
    - supports {KEY} and {KEY:format}
    - missing => ###BRAK PARAMETRU:KEY###
    """
    def __init__(self, missing_prefix: str = "###BRAK PARAMETRU:", missing_suffix: str = "###"):
        self.missing_prefix = missing_prefix
        self.missing_suffix = missing_suffix

    def render(self, text: str, ctx: Dict[str, Any]) -> str:
        def repl(m: re.Match) -> str:
            key = m.group(1)
            fmt = m.group(2)
            if key not in ctx or ctx[key] is None:
                return f"{self.missing_prefix}{key}{self.missing_suffix}"
            val = ctx[key]
            if fmt:
                try:
                    return format(val, fmt)
                except Exception:
                    return str(val)
            return str(val)

        return _PLACEHOLDER_RE.sub(repl, text)
