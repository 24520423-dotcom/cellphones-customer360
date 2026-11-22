import frappe
from frappe.model import get_permitted_fields


@frappe.whitelist(methods=["GET"])
def get_options(deal=None):
    doctype = "CRM Deal"
    writable = set(get_permitted_fields(doctype, permission_type="write"))
    if deal:
        doc = frappe.get_doc(doctype, deal)
        doc.check_permission("read")
        return {"canEdit": bool(doc.has_permission("write") and "status" in writable)}

    if not frappe.has_permission(doctype, "read"):
        frappe.throw("Bạn không có quyền xem Deal.", frappe.PermissionError)

    statuses = frappe.get_list(
        "CRM Deal Status",
        fields=["name", "type"],
        order_by="position asc, name asc",
        page_length=0,
    )
    return {
        "statuses": statuses,
        "canCreate": bool(frappe.has_permission(doctype, "create")),
        "canMove": bool(frappe.has_permission(doctype, "write") and "status" in writable),
    }
