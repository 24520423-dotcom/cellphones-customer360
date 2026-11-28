from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.model import get_permitted_fields
from frappe.utils import get_datetime, get_system_timezone

from cellphones_c360.api.crm_links import related_records
from cellphones_c360.api.leads import get_linked_history


def iso_timestamp(value):
    if not value:
        return None
    timestamp = get_datetime(value)
    zone = ZoneInfo(get_system_timezone())
    return (timestamp.astimezone(zone) if timestamp.tzinfo else timestamp.replace(tzinfo=zone)).isoformat()


def _rows(doctype, fields, filters):
    if not frappe.has_permission(doctype, "read"):
        return []
    permitted = set(get_permitted_fields(doctype, permission_type="read"))
    return frappe.get_list(
        doctype, fields=["name", *(field for field in fields if field in permitted)],
        filters=filters, page_length=0, order_by="name",
    )


def build_timeline(customer):
    events = []

    def add(kind, summary, timestamp, doctype, name, source=None):
        if timestamp:
            events.append({
                "id": f"{kind}-{doctype}-{name}",
                "type": kind,
                "summary": summary,
                "occurred_at": iso_timestamp(timestamp),
                "source": source or doctype,
                "related_doctype": doctype,
                "related_name": str(name),
            })

    add("customer", _("Customer profile created"), customer.creation, customer.doctype, customer.name,
        customer.source_channel)
    add("merge", _("Customer profile merged"), customer.get("merged_at"), customer.doctype, customer.name)
    for row in _rows(customer.doctype, ("merged_at",), {"merged_into": customer.name}):
        add("merge", _("A verified duplicate was merged into this profile"), row.get("merged_at"), customer.doctype, row.name)
    for row in _rows("C360 Source Record", ("received_at", "source_channel", "processing_status"), {"customer": customer.name}):
        add("intake", _("Source record received"), row.get("received_at"), "C360 Source Record", row.name, row.get("source_channel"))

    crm = related_records(customer)
    references = {
        customer.doctype: [customer.name],
        **{doctype: [row.name for row in rows] for doctype, rows in crm.items()},
    }
    for doctype, field, kind in (("CRM Lead", "lead_name", "lead"), ("CRM Deal", "status", "deal")):
        for row in crm[doctype]:
            add(kind, row.get(field) or row.name, row.creation, doctype, row.name)

    orders = _rows("Customer Order", ("order_date", "order_status", "creation", "paid_at", "completed_at"),
                   {"customer": customer.name})
    references["Customer Order"] = [row.name for row in orders]
    for row in orders:
        add("order", _("Order {0}").format(row.name), row.get("order_date") or row.get("creation"), "Customer Order", row.name)
        add("payment", _("Payment recorded · {0}").format(row.name), row.get("paid_at"), "Customer Order", row.name)
        add("fulfillment", _("Order handed over · {0}").format(row.name), row.get("completed_at"), "Customer Order", row.name)

    tickets = _rows("Customer Support Ticket", ("subject", "created_date", "creation", "resolved_date"),
                    {"customer": customer.name})
    references["Customer Support Ticket"] = [row.name for row in tickets]
    for row in tickets:
        add("support", row.get("subject") or row.name, row.get("created_date") or row.get("creation"),
            "Customer Support Ticket", row.name)
        add("resolution", _("Support request resolved · {0}").format(row.name), row.get("resolved_date"),
            "Customer Support Ticket", row.name)

    for item in get_linked_history(references):
        doctype, name = item["id"].split("/", 1)
        text = " · ".join(value for value in (item["title"], item["status"]) if value)
        add(item["kind"], text or item["type"], item["date"], doctype, name, item["reference_type"])

    for doctype, names in references.items():
        if not names:
            continue
        for link_type, ref_type, ref_name, time_field, title, kind, fallback in (
            ("FCRM Note", "reference_doctype", "reference_docname", "creation", "title", "note", _("CRM note")),
            ("Communication", "reference_doctype", "reference_name", "communication_date", "subject", "email", _("Communication")),
            ("Version", "ref_doctype", "docname", "creation", None, "change", _("Record updated")),
            ("Comment", "reference_doctype", "reference_name", "creation", None, "comment", _("Comment added")),
        ):
            filters = {ref_type: doctype, ref_name: ("in", names)}
            if link_type == "Comment":
                filters["comment_type"] = ("in", ("Comment", "Info"))
            if link_type == "Communication":
                filters["communication_medium"] = "Email"
            rows = _rows(link_type, (time_field, ref_name, *((title,) if title else ())), filters)
            for row in rows:
                text = (row.get(title) if title else None) or fallback
                add(kind, text, row.get(time_field), link_type, row.name, doctype)

    events.sort(key=lambda event: (get_datetime(event["occurred_at"]), event["id"]), reverse=True)
    return events
