"""SQLite: lưu users, conversations, messages, usage_log, user_preferences.
Mọi hàm đều nhận user_id để đảm bảo người dùng chỉ thấy dữ liệu của mình.
"""
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "studybot.db"


@contextmanager
def conn():
    """Mở kết nối, tự commit khi xong, tự đóng khi thoát."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    """Tạo các bảng nếu chưa có."""
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            subject TEXT,
            created_at REAL NOT NULL,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id)
        );
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feature TEXT NOT NULL,
            subject TEXT,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            preset TEXT NOT NULL,
            bg TEXT NOT NULL,
            text_color TEXT NOT NULL,
            accent TEXT NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_log(user_id, created_at);
        """)


# ---------- USERS ----------
def create_user(username, password_hash):
    with conn() as c:
        c.execute(
            "INSERT INTO users(username, password_hash, created_at) VALUES (?,?,?)",
            (username, password_hash, time.time()),
        )
        return c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()["id"]


def get_user(username):
    with conn() as c:
        return c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()


def user_exists(username):
    return get_user(username) is not None


# ---------- USER PREFERENCES (THEME) ----------
def get_user_theme(user_id):
    """Trả về dict {preset, bg, text, accent} hoặc None nếu user chưa lưu theme."""
    with conn() as c:
        row = c.execute(
            "SELECT preset, bg, text_color, accent FROM user_preferences WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "preset": row["preset"],
            "bg": row["bg"],
            "text": row["text_color"],
            "accent": row["accent"],
        }


def save_user_theme(user_id, preset, bg, text, accent):
    """Lưu/ghi đè theme của user (upsert)."""
    with conn() as c:
        c.execute("""
            INSERT INTO user_preferences(user_id, preset, bg, text_color, accent, updated_at)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                preset=excluded.preset,
                bg=excluded.bg,
                text_color=excluded.text_color,
                accent=excluded.accent,
                updated_at=excluded.updated_at
        """, (user_id, preset, bg, text, accent, time.time()))


def new_conversation(user_id, title="New conversation"):
    with conn() as c:
        now = time.time()
        c.execute(
            "INSERT INTO conversations(user_id, title, created_at, updated_at) VALUES (?,?,?,?)",
            (user_id, title[:80], now, now),
        )
        return c.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]


def list_conversations(user_id, search=""):
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM conversations WHERE user_id=? AND title LIKE ? "
            "ORDER BY updated_at DESC",
            (user_id, f"%{search}%"),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_conversation(user_id, conv_id):
    with conn() as c:
        c.execute(
            "DELETE FROM messages WHERE conversation_id=? AND conversation_id IN "
            "(SELECT id FROM conversations WHERE user_id=? AND id=?)",
            (conv_id, user_id, conv_id),
        )
        c.execute("DELETE FROM conversations WHERE id=? AND user_id=?", (conv_id, user_id))


def touch_conversation(conv_id):
    with conn() as c:
        c.execute("UPDATE conversations SET updated_at=? WHERE id=?", (time.time(), conv_id))


# ---------- MESSAGES ----------
def add_message(conv_id, role, content, subject=None):
    with conn() as c:
        c.execute(
            "INSERT INTO messages(conversation_id, role, content, subject, created_at) "
            "VALUES (?,?,?,?,?)",
            (conv_id, role, content, subject, time.time()),
        )


def get_messages(conv_id):
    with conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY id",
            (conv_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------- USAGE ----------
def log_usage(user_id, feature, subject=None):
    with conn() as c:
        c.execute(
            "INSERT INTO usage_log(user_id, feature, subject, created_at) VALUES (?,?,?,?)",
            (user_id, feature, subject, time.time()),
        )


def usage_stats(user_id, since_ts=None):
    where = "WHERE user_id=?"
    params = [user_id]
    if since_ts:
        where += " AND created_at>=?"
        params.append(since_ts)
    with conn() as c:
        total_q = c.execute(
            f"SELECT COUNT(*) n FROM usage_log {where} AND feature='question'", params
        ).fetchone()["n"]
        total_conv = c.execute(
            "SELECT COUNT(*) n FROM conversations WHERE user_id=?", (user_id,)
        ).fetchone()["n"]
        by_subject = c.execute(
            f"SELECT COALESCE(subject,'Chung') s, COUNT(*) n FROM usage_log "
            f"{where} AND feature='question' GROUP BY s ORDER BY n DESC", params
        ).fetchall()
        by_feature = c.execute(
            f"SELECT feature f, COUNT(*) n FROM usage_log {where} GROUP BY f ORDER BY n DESC",
            params,
        ).fetchall()
        by_day = c.execute(
            f"SELECT date(created_at,'unixepoch','localtime') d, COUNT(*) n "
            f"FROM usage_log {where} AND feature='question' GROUP BY d ORDER BY d", params
        ).fetchall()
        recent = c.execute(
            f"SELECT feature, subject, created_at FROM usage_log {where} "
            f"ORDER BY created_at DESC LIMIT 20", params
        ).fetchall()
    return {
        "total_questions": total_q,
        "total_conversations": total_conv,
        "by_subject": [dict(r) for r in by_subject],
        "by_feature": [dict(r) for r in by_feature],
        "by_day": [dict(r) for r in by_day],
        "recent": [dict(r) for r in recent],
    }