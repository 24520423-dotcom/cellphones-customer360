import csv
from datetime import datetime
from io import StringIO
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.utils import get_system_timezone, now_datetime

from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
    find_identity_matches,
    lock_customer_identity_writes,
    normalize_email,
    normalize_phone,
    normalize_source,
)
from cellphones_c360.cellphones_customer_360.doctype.c360_source_record.c360_source_record import source_key

DOCTYPE = "C360 Source Record"
CUSTOMER = "C360 Customer"
MAX_BATCH = 100
CSV_COLUMNS = {
    "source_channel", "source_record_id", "received_at", "customer_name",
    "phone_number", "email", "customer_type", "purchase_interest",
}


def _text(value, maximum=140):
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > maximum:
        frappe.throw(_("A source field has an invalid type or length."))
    return value.strip()


def _received_at(value):
    if not value:
        return now_datetime()
    try:
        received = datetime.fromisoformat(_text(value))
    except ValueError:
        frappe.throw(_("Received At must be an ISO 8601 date and time."))
    if received.tzinfo:
        return received.astimezone(ZoneInfo(get_system_timezone())).replace(tzinfo=None)
    return received


def _normalize(row):
    name = " ".join(_text(row.get("customer_name")).split())
    if not name:
        frappe.throw(_("Customer Name is required."))
    phone = normalize_phone(_text(row.get("phone_number")))
    email = normalize_email(_text(row.get("email")))
    customer_type = _text(row.get("customer_type")) or "Individual"
    if customer_type not in frappe.get_meta(CUSTOMER).get_field("customer_type").options.splitlines():
        frappe.throw(_("Customer Type is invalid."))
    interest = row.get("purchase_interest")
    if interest not in (None, "", 0, 1, "0", "1"):
        frappe.throw(_("Purchase Interest must be 0 or 1."))
    return {
        "customer_name": name,
        "phone_number": phone,
        "email": email,
        "customer_type": customer_type,
        "received_at": _received_at(row.get("received_at")),
        "purchase_interest": int(interest in (1, "1")),
    }


def _result(record, replay=False):
    customer = record.customer
    return {
        "source_record_id": record.source_record_id,
        "source_document": record.name,
        "status": record.processing_status,
        "reason": record.result_reason,
        "customer": customer if customer and frappe.has_permission(CUSTOMER, "read", doc=customer) else None,
        "purchase_interest": bool(record.purchase_interest),
        "replay": replay,
    }


def _require(doctype, permission):
    if not frappe.has_permission(doctype, permission):
        frappe.throw(_("You cannot process Customer 360 source records."), frappe.PermissionError)


def _process(row, channel, reference):
    name = source_key(channel, reference)
    if frappe.db.get_value(DOCTYPE, name, "name", for_update=True):
        record = frappe.get_doc(DOCTYPE, name, for_update=True)
        record.check_permission("read")
        return _result(record, replay=True)

    record = frappe.get_doc({
        "doctype": DOCTYPE,
        "source_channel": channel,
        "source_record_id": reference,
        "received_at": now_datetime(),
    })
    record.flags.processing_intake = True
    savepoint = "c360_intake_row"
    frappe.db.savepoint(savepoint)
    try:
        normalized = _normalize(row)
        record.update({field: value for field, value in normalized.items() if field != "customer_type"})
        matches = find_identity_matches(record.phone_number, record.email)
        related = None
        if len(matches) == 1 and matches[0].phone_match and matches[0].email_match:
            candidate = frappe.get_doc(CUSTOMER, matches[0].name, for_update=True)
            if candidate.has_permission("read"):
                candidate.apply_fieldlevel_read_permissions()
                if (candidate.customer_name or "").casefold() == record.customer_name.casefold():
                    related = candidate.name
        if related:
            record.customer = related
            record.processing_status = "Linked"
            record.result_reason = _("Name, phone number and email matched an accessible customer.")
        elif matches:
            record.processing_status = "Needs Review"
            record.result_reason = _("Verify the existing phone number or email before linking the record.")
        else:
            customer = frappe.get_doc({
                "doctype": CUSTOMER,
                "source_channel": channel,
                "customer_name": record.customer_name,
                "phone_number": record.phone_number,
                "email": record.email,
                "customer_type": normalized["customer_type"],
            }).insert()
            record.customer = customer.name
            record.processing_status = "Created"
    except frappe.ValidationError as exc:
        frappe.db.rollback(save_point=savepoint)
        frappe.clear_last_message()
        record.processing_status = "Invalid"
        record.result_reason = str(exc)
    record.insert()
    return _result(record)


@frappe.whitelist(methods=["POST"])
def process_records(rows: list[dict]):
    for perm in ("read", "create"):
        _require(DOCTYPE, perm)
    _require(CUSTOMER, "create")
    if not 1 <= len(rows) <= MAX_BATCH:
        frappe.throw(_("Send between 1 and {0} source records.").format(MAX_BATCH))

    channels = frappe.get_meta(CUSTOMER).get_field("source_channel").options.splitlines()
    lock_customer_identity_writes()
    results = []
    for index, row in enumerate(rows, start=1):
        try:
            channel = normalize_source(_text(row.get("source_channel")))
            reference = _text(row.get("source_record_id"))
            if channel not in channels or not channel or not reference:
                frappe.throw(_("A valid Source Channel and Source Record ID are required."))
        except frappe.ValidationError as exc:
            frappe.clear_last_message()
            results.append({"row": index, "status": "Invalid", "reason": str(exc)})
            continue
        results.append({"row": index, **_process(row, channel, reference)})
    return {"items": results}


@frappe.whitelist(methods=["POST"])
def process_csv(csv_text: str):
    _require(DOCTYPE, "create")
    if len(csv_text) > 128_000:
        frappe.throw(_("The source CSV exceeds the supported size."))
    reader = csv.DictReader(StringIO(csv_text.lstrip("\ufeff")), strict=True)
    try:
        headers = reader.fieldnames or []
        if set(headers) != CSV_COLUMNS or len(headers) != len(CSV_COLUMNS):
            frappe.throw(_("Use the Customer 360 intake CSV template."))
        rows = list(reader)
    except csv.Error:
        frappe.throw(_("The source CSV is malformed."))
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        frappe.throw(_("Each CSV row must have the same columns as the header."))
    return process_records(rows)


@frappe.whitelist(methods=["POST"])
def resolve_record(source_document, customer, reason):
    _require(DOCTYPE, "write")
    lock_customer_identity_writes()
    record = frappe.get_doc(DOCTYPE, source_document, for_update=True)
    record.check_permission("read")
    record.check_permission("write")
    if record.processing_status != "Needs Review":
        frappe.throw(_("Only records awaiting identity review can be resolved."))
    target = frappe.get_doc(CUSTOMER, customer, for_update=True)
    target.check_permission("read")
    target.check_permission("write")
    if target.get("merged_into"):
        frappe.throw(_("Choose the current customer profile. This profile was merged."))
    reason = _text(reason, 1000)
    if not reason:
        frappe.throw(_("Enter the reason for linking this source record."))

    record.flags.processing_intake = True
    record.customer = target.name
    record.processing_status = "Linked"
    record.result_reason = _("Linked after identity review.")
    record.review_reason = reason
    record.reviewed_by = frappe.session.user
    record.reviewed_at = now_datetime()
    record.save()
    return _result(record)
