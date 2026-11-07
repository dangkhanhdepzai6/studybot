"""Trang đăng nhập / đăng ký."""
import streamlit as st
import auth
from i18n import t


def _criteria_text(missing, lang):
    if not missing:
        return ""
    parts = [t(f"crit_{m}", lang) for m in missing]
    return t("weak_password", lang) + " " + ", ".join(parts)


def render(theme_css: str):
    st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)
    lang = st.session_state.get("lang", "vi")

    # ==========================================
    # ĐƯA TOÀN BỘ CSS LÊN ĐẦU TRANG (TRÁNH BỊ STREAMLIT NUỐT)
    # ==========================================
    st.markdown("""
    <style>
    /* 1. BANNER ĐĂNG NHẬP */
    .login-banner-wrapper {
        background: linear-gradient(135deg, #1A2235 0%, #253052 100%);
        border: 1px solid #3B4B6B;
        border-radius: 24px;
        padding: 40px 30px;
        text-align: center;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
    }
    .login-banner-wrapper::before {
        content: "";
        position: absolute;
        top: -50%;
        left: 50%;
        transform: translateX(-50%);
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(79, 124, 255, 0.15) 0%, transparent 70%);
        z-index: 0;
    }
    .login-banner-wrapper h1 {
        margin: 0 0 10px 0;
        font-size: 38px;
        font-weight: 800;
        background: linear-gradient(90deg, #FFFFFF, #A0C0FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        position: relative;
        z-index: 1;
    }
    .login-banner-wrapper p {
        color: #94A3B8;
        font-size: 16px;
        margin-bottom: 20px;
        position: relative;
        z-index: 1;
    }
    .login-icon-float {
        font-size: 70px;
        line-height: 1;
        position: relative;
        z-index: 1;
        animation: floatIcon 3s ease-in-out infinite;
    }
    @keyframes floatIcon {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    /* 2. KHUNG FORM KÍNH MỜ */
    div[data-testid="stForm"] {
        background: rgba(26, 34, 53, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(79, 124, 255, 0.3) !important;
        border-radius: 20px !important;
        padding: 30px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* 3. NÚT ĐĂNG NHẬP GRADIENT */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #4F7CFF, #3B82F6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(79, 124, 255, 0.4) !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(79, 124, 255, 0.6) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # CĂN GIỮA VÀ VẼ GIAO DIỆN
    # ==========================================
    _, center, _ = st.columns([1, 1.5, 1])
    
    with center:
        # Vẽ Banner bằng class CSS (không dùng inline style)
        st.markdown(
            f"""
            <div class="login-banner-wrapper">
                <h1>🎓 {t("app_name", lang)}</h1>
                <p>{t("login_subtitle", lang)}</p>
                <div class="login-icon-float">📘✨</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Chuyển đổi ngôn ngữ
        c1, c2 = st.columns(2)
        if c1.button("🌐 Tiếng Việt", key="lang_vi", use_container_width=True):
            st.session_state.lang = "vi"
            st.rerun()
        if c2.button("🌐 English", key="lang_en", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()

        st.write("")

        # Chọn chế độ Đăng nhập / Đăng ký
        mode = st.radio(
            "mode",
            [t("login", lang), t("register", lang)],
            horizontal=True,
            label_visibility="collapsed",
        )

        # Form đăng nhập/đăng ký
        with st.form("auth_form"):
            username = st.text_input(t("username", lang))
            password = st.text_input(t("password", lang), type="password")
            
            confirm = ""
            if mode == t("register", lang):
                confirm = st.text_input(t("confirm_password", lang), type="password")
                if password:
                    score, missing = auth.password_strength(password)
                    st.progress(score / 6)
                    if missing:
                        st.caption("⚠️ " + _criteria_text(missing, lang))
                    else:
                        st.caption("✅ Mật khẩu mạnh" if lang == "vi" else "✅ Strong password")

            submit = st.form_submit_button(
                t("login_btn", lang) if mode == t("login", lang) else t("register_btn", lang),
                use_container_width=True,
            )

        if submit:
            if mode == t("login", lang):
                ok, info = auth.login(username, password)
                if ok:
                    st.session_state.user_id = int(info)
                    st.session_state.username = username
                    st.success(t("login_success", lang))
                    st.rerun()
                else:
                    if info.startswith("locked:"):
                        mins = info.split(":")[1]
                        st.error(f"🔒 Tài khoản đang bị khóa. Thử lại sau {mins} phút.")
                    else:
                        st.error(t("login_fail", lang))
            else:
                ok, info = auth.register(username, password, confirm)
                if ok:
                    st.success(t("register_success", lang))
                else:
                    if info.startswith("weak_password:"):
                        missing = info.split(":", 1)[1].split(",")
                        st.error(_criteria_text(missing, lang))
                    else:
                        st.error(t(info, lang))