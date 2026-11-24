import frappe
from frappe import _
from frappe.model import get_permitted_fields

from cellphones_c360.api.access import get_scoped_document
from cellphones_c360.api.crm_links import can_link
from cellphones_c360.api.intake import intake_access
from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
    CRM_DOCTYPES,
    normalize_email,
    normalize_phone,
)

DOCTYPE = "C360 Customer"
EDIT_FIELDS = ("customer_name", "phone_number", "email", "customer_type", "customer_status", "source_channel")
FORM_FIELDS = EDIT_FIELDS + ("marketing_consent",)
LINK_FIELDS = ("crm_contact", "crm_lead")


@frappe.whitelist(methods=["GET"])
def get_access(customer=None):
    if not customer:
        return {
            "canCreate": bool(frappe.has_permission(DOCTYPE, "create")),
            "fields": form_fields("create"),
            **intake_access(),
        }

    doc = get_scoped_document(DOCTYPE, customer)
    writable = set(get_permitted_fields(DOCTYPE, permission_type="write"))
    readable = set(get_permitted_fields(DOCTYPE, permission_type="read"))
    can_edit = (
        not doc.get("merged_into") and doc.has_permission("write")
        and set(EDIT_FIELDS).issubset(writable & readable)
    )
    can_associate = can_link(doc)
    from cellphones_c360.api.merge import _can_merge
    can_review = not doc.get("merged_into") and _can_merge(doc)
    return {
        "canEdit": bool(can_edit),
        "canReviewDuplicate": bool(can_review),
        "fields": form_fields("write") if can_edit else [],
        "crmTypes": [doctype for doctype in CRM_DOCTYPES if frappe.has_permission(doctype, "read")]
        if can_associate else [],
        "canCreateLead": can_associate and frappe.has_permission("CRM Lead", "create"),
        "canCreateDeal": can_associate and frappe.has_permission("CRM Deal", "create"),
    }


def form_fields(action):
    if not frappe.has_permission(DOCTYPE, action):
        return []
    meta = frappe.get_meta(DOCTYPE)
    permitted = set(get_permitted_fields(DOCTYPE, permission_type="write"))
    readable = set(get_permitted_fields(DOCTYPE, permission_type="read"))
    fields = []
    for fieldname in FORM_FIELDS + (LINK_FIELDS if action == "create" else ()):
        df = meta.get_field(fieldname)
        if fieldname not in permitted or df.read_only or df.hidden:
            continue
        if fieldname == "marketing_consent" and fieldname not in readable:
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
    doc = get_scoped_document(DOCTYPE, customer)
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


@frappe.whitelist(methods=["GET"])
def find_duplicates(customer=None, customer_name=None, phone_number=None, email=None):
    if not frappe.has_permission(DOCTYPE, "read"):
        frappe.throw(_("You cannot review customer identities."), frappe.PermissionError)
    fields = ("customer_name", "phone_number", "email")
    readable = set(get_permitted_fields(DOCTYPE, permission_type="read"))
    readable_identity = [field for field in fields if field in readable]

    if customer:
        doc = get_scoped_document(DOCTYPE, customer)
        doc.apply_fieldlevel_read_permissions()
        values = {field: doc.get(field) for field in readable_identity}
    else:
        supplied = {
            "customer_name": " ".join((customer_name or "").split()),
            "phone_number": normalize_phone(phone_number),
            "email": normalize_email(email),
        }
        values = {field: supplied[field] for field in readable_identity}

    predicates = {field: value for field, value in values.items() if value}
    if not predicates:
        return []
    filters = {"name": ("!=", customer)} if customer else {}
    if frappe.get_meta(DOCTYPE).has_field("merged_into"):
        filters["merged_into"] = ("is", "not set")
    rows = frappe.get_list(
        DOCTYPE,
        filters=filters,
        or_filters=predicates,
        fields=["name", *readable_identity, "modified"],
        order_by="modified desc, name",
        page_length=20,
    )
    for row in rows:
        row.matched_fields = [
            field for field, value in predicates.items()
            if (row.get(field) or "").casefold() == value.casefold()
        ]
    return [row for row in rows if row.matched_fields]
