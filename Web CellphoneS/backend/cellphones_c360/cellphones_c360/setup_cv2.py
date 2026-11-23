"""Idempotent CRM custom fields for Phase 2.

Called during app install and on every migrate; never changes existing values.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

FIELDS = {
    "CRM Lead": [
        {"fieldname": "custom_c360_customer", "label": "Customer 360", "fieldtype": "Link", "options": "C360 Customer", "insert_after": "lead_owner"},
        {"fieldname": "custom_consultation_notes", "label": "Ghi chú tư vấn", "fieldtype": "Small Text", "insert_after": "custom_c360_customer"},
    ],
    "CRM Deal": [
        {"fieldname": "custom_c360_customer", "label": "Customer 360", "fieldtype": "Link", "options": "C360 Customer", "insert_after": "lead"},
    ],
}


def ensure_custom_fields():
    missing = {}
    for doctype, fields in FIELDS.items():
        if not frappe.db.exists("DocType", doctype):
            frappe.throw(f"Thiếu DocType {doctype}; cần cài ứng dụng crm trước cellphones_c360.")
        meta = frappe.get_meta(doctype)
        pending = [field for field in fields if not meta.has_field(field["fieldname"])]
        if pending:
            missing[doctype] = pending
    if missing:
        create_custom_fields(missing, update=True)
        for doctype in missing:
            frappe.clear_cache(doctype=doctype)
