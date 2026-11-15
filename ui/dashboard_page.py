"""Dashboard: thẻ thống kê + biểu đồ + cài đặt giao diện."""
import time
import streamlit as st
import pandas as pd
import altair as alt
import database as db
from i18n import t
from theme import CUSTOM, PRESETS, build_css, contrast_ratio, readable_text, save_theme, default_theme

CHART_LABELS = {
    "vi": {
        "subject": "Môn học", "count": "Số câu", "date": "Ngày",
        "feature": "Chức năng", "usage": "Số lần dùng",
        "feature_map": {"question": "Hỏi đáp", "solve": "Giải bài",
                        "explain": "Giải thích", "practice": "Luyện tập",
                        "summarize": "Tóm tắt"},
        "subject_map": {"Chung": "Chung", "Toán": "Toán", "Vật lý": "Vật lý",
                        "Hóa học": "Hóa học", "Sinh học": "Sinh học",
                        "Ngữ văn": "Ngữ văn", "Tiếng Anh": "Tiếng Anh",
                        "Lịch sử": "Lịch sử", "Địa lý": "Địa lý",
                        "Tin học": "Tin học"},
    },
    "en": {
        "subject": "Subject", "count": "Count", "date": "Date",
        "feature": "Feature", "usage": "Usage count",
        "feature_map": {"question": "Q&A", "solve": "Solve",
                        "explain": "Explain", "practice": "Practice",
                        "summarize": "Summarize"},
        "subject_map": {"Chung": "General", "Toán": "Math", "Vật lý": "Physics",
                        "Hóa học": "Chemistry", "Sinh học": "Biology",
                        "Ngữ văn": "Literature", "Tiếng Anh": "English",
                        "Lịch sử": "History", "Địa lý": "Geography",
                        "Tin học": "Informatics"},
    },
}

PRESET_I18N_KEYS = {
    "🌙 Tối": "preset_dark",
    "☀️ Sáng": "preset_light",
    "🌊 Xanh đêm": "preset_ocean",
    "🌿 Rừng xanh": "preset_forest",
    "☕ Cà phê": "preset_coffee",
    "🌸 Hồng nhạt": "preset_pink",
    CUSTOM: "preset_custom",
}


def _chart_labels(lang):
    return CHART_LABELS.get(lang, CHART_LABELS["vi"])


def _render_bar_chart(df, x_col, y_col, color, title_x, title_y):
    chart = alt.Chart(df).mark_bar(
        color=color,
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        size=40,
    ).encode(
        x=alt.X(
            f"{x_col}:N",
            sort="-y",
            axis=alt.Axis(
                labelAngle=-30,
                title=title_x,
                labelFontSize=11,
                titleFontSize=12,
                grid=False,
            ),
        ),
        y=alt.Y(
            f"{y_col}:Q",
            axis=alt.Axis(
                title=title_y,
                labelFontSize=11,
                titleFontSize=12,
                gridColor="rgba(148,163,184,0.1)",
                tickCount=5,
            ),
        ),
        tooltip=[x_col, y_col],
    ).properties(height=280)
    return chart


def _render_line_chart(df, x_col, y_col, color, title_x, title_y):
    """Biểu đồ đường gọn: nét mảnh, điểm nhỏ."""
    chart = alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(color=color, size=40, filled=True),
        color=color,
        strokeWidth=2,
    ).encode(
        x=alt.X(
            f"{x_col}:T",
            axis=alt.Axis(
                format="%d/%m",
                title=title_x,
                labelFontSize=11,
                titleFontSize=12,
                grid=False,
            ),
        ),
        y=alt.Y(
            f"{y_col}:Q",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                title=title_y,
                labelFontSize=11,
                titleFontSize=12,
                gridColor="rgba(148,163,184,0.1)",
                tickCount=5,
            ),
        ),
        tooltip=[x_col, y_col],
    ).properties(height=280)
    return chart


def render(theme_css: str):
    lang = st.session_state.get("lang", "vi")
    labels = _chart_labels(lang)

    st.markdown(f"## 📊 {t('dashboard_title', lang)}")
    st.caption(t("dashboard_sub", lang))

    f1, f2 = st.columns(2)
    time_filter = f1.selectbox(
        t("filter_time", lang),
        [t("time_all", lang), t("time_7d", lang), t("time_30d", lang)],
        key="dash_time_filter",
    )
    since = None
    if time_filter == t("time_7d", lang):
        since = time.time() - 7 * 86400
    elif time_filter == t("time_30d", lang):
        since = time.time() - 30 * 86400

    stats = db.usage_stats(st.session_state.user_id, since_ts=since)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("stat_questions", lang), stats["total_questions"])
    c2.metric(t("stat_conversations", lang), stats["total_conversations"])
    c3.metric(t("stat_subjects", lang), len(stats["by_subject"]))
    c4.metric(t("stat_active_days", lang), len(stats["by_day"]))

    st.divider()

    accent = st.session_state.get("accent_color", "#4F7CFF")
    green = "#10B981"

    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"#### {t('chart_by_subject', lang)}")
        if stats["by_subject"]:
            df_sub = pd.DataFrame(stats["by_subject"])
            df_sub.columns = [labels["subject"], labels["count"]]
            df_sub[labels["subject"]] = df_sub[labels["subject"]].map(
                lambda s: labels["subject_map"].get(s, s)
            )
            chart1 = _render_bar_chart(
                df_sub, labels["subject"], labels["count"],
                accent, labels["subject"], labels["count"]
            )
            st.altair_chart(chart1, use_container_width=True)
        else:
            st.info(t("no_data", lang))

    with g2:
        st.markdown(f"#### {t('chart_by_day', lang)}")
        if stats["by_day"]:
            df_day = pd.DataFrame(stats["by_day"])
            df_day.columns = [labels["date"], labels["count"]]
            df_day[labels["date"]] = pd.to_datetime(df_day[labels["date"]])
            chart2 = _render_line_chart(
                df_day, labels["date"], labels["count"],
                accent, labels["date"], labels["count"]
            )
            st.altair_chart(chart2, use_container_width=True)
        else:
            st.info(t("no_data", lang))

    st.markdown(f"#### {t('chart_by_feature', lang)}")
    if stats["by_feature"]:
        df_feat = pd.DataFrame(stats["by_feature"])
        df_feat.columns = [labels["feature"], labels["usage"]]
        df_feat[labels["feature"]] = df_feat[labels["feature"]].map(
            lambda f: labels["feature_map"].get(f, f)
        )
        chart3 = _render_bar_chart(
            df_feat, labels["feature"], labels["usage"],
            green, labels["feature"], labels["usage"]
        )
        st.altair_chart(chart3, use_container_width=True)
    else:
        st.info(t("no_data", lang))

    st.divider()
    st.markdown(f"### 🎨 {t('settings', lang)}")

    def _apply():
        save_theme(st.session_state.preset, st.session_state.bg_color,
                   st.session_state.text_color, st.session_state.accent_color)

    def _on_bg_change():
        st.session_state.bg_color = st.session_state["_dash_bg_sel"]
        st.session_state.preset = CUSTOM
        _apply()

    def _on_text_change():
        st.session_state.text_color = st.session_state["_dash_text_sel"]
        st.session_state.preset = CUSTOM
        _apply()

    def _on_accent_change():
        st.session_state.accent_color = st.session_state["_dash_accent_sel"]
        st.session_state.preset = CUSTOM
        _apply()

    def _on_auto_text():
        st.session_state.text_color = readable_text(st.session_state.bg_color)
        _apply()

    def _on_reset():
        d = default_theme()
        st.session_state.preset = d["preset"]
        st.session_state.bg_color = d["bg"]
        st.session_state.text_color = d["text"]
        st.session_state.accent_color = d["accent"]
        _apply()

    preset_keys = list(PRESETS) + [CUSTOM]
    display_labels = [t(PRESET_I18N_KEYS[k], lang) for k in preset_keys]

    current_key = st.session_state.get("preset", "🌙 Tối")
    if current_key not in preset_keys:
        current_key = "🌙 Tối"
    current_display = t(PRESET_I18N_KEYS[current_key], lang)
    try:
        current_idx = display_labels.index(current_display)
    except ValueError:
        current_idx = 0

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    chosen_label = col1.selectbox(
        t("theme_preset", lang),
        display_labels,
        index=current_idx,
        key="_dash_preset_sel",
    )

    chosen_key = None
    for k in preset_keys:
        if t(PRESET_I18N_KEYS[k], lang) == chosen_label:
            chosen_key = k
            break
    if chosen_key and chosen_key != st.session_state.preset:
        st.session_state.preset = chosen_key
        p = PRESETS.get(chosen_key)
        if p:
            st.session_state.bg_color = p["bg"]
            st.session_state.text_color = p["text"]
            st.session_state.accent_color = p["accent"]
            _apply()
        elif chosen_key == CUSTOM:
            _apply()

    col2.color_picker(
        t("bg_color", lang),
        value=st.session_state.bg_color,
        key="_dash_bg_sel",
        on_change=_on_bg_change,
    )
    col3.color_picker(
        t("text_color", lang),
        value=st.session_state.text_color,
        key="_dash_text_sel",
        on_change=_on_text_change,
    )
    col4.color_picker(
        t("accent_color", lang),
        value=st.session_state.accent_color,
        key="_dash_accent_sel",
        on_change=_on_accent_change,
    )

    u1, u2, u3 = st.columns([1, 1, 3])
    u1.button("🪄 " + t("auto_text", lang), on_click=_on_auto_text)
    u2.button("↩️ " + t("reset_theme", lang), on_click=_on_reset)

    ratio = contrast_ratio(st.session_state.bg_color, st.session_state.text_color)
    if ratio < 3:
        u3.warning("Màu chữ và nền quá gần nhau, khó đọc.")
    elif ratio < 4.5:
        u3.caption(f"Độ tương phản {ratio:.1f}:1, hơi thấp.")

    fresh_css = build_css(
        st.session_state.bg_color,
        st.session_state.text_color,
        st.session_state.accent_color,
    )
    st.markdown(f"<style>{fresh_css}</style>", unsafe_allow_html=True)