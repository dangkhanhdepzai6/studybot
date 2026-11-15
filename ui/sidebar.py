import streamlit as st
import database as db
from i18n import t

SUBJECT_OPTIONS = [
    ("Chung", "Chung", "General"),
    ("Toán", "Toán", "Math"),
    ("Vật lý", "Vật lý", "Physics"),
    ("Hóa học", "Hóa học", "Chemistry"),
    ("Sinh học", "Sinh học", "Biology"),
    ("Ngữ văn", "Ngữ văn", "Literature"),
    ("Tiếng Anh", "Tiếng Anh", "English"),
    ("Lịch sử", "Lịch sử", "History"),
    ("Địa lý", "Địa lý", "Geography"),
    ("Tin học", "Tin học", "Informatics"),
]

GRADE_OPTIONS = [
    ("grade_6", "Lớp 6", "Grade 6"),
    ("grade_7", "Lớp 7", "Grade 7"),
    ("grade_8", "Lớp 8", "Grade 8"),
    ("grade_9", "Lớp 9", "Grade 9"),
    ("grade_10", "Lớp 10", "Grade 10"),
    ("grade_11", "Lớp 11", "Grade 11"),
    ("grade_12", "Lớp 12", "Grade 12"),
    ("university", "Đại học", "University"),
]

QUICK_ACTIONS = {
    "solve": {
        "icon": "🧮",
        "prompt": "Hãy đóng vai một gia sư giỏi. Giải chi tiết bài tập sau từng bước một, giải thích rõ công thức và lý do chọn công thức đó: ",
        "en_prompt": "Act as a great tutor. Solve the following exercise step by step, explaining the formulas used: ",
    },
    "explain": {
        "icon": "📖",
        "prompt": "Hãy đóng vai một giáo viên kiên nhẫn. Giải thích chủ đề sau thật dễ hiểu, lấy ví dụ minh họa thực tế: ",
        "en_prompt": "Act as a patient teacher. Explain the following topic simply with real-world examples: ",
    },
    "practice": {
        "icon": "📝",
        "prompt": "Hãy đóng vai người ra đề. Tạo cho tôi 5 câu hỏi luyện tập (từ dễ đến khó) về chủ đề sau. Chưa đưa ra đáp án ngay: ",
        "en_prompt": "Act as an examiner. Create 5 practice questions (easy to hard) about: ",
    },
    "summarize": {
        "icon": "📚",
        "prompt": "Hãy đóng vai chuyên gia tóm tắt. Tóm tắt nội dung sau thành các gạch đầu dòng ngắn gọn, dễ nhớ, giữ lại các ý chính quan trọng nhất: ",
        "en_prompt": "Act as a summarization expert. Summarize the following into concise bullet points: ",
    },
}

_SIDEBAR_CSS = """
<style>
div[data-testid="stSidebar"] .stButton > button {
    background-color: #1A2235 !important;
    border: 1px solid #2A3654 !important;
    border-radius: 12px !important;
    padding: 10px 16px !important;
    text-align: left !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    font-weight: 500 !important;
    color: #E2E8F0 !important;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #1E3A8A !important;
    border-color: #3B82F6 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2) !important;
    color: #FFFFFF !important;
}
div[data-testid="stSidebar"] .stButton > button:active {
    transform: translateY(1px) !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
}
</style>
"""


def _localized_title(title, lang):
    if lang == "vi" and title == "New conversation":
        return "Cuộc trò chuyện mới"
    if lang == "en" and title == "Cuộc trò chuyện mới":
        return "New conversation"
    return title


def _grade_labels(lang):
    return [vi if lang == "vi" else en for _, vi, en in GRADE_OPTIONS]


def _grade_key_to_label(key, lang):
    for k, vi, en in GRADE_OPTIONS:
        if k == key:
            return vi if lang == "vi" else en
    return key


def _grade_label_to_key(label, lang):
    for k, vi, en in GRADE_OPTIONS:
        if (lang == "vi" and label == vi) or (lang == "en" and label == en):
            return k
    return None


def _subject_labels(lang):
    return [vi if lang == "vi" else en for _, vi, en in SUBJECT_OPTIONS]


def _subject_key_to_label(key, lang):
    for k, vi, en in SUBJECT_OPTIONS:
        if k == key:
            return vi if lang == "vi" else en
    return key


def _subject_label_to_key(label, lang):
    for k, vi, en in SUBJECT_OPTIONS:
        if (lang == "vi" and label == vi) or (lang == "en" and label == en):
            return k
    return None


def render():
    lang = st.session_state.get("lang", "vi")

    if "sidebar_css_loaded" not in st.session_state:
        st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
        st.session_state.sidebar_css_loaded = True

    with st.sidebar:
        st.markdown(f"## 🎓 {t('app_name', lang)}")
        st.caption(t("tagline", lang))

        st.markdown(f"**{t('logged_in_as', lang)}**  \n`{st.session_state.username}`")
        if st.button("🚪 " + t("logout", lang), use_container_width=True):
            for k in ("user_id", "username", "conversation_id",
                      "bg_color", "text_color", "accent_color", "preset",
                      "loaded_user_theme_for", "theme_initialized"):
                st.session_state.pop(k, None)
            st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🇻🇳 VI", use_container_width=True, key="btn_vi_real"):
                if lang != "vi":
                    st.session_state.lang = "vi"
                    st.rerun()
        with c2:
            if st.button("🇬🇧 EN", use_container_width=True, key="btn_en_real"):
                if lang != "en":
                    st.session_state.lang = "en"
                    st.rerun()

        st.divider()

        if st.button("➕ " + t("new_chat", lang), use_container_width=True):
            convs = db.list_conversations(st.session_state.user_id)
            empty_conv = None
            for c in convs:
                msgs = db.get_messages(c["id"])
                if not msgs:
                    empty_conv = c["id"]
                    break
            if empty_conv:
                st.session_state.conversation_id = empty_conv
            else:
                st.session_state.conversation_id = db.new_conversation(st.session_state.user_id)
            st.rerun()

        st.markdown(f"### 💬 {t('chat_history', lang)}")
        search = st.text_input("🔍 " + t("search_chats", lang),
                               label_visibility="collapsed", key="chat_search")

        convs = db.list_conversations(st.session_state.user_id, search)
        if not convs:
            st.caption(t("no_chats", lang))
        else:
            for conv in convs:
                active = conv["id"] == st.session_state.get("conversation_id")
                cols = st.columns([5, 1])
                title = _localized_title(conv["title"], lang)
                label = ("🟢 " if active else "▫️ ") + title

                if cols[0].button(label, key=f"conv_{conv['id']}", use_container_width=True):
                    st.session_state.conversation_id = conv["id"]
                    st.rerun()

                if cols[1].button("🗑", key=f"del_{conv['id']}", help="Xóa"):
                    db.delete_conversation(st.session_state.user_id, conv["id"])
                    if st.session_state.get("conversation_id") == conv["id"]:
                        st.session_state.conversation_id = None
                    st.rerun()

        st.divider()

        grade_labels = _grade_labels(lang)
        current_key = st.session_state.get("grade_key", "grade_10")
        current_label = _grade_key_to_label(current_key, lang)
        try:
            current_idx = grade_labels.index(current_label)
        except ValueError:
            current_idx = 4

        chosen_label = st.selectbox(
            t("class", lang), grade_labels, index=current_idx, key="sb_grade"
        )
        chosen_key = _grade_label_to_key(chosen_label, lang)
        if chosen_key:
            st.session_state.grade_key = chosen_key
            st.session_state.grade = _grade_key_to_label(chosen_key, lang)

        subject_labels = _subject_labels(lang)
        current_subj_key = st.session_state.get("subject_key", "Chung")
        current_subj_label = _subject_key_to_label(current_subj_key, lang)
        try:
            subj_idx = subject_labels.index(current_subj_label)
        except ValueError:
            subj_idx = 0

        chosen_subj_label = st.selectbox(
            t("subject", lang), subject_labels, index=subj_idx, key="sb_subject"
        )
        chosen_subj_key = _subject_label_to_key(chosen_subj_label, lang)
        if chosen_subj_key:
            st.session_state.subject_key = chosen_subj_key
            st.session_state.subject = chosen_subj_key  # giữ tương thích code cũ

        st.divider()

        st.markdown(f"### 🚀 {t('quick_actions', lang)}")
        for key, data in QUICK_ACTIONS.items():
            label = f"{data['icon']} {t(key, lang)}"
            if st.button(label, use_container_width=True):
                st.session_state.conversation_id = db.new_conversation(
                    st.session_state.user_id,
                    title=t(key, lang),
                )
                st.session_state.pending_action = key
                st.session_state.pending_prompt = data["prompt"] if lang == "vi" else data["en_prompt"]
                st.session_state.tab = "chat"
                st.rerun()