import frappe
from frappe import _
from frappe.model import get_permitted_fields

DOCTYPE = "C360 Customer"
EDIT_FIELDS = ("customer_name", "phone_number", "email", "customer_type", "customer_status", "source_channel")
LINK_FIELDS = ("crm_contact", "crm_lead")


@frappe.whitelist(methods=["GET"])
def get_access(customer=None):
    if not customer:
        return {
            "canCreate": bool(frappe.has_permission(DOCTYPE, "create")),
            "fields": form_fields("create"),
        }

    doc = frappe.get_doc(DOCTYPE, customer)
    doc.check_permission("read")
    writable = set(get_permitted_fields(DOCTYPE, permission_type="write"))
    readable = set(get_permitted_fields(DOCTYPE, permission_type="read"))
    can_edit = doc.has_permission("write") and set(EDIT_FIELDS).issubset(writable & readable)
    return {"canEdit": bool(can_edit), "fields": form_fields("write") if can_edit else []}


def form_fields(action):
    if not frappe.has_permission(DOCTYPE, action):
        return []
    meta = frappe.get_meta(DOCTYPE)
    permitted = set(get_permitted_fields(DOCTYPE, permission_type=action))
    fields = []
    for fieldname in EDIT_FIELDS + (LINK_FIELDS if action == "create" else ()):
        df = meta.get_field(fieldname)
        if fieldname not in permitted or df.read_only or df.hidden:
            continue
        if df.fieldtype == "Link" and not (
            frappe.has_permission(df.options, "read") or frappe.has_permission(df.options, "select")
        ):
            continue
        fields.append({
            "fieldname": fieldname,
            "label": df.label.strip(),
            "fieldtype": df.fieldtype,
            "options": df.options.splitlines() if df.fieldtype == "Select" else df.options,
            "required": bool(df.reqd),
            "default": df.default,
        })
    return fields


@frappe.whitelist(methods=["POST"])
def update_customer(customer, values: dict, modified):
    doc = frappe.get_doc(DOCTYPE, customer)
    doc.check_permission("read")
    doc.check_permission("write")
    allowed = {field["fieldname"] for field in form_fields("write")}
    if not set(values).issubset(allowed):
        frappe.throw(_("Some customer fields cannot be edited."), frappe.PermissionError)
    if not modified:
        frappe.throw(_("Reload the customer before editing."))

    doc.update(values)
    doc.modified = modified
    doc.save()
    return {"name": doc.name}
