"""CV2-02/03: idempotent customer intake, duplicate review, CSV import.

All HTTP endpoints require a signed-in System Manager. They are not open lead
capture endpoints; external channel webhooks need separate authentication.
"""
import csv
import hashlib
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from cellphones_c360.cv2_utils import CHANNELS, decide_match, validate_identity

INTAKE = "C360 Customer Intake"
CUSTOMER = "C360 Customer"


def _require_operator():
    user = frappe.session.user
    if user in (None, "", "Guest") or (user != "Administrator" and "System Manager" not in frappe.get_roles(user)):
        frappe.throw(_("Chỉ System Manager được tiếp nhận và đối chiếu danh tính khách hàng."), frappe.PermissionError)


def _source_key(channel, reference):
    return hashlib.sha256(f"{channel}\0{reference}".encode("utf-8")).hexdigest()


def _find_candidates(identity):
    conditions = []
    if identity["phone_number"]:
        conditions.append(["phone_number", "=", identity["phone_number"]])
    if identity["email"]:
        conditions.append(["email", "=", identity["email"]])
    # get_all intentionally bypasses row permissions here, only after _require_operator.
    return frappe.get_all(
        CUSTOMER, or_filters=conditions,
        fields=["name", "customer_name", "phone_number", "email"],
        limit_page_length=0,
    )


def _process(name, phone, email, channel, reference, received_at, *, dry_run=False, virtual_candidates=None):
    _require_operator()
    channel, reference = str(channel or "").strip(), str(reference or "").strip()
    if channel not in CHANNELS:
        frappe.throw(_("Source channel không hợp lệ."), frappe.ValidationError)
    if not reference or len(reference) > 120:
        frappe.throw(_("Cần source_reference dài tối đa 120 ký tự."), frappe.ValidationError)
    received = get_datetime(received_at) if received_at else now_datetime()
    if not received:
        frappe.throw(_("received_at không hợp lệ."), frappe.ValidationError)

    key = _source_key(channel, reference)
    previous = frappe.db.get_value(INTAKE, {"source_key": key}, ["name", "status", "customer"], as_dict=True)
    if previous:
        return {"action": "already_imported", "intake_id": previous.name,
                "status": previous.status, "customer_id": previous.customer}

    identity = None
    try:
        identity = validate_identity(name, phone, email)
        action, candidate, reason = decide_match(identity, _find_candidates(identity) + (virtual_candidates or []))
    except ValueError as error:
        action, candidate, reason = "rejected", None, str(error)

    if dry_run:
        return {"action": action, "customer_id": candidate if action == "linked" else None,
                "candidate_customer": candidate if action == "review" else None,
                "reason": reason, "source_reference": reference, "dry_run": True}

    customer_id = None
    if action == "new":
        customer_doc = frappe.get_doc({
            "doctype": CUSTOMER,
            **identity,
            "customer_type": "Individual",
            "customer_status": "Active",
            "source_channel": channel,
        })
        customer_doc.insert()
        customer_id = customer_doc.name
    elif action == "linked":
        customer_id = candidate

    intake = frappe.get_doc({
        "doctype": INTAKE,
        "source_key": key,
        "source_channel": channel,
        "source_reference": reference,
        "received_at": received,
        "customer_name": identity["customer_name"] if identity else " ".join(str(name or "").split()) or "(thiếu tên)",
        "phone_number": identity["phone_number"] if identity else str(phone or "").strip(),
        "email": identity["email"] if identity else str(email or "").strip(),
        "status": {"new": "Created", "linked": "Linked", "review": "Needs Review", "rejected": "Rejected"}[action],
        "customer": customer_id,
        "candidate_customer": candidate if action == "review" else customer_id,
        "review_reason": reason,
    })
    intake.insert()
    return {"action": action, "intake_id": intake.name, "status": intake.status,
            "customer_id": customer_id, "candidate_customer": candidate if action == "review" else None,
            "reason": reason}


@frappe.whitelist(methods=["POST"])
def ingest_customer(customer_name, source_channel, source_reference, phone_number=None,
                    email=None, received_at=None, dry_run=0):
    """System Manager-only ingestion. Frappe will commit POST on success."""
    return _process(customer_name, phone_number, email, source_channel,
                    source_reference, received_at, dry_run=bool(int(dry_run)))


@frappe.whitelist(methods=["POST"])
def resolve_duplicate(intake_id, customer_id):
    """Manually confirm a pending intake belongs to an existing Customer.

    No automatic merge or overwrite. The operator must verify the evidence.
    """
    _require_operator()
    intake = frappe.get_doc(INTAKE, intake_id)
    intake.check_permission("write")
    if intake.status != "Needs Review":
        frappe.throw(_("Chỉ xử lý bản ghi đang chờ xác minh."), frappe.ValidationError)
    customer = frappe.get_doc(CUSTOMER, customer_id)
    customer.check_permission("read")
    intake.customer = customer.name
    intake.candidate_customer = customer.name
    intake.status = "Linked"
    intake.review_reason = "Đã được System Manager xác minh thủ công."
    intake.reviewed_by = frappe.session.user
    intake.reviewed_at = now_datetime()
    intake.save()
    return {"intake_id": intake.name, "status": intake.status, "customer_id": customer.name}


def import_customer_csv(path, dry_run=True):
    """Trusted site-console/bench executor. The path is inside the Frappe container.

    One transaction per valid row; rejected rows are tracked, errors isolated.
    Errors are returned, not silently ignored. Run with dry_run=True first.
    """
    _require_operator()
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)
    results = []
    virtual_candidates = []  # forecast earlier creates during dry-run only
    seen_keys = set()
    with csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"source_channel", "source_reference", "customer_name", "phone_number", "email", "received_at"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Thiếu cột CSV: {sorted(required - set(reader.fieldnames or []))}")
        for index, row in enumerate(reader, start=2):
            savepoint = f"cv2_row_{index}"
            if not dry_run:
                frappe.db.savepoint(savepoint)
            try:
                key = _source_key(row["source_channel"].strip(), row["source_reference"].strip())
                if dry_run and key in seen_keys:
                    response = {"action": "already_imported", "reason": "Trùng source_reference trong cùng CSV.", "dry_run": True}
                else:
                    response = _process(
                        row["customer_name"], row["phone_number"], row["email"],
                        row["source_channel"], row["source_reference"], row["received_at"],
                        dry_run=dry_run, virtual_candidates=virtual_candidates if dry_run else None,
                    )
                seen_keys.add(key)
                if dry_run and response["action"] == "new":
                    simulated = validate_identity(row["customer_name"], row["phone_number"], row["email"])
                    virtual_candidates.append({"name": f"PREVIEW-{len(virtual_candidates)+1:04d}", **simulated})
                results.append({"row": index, "source_reference": row["source_reference"], **response})
                if not dry_run:
                    frappe.db.commit()
            except Exception as exc:
                if not dry_run:
                    frappe.db.rollback(save_point=savepoint)
                results.append({"row": index, "source_reference": row.get("source_reference"),
                                "action": "error", "reason": str(exc)})
    totals = {}
    for result in results:
        totals[result["action"]] = totals.get(result["action"], 0) + 1
    return {"dry_run": bool(dry_run), "rows": results, "totals": totals}


def import_csv_from_bench(path, dry_run=True):
    """Operator-only CLI entrypoint; not whitelisted over HTTP."""
    frappe.set_user("Administrator")
    return import_customer_csv(path, dry_run=dry_run)
