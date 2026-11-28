import json
from hmac import compare_digest

import frappe
from frappe import _

from cellphones_c360.permissions import CUSTOMER, ORDER, TICKET


SCOPED_DOCTYPES = {CUSTOMER, ORDER, TICKET, "C360 Source Record"}
DOCUMENT_METHODS = {
    "frappe.client.get",
    "frappe.client.set_value",
    "frappe.client.delete",
    "frappe.desk.form.load.getdoc",
}


class InvalidTransition(frappe.ValidationError):
    http_status_code = 422


def get_scoped_document(doctype, name, *, for_update=False):
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("You do not have access to this module."), frappe.PermissionError)
    if not isinstance(name, str) or not name:
        frappe.throw(_("The requested record is unavailable."), frappe.DoesNotExistError)
    try:
        doc = frappe.get_doc(doctype, name, for_update=for_update)
    except frappe.DoesNotExistError:
        frappe.clear_last_message()
        doc = None
    if not doc or not doc.has_permission("read"):
        frappe.throw(_("The requested record is unavailable."), frappe.DoesNotExistError)
    return doc


def sanitize_api_error(request, response):
    if response is None or response.status_code < 400 or not response.is_json:
        return
    parts = request.path.strip("/").split("/")
    if not parts or parts.pop(0) != "api":
        return
    version_two = parts[:1] == ["v2"]
    if parts[:1] in (["v1"], ["v2"]):
        parts.pop(0)
    route = parts[0] if parts else ""
    method = parts[1] if route == "method" and len(parts) == 2 else ""
    if route in ("resource", "document") and len(parts) >= 2:
        doctype = parts[1]
        name = parts[2] if len(parts) >= 3 else None
    elif method in DOCUMENT_METHODS:
        doctype = frappe.form_dict.get("doctype")
        name = frappe.form_dict.get("name")
    else:
        doctype, name = None, None
    scoped_doctype = isinstance(doctype, str) and doctype in SCOPED_DOCTYPES
    if not method.startswith("cellphones_c360.api.") and not scoped_doctype:
        return

    status = response.status_code
    if scoped_doctype and isinstance(name, str) and name and status in (403, 404):
        if not frappe.has_permission(doctype, "read"):
            status = 403
        elif status == 403:
            if not frappe.db.exists(doctype, name) or not frappe.get_doc(doctype, name).has_permission("read"):
                status = 404
    messages = {
        401: ("AuthenticationError", _("Please sign in again.")),
        403: ("PermissionError", _("You do not have permission to perform this action.")),
        404: ("DoesNotExistError", _("The requested record is unavailable.")),
        InvalidTransition.http_status_code: (
            "InvalidTransition", _("The requested status transition is not allowed."),
        ),
        500: ("ServerError", _("The request could not be completed.")),
    }
    generic = messages.get(500 if status >= 500 else status)
    if generic:
        error, message = generic
        if version_two:
            body = {"errors": [{"type": error, "message": message}]}
        else:
            body = {
                "exc_type": error,
                "_server_messages": json.dumps([json.dumps({"message": message})]),
            }
    else:
        body = response.get_json()
        if not isinstance(body, dict):
            return
        for key in ("exc", "exception", "_debug_messages"):
            body.pop(key, None)
        for error in body.get("errors") or []:
            error.pop("exception", None)
    response.status_code = status
    response.set_data(json.dumps(body, ensure_ascii=False))


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
