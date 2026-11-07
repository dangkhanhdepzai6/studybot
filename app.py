"""StudyBot - điểm vào chính."""
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

import database as db
from gemini_client import SYSTEM_PROMPT
from i18n import t
from theme import build_css, default_theme
from ui import chat_page, dashboard_page, login_page, sidebar

_ENV_FILE = Path(__file__).parent / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)

st.set_page_config(page_title="StudyBot", page_icon="🎓", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');

html { color-scheme: dark; }

html, body, .stApp, .stMarkdown, h1, h2, h3, h4, h5, h6,
label, input, textarea, select, button,
[data-testid="stChatInput"] textarea, [data-testid="stSidebar"] p {
    font-family: 'Be Vietnam Pro', 'Segoe UI', Roboto, Arial, sans-serif !important;
}
[data-testid="stIconMaterial"], .material-icons, .material-symbols-rounded {
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}

header {visibility: hidden;}

.stMainBlockContainer {
    padding-top: 0 !important;
    padding-bottom: 1.5rem !important;
}

div[data-testid="stVerticalBlock"] > div:first-child {
    margin-top: 0rem !important;
}

.stButton > button, [data-testid="stFormSubmitButton"] > button {
    border-radius: 12px !important;
    border: 1px solid #2A3654 !important;
    background-color: #151B2B !important;
    color: #E2E8F0 !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
}
.stButton > button:hover {
    background-color: #1E3A8A !important;
    border-color: #3B82F6 !important;
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2) !important;
}
.stButton > button:active {
    transform: translateY(1px) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
}

/* ===== NAVBAR ===== */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.custom-nav-marker) {
    background-color: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 !important;
    padding: 8px 16px !important;
    margin-top: 0 !important;
    margin-bottom: 20px !important;
    margin-left: calc(-50vw + 50%) !important;
    margin-right: calc(-50vw + 50%) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.custom-nav-marker) button {
    background-color: transparent !important;
    color: var(--text) !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    min-width: 130px !important;
    white-space: nowrap !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.custom-nav-marker) button[kind="primary"] {
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--accent) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.custom-nav-marker) button:hover {
    color: var(--text) !important;
    background-color: var(--hover) !important;
}
</style>
""", unsafe_allow_html=True)


def _init_state():
    st.session_state.setdefault("lang", "vi")
    st.session_state.setdefault("username", None)
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("conversation_id", None)
    st.session_state.setdefault("grade_key", "grade_10")
    st.session_state.setdefault("grade", "Lớp 10")
    st.session_state.setdefault("subject_key", "Chung")
    st.session_state.setdefault("subject", "Chung")
    st.session_state.setdefault("tab", "chat")


def _load_default_theme():
    """Luôn dùng theme mặc định. Không đọc DB."""
    d = default_theme()
    st.session_state.preset = d["preset"]
    st.session_state.bg_color = d["bg"]
    st.session_state.text_color = d["text"]
    st.session_state.accent_color = d["accent"]


@st.cache_data(show_spinner=False, max_entries=32)
def _cached_css(bg: str, text: str, accent: str) -> str:
    return build_css(bg, text, accent)


def _system_prompt_builder():
    lang = st.session_state.get("lang", "vi")
    if lang == "vi":
        lang_rule = (
            "NGÔN NGỮ GIAO DIỆN: Tiếng Việt. "
            "LUÔN trả lời bằng tiếng Việt có dấu, bất kể người dùng viết gì."
        )
    else:
        lang_rule = (
            "INTERFACE LANGUAGE: English. "
            "ALWAYS reply in English, regardless of the user's input language."
        )

    grade = st.session_state.get("grade", "Lớp 10")
    subject_vi = st.session_state.get("subject_key", "Chung")

    return (
        SYSTEM_PROMPT
        + f"\n\n{lang_rule}"
        + f"\nHọc sinh đang học: {grade}, môn: {subject_vi}. Điều chỉnh độ khó cho phù hợp."
    )


def _top_nav():
    with st.container(border=True):
        st.markdown('<div class="custom-nav-marker"></div>', unsafe_allow_html=True)
        c1, c2, _ = st.columns([2.5, 2.5, 5])

        with c1:
            if st.button("💬 " + t("tab_chat", st.session_state.lang),
                         use_container_width=True,
                         type="primary" if st.session_state.tab == "chat" else "secondary",
                         key="btn_nav_chat"):
                st.session_state.tab = "chat"
                st.rerun()

        with c2:
            if st.button("📊 " + t("tab_dashboard", st.session_state.lang),
                         use_container_width=True,
                         type="primary" if st.session_state.tab == "dashboard" else "secondary",
                         key="btn_nav_dash"):
                st.session_state.tab = "dashboard"
                st.rerun()


def main():
    db.init_db()
    _init_state()

    user_id = st.session_state.get("user_id")

    if not user_id:
        _load_default_theme()
        css = _cached_css(
            st.session_state.bg_color,
            st.session_state.text_color,
            st.session_state.accent_color,
        )
        st.markdown("""
        <style>
        .stMainBlockContainer { padding-top: 5rem !important; }
        </style>
        """, unsafe_allow_html=True)
        login_page.render(css)
        return

    if "theme_initialized" not in st.session_state:
        _load_default_theme()
        st.session_state.theme_initialized = True

    css = _cached_css(
        st.session_state.bg_color,
        st.session_state.text_color,
        st.session_state.accent_color,
    )

    sidebar.render()
    _top_nav()

    builder = _system_prompt_builder
    if st.session_state.tab == "chat":
        chat_page.render(css, builder)
    else:
        dashboard_page.render(css)


if __name__ == "__main__":
    main()