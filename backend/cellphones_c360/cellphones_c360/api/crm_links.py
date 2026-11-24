import frappe
from frappe import _
from frappe.model import get_permitted_fields

from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
    CRM_DOCTYPES,
    customer_crm_links,
    lock_customer_identity_writes,
)

CUSTOMER = "C360 Customer"


def visible_doc(doctype, name):
    if not name or not frappe.has_permission(doctype, "read"):
        return None
    try:
        doc = frappe.get_doc(doctype, name)
    except frappe.DoesNotExistError:
        return None
    if not doc.has_permission("read"):
        return None
    doc.apply_fieldlevel_read_permissions()
    return doc


def related_records(customer):
    records = {doctype: [] for doctype in CRM_DOCTYPES}
    direct_deals = set()
    for doctype, name in customer_crm_links(customer):
        if doctype == "CRM Deal":
            direct_deals.add(name)
        elif doctype in records:
            doc = visible_doc(doctype, name)
            if doc:
                records[doctype].append(doc)

    if not frappe.has_permission("CRM Deal", "read"):
        return records

    contact_names = [contact.name for contact in records["Contact"]]
    lead_names = [lead.name for lead in records["CRM Lead"]]
    if contact_names:
        direct_deals.update(frappe.get_all("CRM Contacts", filters={
            "parenttype": "CRM Deal", "parentfield": "contacts", "contact": ("in", contact_names),
        }, pluck="parent"))
    conditions = []
    if direct_deals:
        conditions.append(["name", "in", sorted(direct_deals)])
    if lead_names:
        conditions.append(["lead", "in", lead_names])
    if conditions:
        records["CRM Deal"] = frappe.get_list(
            "CRM Deal", or_filters=conditions, page_length=0, order_by="creation desc, name",
            fields=["name", "lead", "status", "deal_owner", "probability", "expected_deal_value",
                    "total", "net_total", "creation"],
        )
    return records


def can_link(customer):
    return (
        not customer.get("merged_into")
        and frappe.get_meta(CUSTOMER).has_field("crm_links")
        and customer.has_permission("write")
        and customer.has_permlevel_access_to("crm_links", permission_type="write")
    )


def _editable_customer(customer):
    lock_customer_identity_writes()
    doc = frappe.get_doc(CUSTOMER, customer, for_update=True)
    doc.check_permission("read")
    if not can_link(doc):
        frappe.throw(_("You cannot link CRM records to this customer."), frappe.PermissionError)
    return doc


def _associate(customer, doctype, record):
    if (doctype, record) in customer_crm_links(customer):
        return
    customer.append("crm_links", {"link_doctype": doctype, "link_name": record})
    customer.save()


@frappe.whitelist(methods=["POST"])
def link_record(customer, doctype, record):
    if doctype not in CRM_DOCTYPES or not record:
        frappe.throw(_("Choose a Contact, CRM Lead or CRM Deal."))
    doc = _editable_customer(customer)
    if not visible_doc(doctype, record):
        frappe.throw(_("You cannot view the selected CRM record."), frappe.PermissionError)
    _associate(doc, doctype, record)
    return {"name": record}


@frappe.whitelist(methods=["POST"])
def create_linked_lead(customer, doc: dict):
    customer = _editable_customer(customer)
    writable = set(get_permitted_fields("CRM Lead", permission_type="create"))
    meta = frappe.get_meta("CRM Lead")
    values = {
        key: value for key, value in doc.items()
        if key in writable and meta.get_field(key) and not meta.get_field(key).read_only
    }
    lead = frappe.get_doc({"doctype": "CRM Lead", **values}).insert()
    _associate(customer, lead.doctype, lead.name)
    return {"name": lead.name}


@frappe.whitelist(methods=["POST"])
def create_linked_deal(customer, doc: dict):
    from crm.fcrm.doctype.crm_deal.crm_deal import create_deal

    customer = _editable_customer(customer)
    frappe.has_permission("CRM Deal", "create", throw=True)
    writable = set(get_permitted_fields("CRM Deal", permission_type="create"))
    meta = frappe.get_meta("CRM Deal")
    values = {
        key: value for key, value in doc.items()
        if key in writable and meta.get_field(key) and not meta.get_field(key).read_only
    }
    for field, doctype in (("contact", "Contact"), ("organization", "CRM Organization"), ("lead", "CRM Lead")):
        if doc.get(field):
            if not visible_doc(doctype, doc[field]):
                frappe.throw(_("You cannot view the selected {0}.").format(_(doctype)), frappe.PermissionError)
            values[field] = doc[field]
    for field in ("first_name", "last_name", "email", "mobile_no"):
        if field in doc:
            values[field] = doc[field]
    name = create_deal(values)
    _associate(customer, "CRM Deal", name)
    return name
