import frappe
from frappe.model import get_permitted_fields

DOCTYPE = "C360 Customer"
EDIT_FIELDS = ("customer_name", "phone_number", "email", "customer_type", "customer_status", "source_channel")


@frappe.whitelist(methods=["GET"])
def get_access(customer=None):
    if not customer:
        return {"canCreate": bool(frappe.has_permission(DOCTYPE, "create"))}

    doc = frappe.get_doc(DOCTYPE, customer)
    doc.check_permission("read")
    writable = set(get_permitted_fields(DOCTYPE, permission_type="write"))
    return {"canEdit": bool(doc.has_permission("write") and set(EDIT_FIELDS).issubset(writable))}
