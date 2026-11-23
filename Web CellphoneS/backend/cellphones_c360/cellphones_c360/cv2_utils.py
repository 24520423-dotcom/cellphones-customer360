"""Pure deterministic normalization and duplicate decisions; no Frappe dependency."""
import re
import unicodedata

CHANNELS = {"Website", "App", "Facebook", "Zalo", "Hotline", "Store", "Other"}
PHONE_RE = re.compile(r"0[35789][0-9]{8}\Z")
EMAIL_RE = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+\Z")


def normalize_phone(value):
    value = re.sub(r"[\s.()\-]", "", str(value or "").strip())
    if value.startswith("+84"):
        value = "0" + value[3:]
    elif value.startswith("84"):
        value = "0" + value[2:]
    return value


def normalize_email(value):
    return str(value or "").strip().lower()


def normalized_name(value):
    value = unicodedata.normalize("NFD", str(value or "").casefold())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.replace("đ", "d")
    return " ".join(value.split())


def validate_identity(name, phone, email):
    name = " ".join(str(name or "").split())
    phone = normalize_phone(phone)
    email = normalize_email(email)
    if not name:
        raise ValueError("Thiếu họ tên khách hàng.")
    if not (phone or email):
        raise ValueError("Cần ít nhất số điện thoại hoặc email.")
    if phone and not PHONE_RE.fullmatch(phone):
        raise ValueError("Số điện thoại không đúng định dạng di động Việt Nam.")
    if email and not EMAIL_RE.fullmatch(email):
        raise ValueError("Email không hợp lệ.")
    return {"customer_name": name, "phone_number": phone, "email": email}


def decide_match(identity, candidates):
    """Return (new|linked|review, customer_id|None, reason).

    Only a single record with a matching name and at least one exact unique
    identifier, without any conflicting identifier, can be linked automatically.
    No fuzzy-only merge. Identity comparisons are deterministic but do not
    replace a human identity check for uncertain cases.
    """
    phone, email = identity['phone_number'], identity['email']
    name = normalized_name(identity['customer_name'])
    hits = []
    seen = set()
    for c in candidates:
        cp, ce = normalize_phone(c.get('phone_number')), normalize_email(c.get('email'))
        pm = bool(phone and cp and phone == cp)
        em = bool(email and ce and email == ce)
        if not (pm or em) or c['name'] in seen:
            continue
        seen.add(c['name'])
        hits.append((c, pm, em))
    if not hits:
        return 'new', None, 'Không có số điện thoại hoặc email trùng.'
    if len(hits) != 1:
        return 'review', None, 'Có nhiều hồ sơ trùng định danh; cần đối chiếu thủ công.'
    candidate, pm, em = hits[0]
    conflicting = bool(
        (phone and candidate.get('phone_number') and not pm) or
        (email and candidate.get('email') and not em)
    )
    if conflicting:
        return 'review', candidate['name'], 'Số điện thoại hoặc email xung đột.'
    if normalized_name(candidate.get('customer_name')) != name:
        return 'review', candidate['name'], 'Thông tin định danh trùng nhưng họ tên khác.'
    return 'linked', candidate['name'], 'Định danh và họ tên trùng; không có thông tin xung đột.'
