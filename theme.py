import json
import re
from pathlib import Path

THEME_FILE = Path(__file__).parent / "data" / "theme.json"
CUSTOM = "🎨 Tùy chỉnh"
DEFAULT_PRESET = "🌙 Tối"

PRESETS = {
    "🌙 Tối": {"bg": "#0B0F19", "text": "#FFFFFF", "accent": "#4F7CFF"},
    "☀️ Sáng": {"bg": "#F7F9FC", "text": "#172033", "accent": "#4F7CFF"},
    "🌊 Xanh đêm": {"bg": "#0A1F33", "text": "#E6F4FF", "accent": "#38BDF8"},
    "🌿 Rừng xanh": {"bg": "#0F2318", "text": "#EAFBEF", "accent": "#34D399"},
    "☕ Cà phê": {"bg": "#2B2118", "text": "#F5E9DA", "accent": "#D4A373"},
    "🌸 Hồng nhạt": {"bg": "#FFF1F5", "text": "#4A1D2E", "accent": "#EC4899"},
}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(c):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(x))) for x in c)


def mix(a, b, t):
    return _hex(tuple(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))))


def _lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def readable_text(bg):
    return "#FFFFFF" if contrast_ratio(bg, "#FFFFFF") >= contrast_ratio(bg, "#111111") else "#111111"


def default_theme():
    return {"preset": DEFAULT_PRESET, **PRESETS[DEFAULT_PRESET]}


def load_theme():
    try:
        d = json.loads(THEME_FILE.read_text(encoding="utf-8"))
        if all(_HEX.match(str(d.get(k, ""))) for k in ("bg", "text", "accent")):
            preset = d.get("preset") if d.get("preset") in PRESETS else CUSTOM
            return {"preset": preset, "bg": d["bg"], "text": d["text"], "accent": d["accent"]}
    except Exception:
        pass
    return default_theme()


def save_theme(preset, bg, text, accent):
    try:
        THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
        THEME_FILE.write_text(json.dumps({"preset": preset, "bg": bg, "text": text, "accent": accent},
                                         ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


_TEMPLATE = """
:root {
    --bg: __BG__;  --text: __TEXT__;  --accent: __ACCENT__;
    --panel: __PANEL__;  --field: __FIELD__;  --hover: __HOVER__;
    --border: __BORDER__;  --muted: __MUTED__;  --code: __CODE__;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: var(--bg) !important; }
[data-testid="stHeader"] { background: var(--bg) !important; }
[data-testid="stSidebar"] { background: var(--panel) !important; border-right: 1px solid var(--border); }

[data-testid="stBottom"], 
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div {
    background-color: var(--bg) !important;
    background: var(--bg) !important;
}

.stApp, .stApp *, [data-testid="stSidebar"] *,
[data-baseweb="popover"], [data-baseweb="popover"] * { color: var(--text) !important; }
a, a:visited { text-decoration: underline; }
::placeholder { color: var(--muted) !important; opacity: 1 !important; }

input, textarea, [data-baseweb="input"], [data-baseweb="base-input"],
[data-baseweb="select"] > div, [data-testid="stChatInput"], [data-testid="stChatInput"] > div {
    background: var(--field) !important; border-color: var(--border) !important; caret-color: var(--text);
}

.stButton > button, [data-testid="stFormSubmitButton"] > button {
    background: var(--field); border: 1px solid var(--border); border-radius: 10px;
}
.stButton > button:hover { border-color: var(--accent); background: var(--hover); }

[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--border) !important; background: var(--panel); border-radius: 14px; }
[data-testid="stChatMessage"] { background: var(--panel) !important; border: 1px solid var(--border); border-radius: 14px; }
pre, code, [data-testid="stCode"] { background: var(--code) !important; }
hr { border-color: var(--border) !important; }

svg { color: unset !important; }
[data-baseweb="select"] svg { fill: var(--text) !important; color: var(--text) !important; }
[data-baseweb="select"] > div { background-color: var(--field) !important; }

[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"],
.vega-embed,
.vega-embed > div {
    background-color: var(--bg) !important;
    background: var(--bg) !important;
    color-scheme: dark !important;
}

[data-testid="stVegaLiteChart"] iframe,
[data-testid="stArrowVegaLiteChart"] iframe {
    background-color: var(--bg) !important;
    color-scheme: dark !important;
}
"""


def build_css(bg, text, accent):
    panel = mix(bg, text, 0.07)
    values = {
        "__BG__": bg, "__TEXT__": text, "__ACCENT__": accent,
        "__PANEL__": panel,
        "__FIELD__": mix(bg, text, 0.12),
        "__HOVER__": mix(bg, text, 0.19),
        "__BORDER__": mix(bg, text, 0.26),
        "__MUTED__": mix(bg, text, 0.62),
        "__CODE__": mix(bg, text, 0.10),
        "__HERO__": mix(panel, accent, 0.20),
    }
    css = _TEMPLATE
    for k, v in values.items():
        css = css.replace(k, v)
    return css