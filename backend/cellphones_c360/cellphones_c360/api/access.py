from hmac import compare_digest

import frappe


def require_enabled_api_account():
    request = frappe.local.request
    user = frappe.session.user
    if request.path.startswith("/api/") and user not in ("", "Guest", "Administrator"):
        if not frappe.db.get_value("User", user, "enabled"):
            frappe.throw("Tài khoản đã bị vô hiệu hóa.", frappe.PermissionError)


def require_session_csrf():
    if not frappe.request:
        return

    saved = frappe.session.data.get("csrf_token")
    supplied = frappe.get_request_header("X-Frappe-CSRF-Token")
    if not saved or not supplied or not compare_digest(saved.encode(), supplied.encode()):
        frappe.throw("Thao tác này cần CSRF Token hợp lệ.", frappe.CSRFTokenError)
