import frappe
from frappe.utils import get_datetime

from cellphones_c360.api.access import get_scoped_document

DOCTYPE = "CRM Lead"


@frappe.whitelist(methods=["GET"])
def get_options(lead=None):
    if not lead:
        return {
            "canCreate": bool(frappe.has_permission(DOCTYPE, "create")),
            "statuses": (
                frappe.get_list("CRM Lead Status", pluck="name", order_by="position asc", page_length=0)
                if frappe.has_permission("CRM Lead Status", "read")
                else []
            ),
        }

    doc = get_scoped_document(DOCTYPE, lead)
    return {
        "canEdit": bool(doc.has_permission("write")),
        "history": get_linked_history({"CRM Lead": [lead]}, limit=20),
    }


def get_linked_history(references, limit=0):
    doctypes = [doctype for doctype, names in references.items() if names]
    if not doctypes:
        return []

    names = [name for doctype in doctypes for name in references[doctype]]
    filters = {"reference_doctype": ["in", doctypes], "reference_docname": ["in", names]}
    history = []
    sources = [
        ("CRM Call Log", "call", "Cuộc gọi", "start_time", "type"),
        ("CRM Task", "task", "Công việc", "creation", "title"),
    ]
    for doctype, kind, label, timestamp, title in sources:
        if not frappe.has_permission(doctype, "read"):
            continue
        for row in frappe.get_list(
            doctype,
            fields=["name", timestamp, title, "status", "reference_doctype", "reference_docname"],
            filters=filters,
            order_by=f"{timestamp} desc, name desc",
            page_length=limit,
        ):
            if row.reference_docname not in references.get(row.reference_doctype, ()):
                continue
            date = row.get(timestamp)
            history.append({
                "id": f"{doctype}/{row.name}",
                "kind": kind,
                "type": label,
                "title": row.get(title),
                "status": row.status,
                "date": get_datetime(date).isoformat() if date else None,
                "reference_type": row.reference_doctype,
                "reference_name": row.reference_docname,
            })
    history.sort(key=lambda item: (item["date"] or "", item["id"]), reverse=True)
    return history[:limit] if limit else history
