from html import escape

import frappe
from frappe import _
from frappe.model import get_permitted_fields
from frappe.utils import cint

DOCTYPE = "Customer Support Ticket"

@frappe.whitelist(methods=["GET"])
def get_capabilities(ticket=None):
    if ticket:
        doc = frappe.get_doc(DOCTYPE, ticket)
        doc.check_permission("read")
        writable_fields = set(get_permitted_fields(DOCTYPE, permission_type="write"))
        return {
            "canEdit": bool(
                doc.has_permission("write")
                and {"ticket_status", "resolution"}.issubset(writable_fields)
            ),
        }

    readable = frappe.has_permission(DOCTYPE, "read")
    meta = frappe.get_meta(DOCTYPE)
    return {
        "canRead": bool(readable),
        "canCreate": bool(frappe.has_permission(DOCTYPE, "create")),
        "filters": {
            field: meta.get_field(field).options.splitlines()
            for field in ("ticket_status", "ticket_type", "priority")
        } if readable else {},
    }


@frappe.whitelist(methods=["GET"])
def list_tickets(search="", status="", ticket_type="", priority="", customer="", page=1):
    frappe.has_permission(DOCTYPE, "read", throw=True)
    readable = set(get_permitted_fields(DOCTYPE, permission_type="read"))
    meta = frappe.get_meta(DOCTYPE)
    filters = []
    for field, value in (("ticket_status", status), ("ticket_type", ticket_type), ("priority", priority)):
        if value and field in readable:
            if value not in meta.get_field(field).options.splitlines():
                frappe.throw(_("Invalid ticket filter."))
            filters.append([field, "=", value])
    if customer and "customer" in readable:
        frappe.get_doc("C360 Customer", customer).check_permission("read")
        filters.append(["customer", "=", customer])
    keyword = f"%{search.strip()[:140]}%" if search and search.strip() else None
    search_by = [[field, "like", keyword] for field in ("name", "subject") if field in readable] if keyword else []
    fields = [
        field for field in ("name", "subject", "customer", "ticket_type", "priority",
                            "ticket_status", "assigned_to", "created_date")
        if field in readable
    ]
    page = max(1, cint(page))
    rows = frappe.get_list(
        DOCTYPE, fields=fields, filters=filters, or_filters=search_by,
        order_by="created_date desc, name desc", start=(page - 1) * 20, page_length=21,
    )
    return {"items": rows[:20], "has_more": len(rows) > 20, "page": page}


@frappe.whitelist(methods=["POST"])
def record_demo_proposal(customer, proposal: str):
    record = frappe.get_doc("C360 Customer", customer, for_update=True)
    record.check_permission("read")
    if "C360 Marketing" not in frappe.get_roles():
        record.check_permission("write")
    record.apply_fieldlevel_read_permissions()
    if record.get("merged_into") or not cint(record.get("marketing_consent")):
        frappe.throw(_("Marketing proposals require recorded customer consent."), frappe.PermissionError)
    if not 1 <= len(proposal.strip()) <= 300:
        frappe.throw(_("Enter a proposal of at most 300 characters."))
    comment = record.add_comment("Comment", _("Demo proposal · {0}").format(escape(proposal.strip())))
    return {"comment": comment.name}
