import re
import bcrypt
import database as db


def hash_password(password: str) -> str:
    """Băm mật khẩu bằng bcrypt. Mật khẩu gốc KHÔNG được lưu ở đâu cả."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """So khớp mật khẩu người dùng nhập với chuỗi đã băm."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def validate_username(username: str) -> tuple[bool, str]:
    if not username:
        return False, "empty_username"
    if not re.match(r"^[A-Za-z0-9_.-]{3,32}$", username):
        return False, "invalid_username"
    return True, ""


def password_strength(password: str) -> tuple[int, list[str]]:
    """Trả về (điểm 0-5, danh sách tiêu chí chưa đạt)."""
    checks = {
        "length": len(password) >= 8,
        "upper": bool(re.search(r"[A-Z]", password)),
        "lower": bool(re.search(r"[a-z]", password)),
        "digit": bool(re.search(r"\d", password)),
        "special": bool(re.search(r"[^A-Za-z0-9]", password)),
    }
    missing = [k for k, ok in checks.items() if not ok]
    return sum(checks.values()), missing


def register(username, password, confirm) -> tuple[bool, str]:
    ok, err = validate_username(username)
    if not ok:
        return False, err
    if password != confirm:
        return False, "password_mismatch"
    score, missing = password_strength(password)
    if missing:
        return False, "weak_password:" + ",".join(missing)
    if db.user_exists(username):
        return False, "username_taken"
    db.create_user(username, hash_password(password))
    return True, "register_success"


def login(username, password) -> tuple[bool, str]:
    user = db.get_user(username)
    if not user or not verify_password(password, user["password_hash"]):
        return False, "invalid_credentials"
    return True, str(user["id"])