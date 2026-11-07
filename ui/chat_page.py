"""Trang chatbot: hero, 4 card, gợi ý câu hỏi, khung chat."""
import random
import os
import streamlit as st
import database as db
from gemini_client import SYSTEM_PROMPT, stream_chat
from i18n import t

SUGGESTIONS = {
    "vi": {
        "Toán": ["Giải phương trình x² - 5x + 6 = 0", "Đạo hàm của sin(x) là gì?", "Cách tính diện tích hình tròn?", "Phân biệt chỉnh hợp và tổ hợp?"],
        "Vật lý": ["Định luật Newton thứ 2 phát biểu thế nào?", "Động năng và thế năng khác nhau ra sao?", "Công thức tính điện trở tương đương?", "Hiện tượng cảm ứng điện từ là gì?"],
        "Hóa học": ["Cách cân bằng phương trình hóa học?", "pH là gì?", "Phân biệt liên kết ion và liên kết cộng hóa trị?", "Công thức tính nồng độ mol?"],
        "Sinh học": ["Quá trình quang hợp diễn ra thế nào?", "ADN và ARN khác nhau ở đâu?", "Nguyên phân và giảm phân khác gì nhau?", "Đột biến gen là gì?"],
        "Ngữ văn": ["Phân tích nhân vật Chí Phèo", "Nêu cảm nhận về bài thơ Sóng", "Thuyết minh về chiếc áo dài Việt Nam", "Phân tích tác phẩm Vợ nhặt"],
        "Tiếng Anh": ["Giải thích thì hiện tại hoàn thành", "Phân biệt since và for", "Cách dùng câu điều kiện loại 2", "Phân biệt must và have to"],
        "Lịch sử": ["Nguyên nhân Cách mạng tháng 8/1945", "Phong trào Cần Vương là gì?", "Chiến dịch Điện Biên Phủ năm 1954", "Nội dung Hiệp định Paris 1973"],
        "Địa lý": ["Đặc điểm khí hậu nhiệt đới gió mùa", "Vì sao có hiện tượng thủy triều?", "Phân tích thế mạnh kinh tế biển nước ta", "Vẽ biểu đồ dân số Việt Nam qua các năm"],
        "Tin học": ["Vòng lặp for và while khác nhau thế nào?", "Python có kiểu dữ liệu gì?", "Cách đảo ngược một chuỗi trong Python?", "Sự khác biệt giữa List và Tuple?"],
        "Chung": ["Làm sao để học tốt hơn?", "Gợi ý phương pháp ghi nhớ hiệu quả", "Vòng lặp for và while khác nhau thế nào trong Python?", "Phong trào Cần Vương là gì?", "Cách cân bằng phương trình hóa học?", "Động năng và thế năng khác nhau thế nào?", "Làm sao để tập trung khi học?", "Cách lập kế hoạch học tập hiệu quả?"],
    },
    "en": {
        "Math": ["Solve equation x² - 5x + 6 = 0", "What is the derivative of sin(x)?", "How to calculate the area of a circle?", "Difference between permutation and combination?"],
        "Physics": ["State Newton's second law?", "Difference between kinetic and potential energy?", "Formula for equivalent resistance?", "What is electromagnetic induction?"],
        "Chemistry": ["How to balance a chemical equation?", "What is pH?", "Difference between ionic and covalent bonds?", "Formula for molarity?"],
        "Biology": ["How does photosynthesis work?", "Difference between DNA and RNA?", "Difference between mitosis and meiosis?", "What is a gene mutation?"],
        "Literature": ["Analyze the character Chi Pheo", "Share your thoughts on the poem 'Song'", "Introduce the Vietnamese Ao Dai", "Analyze the work 'Vo Nhat'"],
        "English": ["Explain present perfect tense", "Difference between 'since' and 'for'", "How to use conditional type 2", "Difference between 'must' and 'have to'"],
        "History": ["Causes of the August Revolution 1945", "What is the Can Vuong movement?", "Battle of Dien Bien Phu 1954", "Content of the 1973 Paris Peace Accords"],
        "Geography": ["Characteristics of tropical monsoon climate", "Why do tides occur?", "Analyze Vietnam's marine economic strengths", "Draw a chart of Vietnam's population over the years"],
        "Informatics": ["Difference between for and while loops?", "What data types does Python have?", "How to reverse a string in Python?", "Difference between List and Tuple?"],
        "General": ["How to study better?", "Tips for effective memorization", "Difference between for and while loops in Python?", "What is the Can Vuong movement?", "How to balance a chemical equation?", "Difference between kinetic and potential energy?", "How to stay focused while studying?", "How to plan study effectively?"],
    }
}

def _suggestions_for(subject, lang):
    lang_dict = SUGGESTIONS.get(lang, SUGGESTIONS["vi"])
    default_key = "Chung" if lang == "vi" else "General"
    return lang_dict.get(subject, lang_dict[default_key])


def render(theme_css: str, system_prompt_builder):
    st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)
    lang = st.session_state.get("lang", "vi")

    # Đảm bảo có conversation
    if "conversation_id" not in st.session_state or st.session_state.conversation_id is None:
        convs = db.list_conversations(st.session_state.user_id)
        if convs:
            st.session_state.conversation_id = convs[0]["id"]
        else:
            st.session_state.conversation_id = db.new_conversation(st.session_state.user_id)

    conv_id = st.session_state.conversation_id
    messages = db.get_messages(conv_id)

      # CSS cho Hero và Card
    st.markdown("""
    <style>
    /* Banner chính */
    .hero-banner {
        background: linear-gradient(135deg, #1A2235 0%, #253052 100%);
        border: 1px solid #3B4B6B;
        border-radius: 20px;
        padding: 40px;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center; /* Căn giữa theo chiều dọc */
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2); /* Đổ bóng nhẹ */
        overflow: hidden;
        position: relative;
    }
    
    /* Hiệu ứng ánh sáng mờ phía sau banner */
    .hero-banner::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(79, 124, 255, 0.15) 0%, transparent 70%);
        z-index: 0;
    }

    .hero-text {
        z-index: 1;
        max-width: 65%;
    }
    
    .hero-text h1 { 
        margin: 0 0 12px 0; 
        font-size: 36px; 
        font-weight: 700;
        color: #FFFFFF; 
        letter-spacing: -0.5px;
    }
    
    .hero-text p { 
        margin: 0; 
        font-size: 16px; 
        color: #A0ABC0; 
        line-height: 1.6; 
    }

    .hero-img { 
        font-size: 90px; 
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.3)); /* Hiệu ứng phát sáng cho icon */
        animation: float 3s ease-in-out infinite; /* Hiệu ứng lơ lửng */
    }

    /* Hiệu ứng icon lơ lửng nhẹ nhàng */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
        100% { transform: translateY(0px); }
    }

    /* 4 Card tính năng */
    .feature-card {
        background-color: #151B2B;
        border: 1px solid #232D42;
        border-radius: 14px;
        padding: 20px;
        height: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .feature-card:hover { 
        transform: translateY(-5px); 
        border-color: #4F7CFF; 
        box-shadow: 0 8px 20px rgba(79, 124, 255, 0.15);
    }
    
    .feature-card h4 { 
        margin: 0 0 10px 0; 
        font-size: 17px; 
        color: #FFFFFF; 
        display: flex; 
        align-items: center; 
        gap: 8px;
    }
    
    .feature-card p { 
        margin: 0; 
        font-size: 14px; 
        color: #94A3B8; 
        line-height: 1.4;
    }

    /* Nút gợi ý */
    .stButton > button { 
        border-radius: 20px !important;
        font-size: 14px !important;
        padding: 4px 12px !important;
        border: 1px solid #334155 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        border-color: #4F7CFF !important;
        background-color: rgba(79, 124, 255, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Hero Banner (Luôn hiển thị)
    hero_desc = t("hero_desc", lang)
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-text">
            <h1>🎓 StudyBot</h1>
            <p>{hero_desc}</p>
        </div>
        <div class="hero-img">🎓✨</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 4 Card tính năng
    cols = st.columns(4)
    cards = [
        ("🧮", t("solve", lang), t("solve_desc", lang) if t("solve_desc", lang) != "solve_desc" else "Giải bài theo từng bước."),
        ("📚", t("explain", lang), t("explain_desc", lang) if t("explain_desc", lang) != "explain_desc" else "Giải thích kiến thức dễ hiểu."),
        ("📝", t("practice", lang), t("practice_desc", lang) if t("practice_desc", lang) != "practice_desc" else "Tạo câu hỏi tự kiểm tra."),
        ("📖", t("summarize", lang), t("summarize_desc", lang) if t("summarize_desc", lang) != "summarize_desc" else "Rút gọn bài học thành ý chính."),
    ]
    for col, (icon, title, desc) in zip(cols, cards):
        with col:
            st.markdown(f'''
            <div class="feature-card">
                <h4>{icon} {title}</h4>
                <p>{desc}</p>
            </div>
            ''', unsafe_allow_html=True)

    st.write("")

    # 3. XỬ LÝ CÂU HỎI
    prompt = st.session_state.pop("pending_question", None)
    pending_action = st.session_state.pop("pending_action", None)
    pending_prompt = st.session_state.pop("pending_prompt", None)
    
    if pending_action:
        prompt = pending_prompt
    
    user_input = st.chat_input(t("chat_placeholder", lang))
    if user_input:
        prompt = user_input

    # 4. HIỂN THỊ LỊCH SỬ CHAT (Vẽ TRƯỚC KHI trả lời)
    if messages:
        st.markdown(f"### 💬 {t('chat_history', lang)}")
        for m in messages:
            avatar = "🎓" if m["role"] == "user" else "🤖"
            with st.chat_message(m["role"], avatar=avatar):
                st.markdown(m["content"])
    else:
        # Nếu chưa chat -> Hiện gợi ý
        col_title, col_btn = st.columns([8, 2])
        with col_title:
            st.markdown(f"### 💡 {t('suggested_q', lang)}")
        with col_btn:
            if st.button("🔀 " + t("shuffle", lang), use_container_width=True):
                st.session_state.pop("current_suggestions", None)
                st.rerun()

        st.caption(t("suggested_hint", lang))

        subject = st.session_state.get("subject", "Chung")
        pool_vi = _suggestions_for(subject, "vi")
        pool_en = _suggestions_for(subject, "en")

        if "current_suggestions" not in st.session_state or "suggestion_lang" not in st.session_state:
            pool = _suggestions_for(subject, lang)
            st.session_state.current_suggestions = random.sample(pool, min(4, len(pool)))
            st.session_state.suggestion_lang = lang
        elif st.session_state.suggestion_lang != lang:
            translated = []
            for q in st.session_state.current_suggestions:
                if st.session_state.suggestion_lang == "vi" and q in pool_vi:
                    idx = pool_vi.index(q)
                    if idx < len(pool_en): translated.append(pool_en[idx])
                    else: translated.append(q)
                elif st.session_state.suggestion_lang == "en" and q in pool_en:
                    idx = pool_en.index(q)
                    if idx < len(pool_vi): translated.append(pool_vi[idx])
                    else: translated.append(q)
                else: translated.append(q)
            
            st.session_state.current_suggestions = translated
            st.session_state.suggestion_lang = lang
            
        chosen = st.session_state.current_suggestions
        
        c1, c2 = st.columns(2)
        for i, q in enumerate(chosen):
            target = c1 if i % 2 == 0 else c2
            if target.button(q, key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_question = q
                st.rerun()

    # 5. NẾU CÓ CÂU HỎI MỚI -> TRẢ LỜI VÀ LƯU
    if prompt:
        # Lưu câu hỏi của user vào DB và hiển thị ngay dưới cùng
        db.add_message(conv_id, "user", prompt, subject=st.session_state.get("subject"))
        db.log_usage(st.session_state.user_id, "question", st.session_state.get("subject"))
        if len(messages) == 0:
            with db.conn() as c:
                c.execute("UPDATE conversations SET title=? WHERE id=?", (prompt[:60], conv_id))
        db.touch_conversation(conv_id)

        with st.chat_message("user", avatar="🎓"):
            st.markdown(prompt)

        # Gọi API và hiển thị câu trả lời ngay bên dưới
        key = os.getenv("STUDYBOT_API_KEY", "")
        url = os.getenv("STUDYBOT_BASE_URL", "")
        model = os.getenv("STUDYBOT_MODEL", "gemini-flash-latest")

        with st.chat_message("assistant", avatar="🤖"):
            if not key:
                answer = "⚠️ Chưa cấu hình API key trong file `.env`."
                st.markdown(answer)
            else:
                # Lấy lịch sử cũ + câu hỏi mới để gửi AI
                history = [{"role": m["role"], "content": m["content"]} for m in messages][-20:]
                history.append({"role": "user", "content": prompt})
                
                try:
                    answer = st.write_stream(
                        stream_chat(history, key, url, model, 0.4, system_prompt_builder()))
                except Exception as e:
                    answer = f"⚠️ Lỗi API: `{e}`"
                    st.markdown(answer)
        
        # Lưu câu trả lời vào DB
        db.add_message(conv_id, "assistant", answer)
        db.touch_conversation(conv_id)
        
        # Tải lại trang để giao diện đồng bộ (lúc này lịch sử đã có sẵn câu trả lời)
        st.rerun()