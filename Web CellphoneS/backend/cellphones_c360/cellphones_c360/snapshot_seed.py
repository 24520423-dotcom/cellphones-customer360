"""Import additive, idempotent SYNTHETIC demo-v2 into a Frappe TEST site.

No HTTP endpoint. Only bench execute with Administrator. No real user accounts,
passwords or emails are created/sent. Dry-run only reads database and CSV.
Use only after making a site backup; this is NOT a MariaDB snapshot/restore.
"""
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import csv
import hashlib
import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from cellphones_c360.api.intake import _process, _source_key
from cellphones_c360.cv2_utils import normalize_email, normalize_phone

SNAP = "cellphones-c360-demo-v2"
ACK = "IMPORT_SYNTHETIC_DEMO_V2"
MARK = "custom_cv2_snapshot_key"
DOCTYPE_FILES = {
    "CRM Lead": "leads.csv", "CRM Deal": "deals.csv",
    "Customer Order": "orders.csv", "Customer Support Ticket": "tickets.csv",
    "C360 Registration Request": "registration_requests.csv",
}
FILES = ["customers.csv", "intakes.csv", "leads.csv", "deals.csv",
         "orders.csv", "order_items.csv", "tickets.csv", "registration_requests.csv"]


def load_data(folder):
    root = Path(folder)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("snapshot_id") != SNAP or manifest.get("data_type") != "synthetic_demo":
        raise ValueError("Snapshot ID/type not recognized")
    if set(manifest.get("import_order", [])) != set(FILES):
        raise ValueError("Missing snapshot CSV in manifest")
    data = {}
    for filename in FILES:
        path = root / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["files"][filename]["sha256"]:
            raise ValueError("Checksum mismatch: " + filename)
        with path.open(newline="", encoding="utf-8-sig") as file:
            data[filename] = list(csv.DictReader(file))
        rows = data[filename]
        if len(rows) != manifest["files"][filename]["record_count"]:
            raise ValueError("Wrong row count: " + filename)
        keys = [r.get("snapshot_id") for r in rows]
        if not all(keys) or len(set(keys)) != len(keys):
            raise ValueError("Duplicate/missing snapshot ID: " + filename)
    idx = {filename: {r["snapshot_id"]: r for r in rows}
           for filename, rows in data.items()}
    for filename in ("intakes.csv", "leads.csv", "deals.csv", "orders.csv", "tickets.csv"):
        for r in data[filename]:
            cid = r.get("customer_snapshot_id")
            if cid and cid not in idx["customers.csv"]:
                raise ValueError("Unknown Customer in " + filename)
            if filename not in ("intakes.csv",) and not cid:
                raise ValueError("Missing Customer in " + filename)
    for r in data["deals.csv"]:
        lead = idx["leads.csv"].get(r["lead_snapshot_id"])
        if not lead or lead["customer_snapshot_id"] != r["customer_snapshot_id"]:
            raise ValueError("Deal/Lead Customer mismatch")
    for r in data["tickets.csv"]:
        order_id = r.get("order_snapshot_id")
        if order_id and (order_id not in idx["orders.csv"] or
                         idx["orders.csv"][order_id]["customer_snapshot_id"] != r["customer_snapshot_id"]):
            raise ValueError("Ticket/Order Customer mismatch")
    items = defaultdict(list)
    for r in data["order_items.csv"]:
        if r["order_snapshot_id"] not in idx["orders.csv"]:
            raise ValueError("Orphan Order Item")
        qty, price, total = int(r["quantity"]), Decimal(r["unit_price"]), Decimal(r["amount"])
        if qty < 1 or price < 0 or qty * price != total:
            raise ValueError("Order Item amount mismatch")
        items[r["order_snapshot_id"]].append(r)
    for r in data["orders.csv"]:
        subset = items[r["snapshot_id"]]
        if not subset or sum((Decimal(i["amount"]) for i in subset), Decimal(0)) != Decimal(r["total_amount"]):
            raise ValueError("Order total mismatch")
    if len({(r["source_channel"], r["source_reference"]) for r in data["intakes.csv"]}) != len(data["intakes.csv"]):
        raise ValueError("Duplicate source reference in Intake")
    return data, items


def require_site():
    if frappe.session.user != "Administrator":
        frappe.throw("DEMO import requires Administrator", frappe.PermissionError)
    if not {"frappe", "crm", "cellphones_c360"}.issubset(set(frappe.get_installed_apps())):
        raise ValueError("Install frappe, crm and cellphones_c360 first")
    for dt in ("C360 Customer", "C360 Customer Intake", "Customer Order Item", *DOCTYPE_FILES):
        if not frappe.db.exists("DocType", dt):
            raise ValueError("Missing DocType: " + dt)
    currency = frappe.db.get_single_value("FCRM Settings", "currency") or "USD"
    if currency != "VND":
        raise ValueError(f"Site FCRM Settings.currency={currency}; set currency to VND on a TEST site before importing VND demo amounts")
    for reason in ("Pricing", "Competition", "Budget Constraints", "Poor Fit", "Unresponsive Prospect"):
        if not frappe.db.exists("CRM Lost Reason", reason):
            raise ValueError(f"Missing CRM Lost Reason {reason} from CRM defaults")
    for dt in ("CRM Lead", "CRM Deal"):
        if not frappe.get_meta(dt).has_field("custom_c360_customer"):
            raise ValueError("CV2 custom_c360_customer missing on " + dt)
    for dt, states in (("CRM Lead Status", {"New", "Contacted", "Qualified", "Nurture", "Converted", "Unqualified", "Junk"}),
                       ("CRM Deal Status", {"Qualification", "Demo/Making", "Proposal/Quotation", "Negotiation", "Ready to Close", "Won", "Lost"})):
        missing = [x for x in states if not frappe.db.exists(dt, x)]
        if missing:
            raise ValueError(f"Missing statuses in {dt}: {missing}")


def find_saved(doctype, marker):
    if not frappe.get_meta(doctype).has_field(MARK):
        return None
    return frappe.db.get_value(doctype, {MARK: marker}, "name")


def add_markers():
    fields = {}
    for dt in DOCTYPE_FILES:
        if not frappe.get_meta(dt).has_field(MARK):
            fields[dt] = [{"fieldname": MARK, "label": "CV2 DEMO Snapshot Key",
                           "fieldtype": "Data", "unique": 1, "hidden": 1,
                           "read_only": 1, "description": "Internal demo import ID"}]
    if fields:
        create_custom_fields(fields, update=True)
        for dt in fields:
            frappe.clear_cache(doctype=dt)


def collisions(data):
    base = {r["snapshot_id"]: r for r in data["customers.csv"]}
    errors = []
    for r in data["intakes.csv"]:
        if r["expected_action"] != "new":
            continue
        key = _source_key(r["source_channel"], r["source_reference"])
        existing = frappe.db.get_value("C360 Customer Intake", {"source_key": key}, "customer")
        c = base[r["customer_snapshot_id"]]
        if existing:
            old = frappe.db.get_value("C360 Customer", existing, ["phone_number", "email"], as_dict=True)
            if not old or normalize_phone(old.phone_number) != normalize_phone(c["phone_number"]) or normalize_email(old.email) != normalize_email(c["email"]):
                errors.append("Existing Snapshot Intake has different Customer: " + r["source_reference"])
            continue
        found = (frappe.db.get_value("C360 Customer", {"phone_number": c["phone_number"]}, "name") or
                 frappe.db.get_value("C360 Customer", {"email": c["email"]}, "name"))
        if found:
            errors.append(f"Identity already belongs to {found}: {r['customer_snapshot_id']}")
    return errors


def add_doc(doctype, r, fields, mapping, counts):
    existing = find_saved(doctype, r["snapshot_id"])
    if existing:
        mapping[r["snapshot_id"]] = existing
        counts["already_imported"] += 1
        return existing
    fields[MARK] = r["snapshot_id"]
    created = frappe.get_doc({"doctype": doctype, **fields}).insert(ignore_permissions=True)
    mapping[r["snapshot_id"]] = created.name
    counts["created"] += 1
    return created.name


def ensure_lead_sources():
    """Add missing demo channel choices to CRM's lookup table, not to users."""
    if not frappe.db.exists("DocType", "CRM Lead Source"):
        return
    for channel in ("Website", "App", "Facebook", "Zalo", "Hotline", "Store"):
        if not frappe.db.exists("CRM Lead Source", channel):
            frappe.get_doc({"doctype": "CRM Lead Source", "source_name": channel}).insert(ignore_permissions=True)


def lead_source_is_allowed(channel):
    f = frappe.get_meta("CRM Lead").get_field("source")
    if not f:
        return False
    if f.fieldtype == "Link":
        return bool(f.options and frappe.db.exists(f.options, channel))
    if f.fieldtype == "Select":
        return channel in (f.options or "").split("\n")
    return f.fieldtype == "Data"


def perform(data, items):
    maps = {kind: {} for kind in ("customer", "lead", "deal", "order", "ticket", "registration")}
    totals = {filename: Counter() for filename in FILES if filename != "order_items.csv"}
    fresh_customers = set()
    for r in data["intakes.csv"]:
        res = _process(r["customer_name"], r["phone_number"], r["email"],
                       r["source_channel"], r["source_reference"], r["received_at"], dry_run=False)
        outcome, expected = res["action"], r["expected_action"]
        required_status = {"new": "Created", "linked": "Linked", "review": "Needs Review", "rejected": "Rejected"}[expected]
        if outcome == "already_imported":
            if res["status"] != required_status:
                raise ValueError("Existing Intake was reviewed/changed: " + r["source_reference"])
            totals["intakes.csv"]["already_imported"] += 1
        elif outcome == expected:
            totals["intakes.csv"][outcome] += 1
            if expected == "new":
                fresh_customers.add(r["customer_snapshot_id"])
        else:
            raise ValueError(f"Decision mismatch for {r['source_reference']}: wanted {expected}, got {outcome}")
        cid = r.get("customer_snapshot_id")
        if cid:
            found = res.get("customer_id")
            if not found or (cid in maps["customer"] and maps["customer"][cid] != found):
                raise ValueError("Intake customer mapping mismatch: " + cid)
            maps["customer"][cid] = found
        if expected == "review":
            candidate = res.get("candidate_customer")
            if outcome == "already_imported":
                candidate = frappe.db.get_value("C360 Customer Intake",
                       {"source_key": _source_key(r["source_channel"], r["source_reference"])}, "candidate_customer")
            if candidate != maps["customer"].get(r["candidate_customer_snapshot_id"]):
                raise ValueError("Wrong review candidate for " + r["source_reference"])
    if set(maps["customer"]) != {r["snapshot_id"] for r in data["customers.csv"]}:
        raise ValueError("Customer import not complete")
    for r in data["customers.csv"]:
        doc = frappe.get_doc("C360 Customer", maps["customer"][r["snapshot_id"]])
        if normalize_phone(doc.phone_number) != normalize_phone(r["phone_number"]) or normalize_email(doc.email) != normalize_email(r["email"]):
            raise ValueError("Customer ID changed: " + r["snapshot_id"])
        if r["snapshot_id"] in fresh_customers:
            doc.customer_type = r["customer_type"]
            doc.customer_status = r["customer_status"]
            doc.save(ignore_permissions=True)
    totals["customers.csv"]["available"] = len(maps["customer"])
    for r in data["leads.csv"]:
        words = r["lead_name"].strip().split()
        fields = {"first_name": " ".join(words[:-1]) or words[-1], "status": r["status"],
                  "mobile_no": r["mobile_no"], "email": r["email"],
                  "custom_c360_customer": maps["customer"][r["customer_snapshot_id"]]}
        m = frappe.get_meta("CRM Lead")
        if m.has_field("last_name"):
            fields["last_name"] = words[-1] if len(words)>1 else ""
        if m.has_field("custom_consultation_notes"):
            fields["custom_consultation_notes"] = r["consultation_notes"]
        if r["status"] in ("Unqualified", "Junk") and m.has_field("lost_reason"):
            fields["lost_reason"] = r["lost_reason"]
        if lead_source_is_allowed(r.get("source")):
            fields["source"] = r["source"]
        add_doc("CRM Lead", r, fields, maps["lead"], totals["leads.csv"])
    for r in data["deals.csv"]:
        fields = {"lead": maps["lead"][r["lead_snapshot_id"]],
                  "custom_c360_customer": maps["customer"][r["customer_snapshot_id"]],
                  "status": r["status"]}
        meta = frappe.get_meta("CRM Deal")
        if meta.has_field("expected_deal_value"):
            fields["expected_deal_value"] = float(r["expected_deal_value"])
        if meta.has_field("deal_name"):
            fields["deal_name"] = r["deal_name"]
        if meta.has_field("expected_closure_date"):
            fields["expected_closure_date"] = r["expected_closure_date"]
        if r["status"] == "Lost" and meta.has_field("lost_reason"):
            fields["lost_reason"] = r["lost_reason"]
        if meta.has_field("currency") and frappe.db.exists("Currency", "VND"):
            fields["currency"] = "VND"
        add_doc("CRM Deal", r, fields, maps["deal"], totals["deals.csv"])
    for r in data["orders.csv"]:
        order_items = [{"product_code": it["product_code"], "product_name": it["product_name"],
                        "quantity": int(it["quantity"]), "unit_price": float(it["unit_price"])}
                       for it in items[r["snapshot_id"]]]
        fields = {"customer": maps["customer"][r["customer_snapshot_id"]],
                  "order_date": r["order_date"], "sales_channel": r["sales_channel"],
                  "order_status": r["order_status"], "items": order_items}
        name = add_doc("Customer Order", r, fields, maps["order"], totals["orders.csv"])
        actual = frappe.db.get_value("Customer Order", name, "total_amount")
        if abs(float(actual or 0) - float(r["total_amount"])) > 1:
            raise ValueError("Order total differs: " + r["snapshot_id"])
    for r in data["tickets.csv"]:
        linked = maps["order"].get(r["order_snapshot_id"]) if r.get("order_snapshot_id") else None
        fields = {"customer": maps["customer"][r["customer_snapshot_id"]],
                  "related_order": linked, "subject": r["subject"], "ticket_type": r["ticket_type"],
                  "priority": r["priority"], "ticket_status": r["ticket_status"],
                  "created_date": r["created_date"], "description": r["description"],
                  "resolution": r.get("resolution") or None, "resolved_date": r.get("resolved_date") or None}
        add_doc("Customer Support Ticket", r, fields, maps["ticket"], totals["tickets.csv"])
    for r in data["registration_requests.csv"]:
        if frappe.db.exists("User", r["email"]):
            raise ValueError("Demo registration email already in Frappe User")
        fields = {"full_name": r["full_name"], "email": r["email"],
                  "phone": r["phone"], "department": r["department"],
                  "status": r["status"], "reason": r.get("reason") or None}
        add_doc("C360 Registration Request", r, fields, maps["registration"],
                totals["registration_requests.csv"])
    return totals, maps


def import_demo_v2(folder, dry_run=True, confirm=None):
    """CLI entrypoint; not whitelisted over HTTP."""
    frappe.set_user("Administrator")
    require_site()
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in {"true", "1", "yes"}
    data, items = load_data(folder)
    issues = collisions(data)
    if issues:
        return {"ok": False, "dry_run": bool(dry_run), "issues": issues[:20],
                "hint": "Use a separate clean test site; do not merge with real customers"}
    counts = {name: len(data[name]) for name in FILES}
    if dry_run:
        existing = {filename: sum(bool(find_saved(dt, r["snapshot_id"])) for r in data[filename])
                    for dt, filename in DOCTYPE_FILES.items()}
        existing["intakes.csv"] = sum(bool(frappe.db.exists(
            "C360 Customer Intake", {"source_key": _source_key(r["source_channel"], r["source_reference"])}))
            for r in data["intakes.csv"])
        return {"ok": True, "dry_run": True, "snapshot_id": SNAP,
                "counts": counts, "already_imported": existing, "writes": 0,
                "note": "Only preflight checks; runtime Frappe validations still require a test import"}
    if confirm != ACK:
        raise ValueError(f"For real import set confirm={ACK}, after backing up your TEST site")
    try:
        add_markers()
        ensure_lead_sources()
        totals, maps = perform(data, items)
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        raise
    return {"ok": True, "dry_run": False, "snapshot_id": SNAP,
            "totals": {k: dict(v) for k, v in totals.items()},
            "sample_customer_ids": list(maps["customer"].items())[:5],
            "note": "Added demo records to this site only; other machines are not synchronized"}


def verify_demo_v2(folder):
    """Read-only marker audit following import."""
    frappe.set_user("Administrator")
    require_site()
    data, _ = load_data(folder)
    found = {filename: sum(bool(find_saved(dt, r["snapshot_id"])) for r in data[filename])
             for dt, filename in DOCTYPE_FILES.items()}
    found["intakes.csv"] = sum(bool(frappe.db.exists(
        "C360 Customer Intake", {"source_key": _source_key(r["source_channel"], r["source_reference"])}))
        for r in data["intakes.csv"])
    return {"found": found, "expected": {k: len(v) for k, v in data.items()},
            "note": "Customer record IDs are mapped through first Intake; confirm UI/API separately"}
