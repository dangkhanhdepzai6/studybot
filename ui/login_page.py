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

    st.markdown("""
    <style>
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

    div[data-testid="stForm"] {
        background: rgba(26, 34, 53, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(79, 124, 255, 0.3) !important;
        border-radius: 20px !important;
        padding: 30px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4) !important;
    }
    
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

    _, center, _ = st.columns([1, 1.5, 1])
    
    with center:
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

        c1, c2 = st.columns(2)
        if c1.button("🌐 Tiếng Việt", key="lang_vi", use_container_width=True):
            st.session_state.lang = "vi"
            st.rerun()
        if c2.button("🌐 English", key="lang_en", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()

        st.write("")

        mode = st.radio(
            "mode",
            [t("login", lang), t("register", lang)],
            horizontal=True,
            label_visibility="collapsed",
        )

        with st.form("auth_form"):
            username = st.text_input(t("username", lang))
            password = st.text_input(t("password", lang), type="password")
            
            confirm = ""
            if mode == t("register", lang):
                confirm = st.text_input(t("confirm_password", lang), type="password")
                if password:
                    score, missing = auth.password_strength(password)
                    pct = int(score / 5 * 100)

                    if score <= 2:
                        bar_color = "#EF4444"  # đỏ
                        strength_text = "Yếu" if lang == "vi" else "Weak"
                    elif score == 3:
                        bar_color = "#F59E0B"  # vàng
                        strength_text = "Trung bình" if lang == "vi" else "Medium"
                    elif score == 4:
                        bar_color = "#3B82F6"  # xanh dương
                        strength_text = "Khá" if lang == "vi" else "Good"
                    else:
                        bar_color = "#10B981"  # xanh lá
                        strength_text = "Mạnh" if lang == "vi" else "Strong"

                    st.markdown(
                        f"""
                        <div style="margin-top: 6px; margin-bottom: 4px; display:flex; align-items:center; gap:8px;">
                            <div style="flex:1; height:8px; background:rgba(148,163,184,0.2); border-radius:4px; overflow:hidden;">
                                <div style="width:{pct}%; height:100%; background:{bar_color}; transition: width 0.3s ease;"></div>
                            </div>
                            <span style="font-size:13px; color:{bar_color}; font-weight:600; white-space:nowrap;">{strength_text}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if missing:
                        st.caption("⚠️ " + _criteria_text(missing, lang))
                    else:
                        st.caption("✅ Mật khẩu mạnh" if lang == "vi" else "✅ Strong password")

                    st.markdown(
                        f"""
                        <div style="font-size:12px; color:#94A3B8; margin-top:2px; line-height:1.5;">
                            {'Yêu cầu: ít nhất 8 ký tự, gồm chữ hoa, chữ thường, chữ số và ký tự đặc biệt.'
                             if lang == 'vi'
                             else 'Requirement: at least 8 characters, including uppercase, lowercase, digit and special character.'}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

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