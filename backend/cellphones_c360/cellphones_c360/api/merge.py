import frappe
from frappe import _
from frappe.model import get_permitted_fields
from frappe.utils import get_datetime, now_datetime

from cellphones_c360.api.customers import DOCTYPE, EDIT_FIELDS
from cellphones_c360.api.intake import DOCTYPE as SOURCE_RECORD
from cellphones_c360.permissions import MERGE_APPROVER
from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
    customer_crm_links,
    lock_customer_identity_writes,
)

MERGE_DOCTYPES = ("Customer Order", "Customer Support Ticket", SOURCE_RECORD)


def _has_merge_role():
    roles = set(frappe.get_roles())
    return (
        frappe.session.user == "Administrator" or "System Manager" in roles
        or {"Sales Manager", MERGE_APPROVER}.issubset(roles)
    )


def _documents(source, target, for_update=False):
    if not source or not target or source == target:
        frappe.throw(_("Choose two different customer records."))
    docs = [
        frappe.get_doc(DOCTYPE, name, for_update=for_update)
        for name in (source, target)
    ]
    for doc in docs:
        doc.check_permission("read")
        if doc.get("merged_into"):
            frappe.throw(_("Choose two active customer records."))
    return docs


def _can_merge(*docs):
    editable = set(get_permitted_fields(DOCTYPE, permission_type="write"))
    readable = set(get_permitted_fields(DOCTYPE, permission_type="read"))
    return (
        _has_merge_role()
        and set(EDIT_FIELDS).issubset(editable & readable)
        and all(doc.has_permission("write") for doc in docs)
    )


@frappe.whitelist(methods=["GET"])
def preview(source, target):
    original, golden = _documents(source, target)
    fields = [
        field for field in EDIT_FIELDS
        if field in get_permitted_fields(DOCTYPE, permission_type="read")
    ]
    meta = frappe.get_meta(DOCTYPE)
    return {
        "source": original.name,
        "target": golden.name,
        "source_modified": str(original.modified),
        "target_modified": str(golden.modified),
        "can_merge": _can_merge(original, golden),
        "fields": [
            {
                "fieldname": field,
                "label": meta.get_field(field).label.strip(),
                "source": original.get(field),
                "target": golden.get(field),
                "suggested": "target" if golden.get(field) else "source",
            }
            for field in fields
        ],
    }


def _dependencies(source):
    dependencies = {}
    for doctype in MERGE_DOCTYPES:
        # Discover every dependent record, then enforce its actual permissions.
        names = [
            name for (name,) in frappe.db.get_values(
                doctype, {"customer": source}, "name", order_by="name", for_update=True,
            )
        ]
        docs = [frappe.get_doc(doctype, name, for_update=True) for name in names]
        for doc in docs:
            doc.check_permission("read")
            doc.check_permission("write")
            if "customer" not in get_permitted_fields(doctype, permission_type="write"):
                frappe.throw(_("You cannot reassign a related record."), frappe.PermissionError)
        dependencies[doctype] = docs
    return dependencies


def _move(doc, customer):
    doc.customer = customer
    if doc.doctype == SOURCE_RECORD:
        doc.flags.processing_intake = True
    doc.flags.merging_customer = True
    doc.save()


@frappe.whitelist(methods=["POST"])
def merge_customers(source, target, source_modified, target_modified, selected: dict, reason, verified: bool):
    if not _has_merge_role():
        frappe.throw(_("You cannot merge customer records."), frappe.PermissionError)
    if verified is not True or not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 1000:
        frappe.throw(_("Confirm the customer's identity and enter a reason for the merge."))
    if not set(selected).issubset(EDIT_FIELDS) or any(value not in ("source", "target") for value in selected.values()):
        frappe.throw(_("Some selected fields cannot be merged."))

    lock_customer_identity_writes()
    original, golden = _documents(source, target, for_update=True)
    if not _can_merge(original, golden):
        frappe.throw(_("You cannot merge these customer records."), frappe.PermissionError)
    if not all(
        timestamp and get_datetime(timestamp) == get_datetime(doc.modified)
        for doc, timestamp in ((original, source_modified), (golden, target_modified))
    ):
        frappe.throw(_("A customer record changed. Review both records again."), frappe.TimestampMismatchError)

    savepoint = "c360_customer_merge"
    frappe.db.savepoint(savepoint)
    try:
        dependencies = _dependencies(original.name)
        additional_links = set(customer_crm_links(original)) - set(customer_crm_links(golden))
        if additional_links and not golden.has_permlevel_access_to("crm_links", permission_type="write"):
            frappe.throw(_("You cannot update CRM associations."), frappe.PermissionError)
        for doctype, name in sorted(additional_links):
            golden.append("crm_links", {"link_doctype": doctype, "link_name": name})
        for field, record in selected.items():
            if record == "source":
                golden.set(field, original.get(field))

        original.flags.merging_customer = True
        original.update({
            "customer_status": "Inactive",
            "merged_into": golden.name,
            "merged_by": frappe.session.user,
            "merged_at": now_datetime(),
            "merge_reason": reason.strip(),
        })
        original.save()
        golden.save()
        for docs in dependencies.values():
            for doc in docs:
                _move(doc, golden.name)
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise

    return {
        "customer": golden.name,
        "archived_customer": original.name,
        "moved": {doctype: len(docs) for doctype, docs in dependencies.items()},
        "crm_links_added": len(additional_links),
    }
