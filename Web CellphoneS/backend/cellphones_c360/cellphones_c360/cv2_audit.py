"""Read-only CV2-01/04 schema inventory and integrity checks for an installed site.

Use: bench --site crm.localhost execute cellphones_c360.cv2_audit.audit_schema
This is intentionally not a whitelisted HTTP endpoint.
"""
import frappe

DOCTYPES = [
    "CRM Lead", "CRM Deal", "CRM Call Log", "CRM Task",
    "C360 Customer", "Customer Order", "Customer Order Item",
    "Customer Support Ticket", "C360 Registration Request", "C360 Customer Intake",
]


def audit_schema():
    result = {"doctypes": {}, "broken_links": [], "cross_customer_deals": [], "missing_fields": []}
    for doctype in DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            result["missing_fields"].append(f"Thiếu DocType: {doctype}")
            continue
        meta = frappe.get_meta(doctype)
        result["doctypes"][doctype] = {
            "istable": bool(meta.istable),
            "fields": [
                {"fieldname": field.fieldname, "fieldtype": field.fieldtype,
                 "options": field.options if field.fieldtype in ("Link", "Table", "Dynamic Link", "Select") else "",
                 "required": bool(field.reqd), "unique": bool(field.unique)}
                for field in meta.fields
            ],
        }

    for doctype, field in (("CRM Lead", "custom_c360_customer"),
                           ("CRM Lead", "custom_consultation_notes"),
                           ("CRM Deal", "custom_c360_customer")):
        if frappe.db.exists("DocType", doctype) and not frappe.get_meta(doctype).has_field(field):
            result["missing_fields"].append(f"{doctype}.{field}")

    # Inspect existing links, not only field metadata. Run as trusted site operator.
    for doctype, link_field, target in (
        ("Customer Order", "customer", "C360 Customer"),
        ("Customer Support Ticket", "customer", "C360 Customer"),
        ("Customer Support Ticket", "related_order", "Customer Order"),
        ("C360 Customer", "crm_lead", "CRM Lead"),
        ("CRM Lead", "custom_c360_customer", "C360 Customer"),
        ("CRM Deal", "lead", "CRM Lead"),
        ("CRM Deal", "custom_c360_customer", "C360 Customer"),
    ):
        if not (frappe.db.exists("DocType", doctype) and frappe.get_meta(doctype).has_field(link_field)):
            continue
        for row in frappe.get_all(doctype, fields=["name", link_field],
                                  filters={link_field: ["is", "set"]}, limit_page_length=0):
            if row.get(link_field) and not frappe.db.exists(target, row.get(link_field)):
                result["broken_links"].append({"doctype": doctype, "name": row.name,
                                               "field": link_field, "target": row.get(link_field)})

    if (frappe.db.exists("DocType", "CRM Deal")
            and frappe.get_meta("CRM Deal").has_field("custom_c360_customer")
            and frappe.get_meta("CRM Lead").has_field("custom_c360_customer")):
        for row in frappe.get_all("CRM Deal", fields=["name", "lead", "custom_c360_customer"],
                                  filters={"lead": ["is", "set"]}, limit_page_length=0):
            lead_customer = frappe.db.get_value("CRM Lead", row.lead, "custom_c360_customer")
            if lead_customer and row.custom_c360_customer and lead_customer != row.custom_c360_customer:
                result["cross_customer_deals"].append(row.name)
    return result
