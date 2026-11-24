from datetime import date

import frappe
from frappe import _
from frappe.model import get_permitted_fields
from frappe.utils import cint

DOCTYPE = "Customer Order"
CUSTOMER = "C360 Customer"


@frappe.whitelist(methods=["GET"])
def get_access():
    readable = frappe.has_permission(DOCTYPE, "read")
    writable = frappe.has_permission(DOCTYPE, "create")
    metadata = frappe.get_meta(DOCTYPE)
    fields = {
        name: metadata.get_field(name).options.splitlines()
        for name in ("order_status", "sales_channel")
    } if readable else {}
    return {"canRead": bool(readable), "canCreate": bool(writable), "filters": fields}


@frappe.whitelist(methods=["GET"])
def list_orders(search="", status="", channel="", from_date="", to_date="", page=1):
    frappe.has_permission(DOCTYPE, "read", throw=True)
    readable = set(get_permitted_fields(DOCTYPE, permission_type="read"))
    meta = frappe.get_meta(DOCTYPE)
    filters = []
    search_fields = []
    if search and search.strip():
        keyword = f"%{search.strip()[:140]}%"
        search_fields.append(["name", "like", keyword])
        if "customer" in readable and frappe.has_permission(CUSTOMER, "read"):
            customer_fields = get_permitted_fields(CUSTOMER, permission_type="read")
            conditions = {"name": ("like", keyword)}
            if "customer_name" in customer_fields:
                conditions["customer_name"] = ("like", keyword)
            names = frappe.get_list(CUSTOMER, or_filters=conditions, pluck="name", page_length=500)
            if names:
                search_fields.append(["customer", "in", names])
    for field, value in (("order_status", status), ("sales_channel", channel)):
        if value and field in readable:
            if value not in meta.get_field(field).options.splitlines():
                frappe.throw(_("Invalid order filter."))
            filters.append([field, "=", value])
    if "order_date" in readable:
        try:
            start = date.fromisoformat(from_date) if from_date else None
            end = date.fromisoformat(to_date) if to_date else None
        except ValueError:
            frappe.throw(_("Use a valid order date."))
        if start and end and start > end:
            frappe.throw(_("The start date must precede the end date."))
        if start:
            filters.append(["order_date", ">=", start])
        if end:
            filters.append(["order_date", "<=", end])

    page = max(1, cint(page))
    fields = [
        name for name in ("name", "customer", "order_date", "sales_channel", "order_status",
                          "payment_status", "fulfillment_status", "total_amount")
        if name in readable
    ]
    rows = frappe.get_list(
        DOCTYPE, fields=fields, filters=filters, or_filters=search_fields,
        order_by="order_date desc, name desc", start=(page - 1) * 20, page_length=21,
    )
    return {"items": rows[:20], "has_more": len(rows) > 20, "page": page}
