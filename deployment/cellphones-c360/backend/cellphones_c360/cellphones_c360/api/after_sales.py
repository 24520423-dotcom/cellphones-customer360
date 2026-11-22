import frappe
from frappe.model import get_permitted_fields


@frappe.whitelist(methods=["GET"])
def get_capabilities(ticket=None):
    doctype = "Customer Support Ticket"
    if ticket:
        doc = frappe.get_doc(doctype, ticket)
        doc.check_permission("read")
        writable_fields = set(get_permitted_fields(doctype, permission_type="write"))
        return {
            "canEdit": bool(
                doc.has_permission("write")
                and {"ticket_status", "resolution"}.issubset(writable_fields)
            ),
        }

    return {"canCreate": bool(frappe.has_permission(doctype, "create"))}
