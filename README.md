# 🎓 StudyBot - Chatbot hỗ trợ học tập (Gemini) - bản cá nhân hóa giao diện

## Chạy nhanh
```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Mặc định chạy **Demo Mode**, không cần API.

## Dùng Gemini thật
1. Tạo API key miễn phí: https://aistudio.google.com/apikey
2. Dán key vào ô **API Key** ở thanh bên (hoặc copy `.env.example` thành `.env` và điền `STUDYBOT_API_KEY`).
3. Chọn **Chế độ → Gemini API Mode**, bấm **🔌 Kiểm tra**.

| Thiết lập | Giá trị |
|-----------|---------|
| Base URL | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Model | `gemini-flash-latest` (mặc định). Lỗi 404 thì bấm **📋 Model** và chọn model có sẵn |

## Cá nhân hóa giao diện (đổi màu nền, màu chữ)
Ở **đầu trang chatbot** có khung **🎨 Giao diện của bạn**:
- **Bộ màu có sẵn**: 🌙 Tối (mặc định), ☀️ Sáng, 🌊 Xanh đêm, 🌿 Rừng xanh, ☕ Cà phê, 🌸 Hồng nhạt.
- **Màu nền / Màu chữ / Màu nhấn**: tự chọn bằng bảng màu. Các màu phụ (khung, ô nhập, viền, nút) tự động tính theo 3 màu này.
- **🪄 Chữ dễ đọc**: tự chọn chữ trắng hoặc đen phù hợp với màu nền. App cũng cảnh báo khi chữ và nền quá gần màu nhau.
- **↩️ Mặc định**: quay về giao diện tối.
- Lựa chọn được ghi nhớ trong `data/theme.json` (lần mở sau vẫn giữ màu). Muốn thêm bộ màu mới: sửa `PRESETS` trong `theme.py`.

## Về lỗi phông chữ
- Giao diện dùng phông **Be Vietnam Pro** (Google Fonts). Nếu máy không có mạng hoặc bị chặn, tự chuyển sang Segoe UI / Roboto / Arial.
- CSS **không** đặt font cho mọi phần tử, nên các icon của Streamlit (mũi tên, đóng/mở sidebar) không bị hiện thành chữ.
- Phản hồi từ API được giải mã UTF-8 nên tiếng Việt không bị lỗi ký tự.
- Nếu vẫn lỗi: nhấn `Ctrl+Shift+R` để tải lại trang không dùng cache; kiểm tra file `app.py` được lưu ở mã hóa **UTF-8**.

## Cấu trúc
```
.
├── app.py              # Giao diện Streamlit
├── gemini_client.py    # Gọi Gemini (stream, danh sách model, báo lỗi)
├── theme.py            # Bộ màu, tính màu phụ, tạo CSS, lưu theme
├── data/theme.json     # (tự tạo) giao diện người dùng đã chọn
├── requirements.txt
├── .env.example
├── .gitignore
└── .streamlit/config.toml
```

## Kiến trúc
Người dùng → Streamlit UI → gemini_client → Gemini API (OpenAI-compatible) → trả lời dạng stream → UI
