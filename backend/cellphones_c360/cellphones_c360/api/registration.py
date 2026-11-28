import re

import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime, validate_email_address

from cellphones_c360.api.access import require_session_csrf

DOCTYPE = "C360 Registration Request"
DEPARTMENTS = ("Sales", "Customer Service", "Operations", "Other")
ROLES = ("Sales User", "Sales Manager")
FIELDS = [
    "name", "full_name", "email", "phone", "department", "status", "creation",
    "reason", "reviewed_by", "reviewed_at", "assigned_role", "invitation_status", "invitation_queue",
]


def _text(value, maximum):
    if not isinstance(value, str) or len(value) > maximum:
        frappe.throw("Thông tin không hợp lệ.", frappe.ValidationError)
    return value.strip()


def _require_administrator():
    if frappe.session.user != "Administrator":
        frappe.throw("Chỉ Administrator có quyền duyệt đăng ký.", frappe.PermissionError)




@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=600, methods=["POST"])
def submit(full_name="", email="", phone="", department="", website=""):
    if website:
        return {"accepted": True}

    full_name = _text(full_name, 140)
    email = _text(email, 140).lower()
    phone = re.sub(r"[ .()\-]", "", _text(phone, 40))
    if (
        len(full_name) < 2 or any(ord(char) < 32 for char in full_name)
        or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
        or not validate_email_address(email)
        or not re.fullmatch(r"\+?[0-9]{9,15}", phone)
        or department not in DEPARTMENTS
    ):
        frappe.throw("Vui lòng kiểm tra họ tên, email, số điện thoại và bộ phận.", frappe.ValidationError)

    if not frappe.db.exists("User", email) and not frappe.db.exists(DOCTYPE, {"email": email}):
        frappe.db.savepoint("registration_insert")
        try:
            frappe.get_doc({
                "doctype": DOCTYPE, "full_name": full_name, "email": email,
                "phone": phone, "department": department, "status": "Pending",
            }).insert(ignore_permissions=True)
        except (frappe.DuplicateEntryError, frappe.UniqueValidationError):
            frappe.db.rollback(save_point="registration_insert")
            frappe.clear_messages()

    # Keep the response identical for new, duplicate and existing-account submissions.
    return {"accepted": True}


def _invitation_status(row):
    if row.invitation_queue:
        status = frappe.db.get_value("Email Queue", row.invitation_queue, "status")
        if status == "Sent":
            return "Sent"
        if status == "Error":
            return "Failed"
    return row.invitation_status


@frappe.whitelist(methods=["GET"])
def list_requests(status="Pending", page=1):
    _require_administrator()
    if status not in ("Pending", "Approved", "Rejected", "All"):
        frappe.throw("Trạng thái không hợp lệ.", frappe.ValidationError)
    page = max(1, min(frappe.utils.cint(page), 10000))
    rows = frappe.get_list(
        DOCTYPE, fields=FIELDS, filters={} if status == "All" else {"status": status},
        order_by="creation desc, name desc", start=(page - 1) * 20, page_length=21,
    )
    for row in rows[:20]:
        row.invitation_status = _invitation_status(row)
        row.pop("invitation_queue", None)
    return {"items": rows[:20], "has_more": len(rows) > 20, "roles": _roles()}


def _roles():
    return [role for role in ROLES if frappe.db.exists("Role", {"name": role, "disabled": 0})]


def _queue_invitation(request):
    user = frappe.get_doc("User", request.provisioned_user, for_update=True)
    if not user.enabled or user.email.lower() != request.email:
        frappe.throw("Tài khoản đã bị vô hiệu hóa hoặc email đã thay đổi.", frappe.ValidationError)

    frappe.db.savepoint("registration_email")
    try:
        reset_password = getattr(user, "_reset_password", None) or user.reset_password
        link = reset_password(send_email=False)
        queue = frappe.sendmail(
            recipients=[user.email], subject="Thiết lập mật khẩu CellphoneS Customer 360",
            template="password_reset",
            args={"first_name": user.first_name, "link": link},
            reference_doctype=DOCTYPE, reference_name=request.name,
            delayed=True, retry=3, redact_message_after_send=True,
        )
        if not queue or not getattr(queue, "name", None):
            frappe.throw("Không tạo được email thiết lập mật khẩu.")
        request.invitation_queue = queue.name
        request.invitation_status = "Queued"
    except Exception:
        frappe.db.rollback(save_point="registration_email")
        frappe.clear_messages()
        request.invitation_status = "Failed"


def _result(request):
    return {"status": request.status, "invitation_status": _invitation_status(request)}


@frappe.whitelist(methods=["POST"])
def review(name, decision, reason, role=None):
    require_session_csrf()
    _require_administrator()
    if decision not in ("Approved", "Rejected"):
        frappe.throw("Quyết định không hợp lệ.", frappe.ValidationError)
    request = frappe.get_doc(DOCTYPE, _text(name, 140), for_update=True)
    if request.status == decision:
        return _result(request)
    if request.status != "Pending":
        frappe.throw("Yêu cầu đã được xử lý.", frappe.ValidationError)
    reason = _text(reason, 1000)
    if not reason:
        frappe.throw("Vui lòng nhập lý do.", frappe.ValidationError)

    if decision == "Approved":
        if role not in _roles():
            frappe.throw("Vai trò được chọn không hợp lệ.", frappe.ValidationError)
        if frappe.db.exists("User", request.email):
            frappe.throw("Email đã có tài khoản Frappe. Kiểm tra tài khoản hiện có trong User.", frappe.ValidationError)

        if frappe.db.exists("User", {"mobile_no": request.phone}):
            frappe.throw("Số điện thoại đã thuộc tài khoản Frappe khác.", frappe.ValidationError)

        user = frappe.get_doc({
            "doctype": "User", "email": request.email, "first_name": request.full_name,
            "enabled": 1, "user_type": "System User", "mobile_no": request.phone,
            "send_welcome_email": 0, "roles": [{"role": role}],
        }).insert()
        request.assigned_role = role
        request.provisioned_user = user.name

    request.status = decision
    request.reason = reason
    request.reviewed_by = frappe.session.user
    request.reviewed_at = now_datetime()
    if decision == "Approved":
        _queue_invitation(request)
    request.save()
    return _result(request)


@frappe.whitelist(methods=["POST"])
def retry_invitation(name):
    require_session_csrf()
    _require_administrator()
    request = frappe.get_doc(DOCTYPE, _text(name, 140), for_update=True)
    if request.status != "Approved" or not request.provisioned_user:
        frappe.throw("Yêu cầu chưa được duyệt.", frappe.ValidationError)
    if _invitation_status(request) != "Failed":
        return _result(request)
    _queue_invitation(request)
    request.save()
    return _result(request)
