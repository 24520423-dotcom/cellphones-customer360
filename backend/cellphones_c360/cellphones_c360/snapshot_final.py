import hashlib
import json
from pathlib import Path
from collections import defaultdict

import frappe


def preflight(folder="/tmp/c360-demo-final-staging/publish_candidate"):
    root = Path(folder)
    manifest = json.loads(
        (root / "manifest.json").read_text(encoding="utf-8")
    )

    for filename, info in manifest["files"].items():
        raw = (root / filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != info["sha256"]:
            raise ValueError("Checksum mismatch: " + filename)

    data = {}

    for filename in [
        "business_data.json",
        "supplementary_data.json"
    ]:
        data.update(json.loads(
            (root / filename).read_text(encoding="utf-8")
        ))

    keys = {
        (dt, str(row["name"]))
        for dt, rows in data.items()
        for row in rows
    }

    keys.update({
        ("User", "Administrator"),
        ("User", "Guest")
    })

    missing = defaultdict(set)
    external = defaultdict(set)
    issues = []

    def check_link(dt, name):
        if not dt or not name:
            return

        name = str(name)

        if (dt, name) in keys:
            return

        if frappe.db.exists(dt, name):
            external[dt].add(name)
        else:
            missing[dt].add(name)

    def check_row(dt, row):
        meta = frappe.get_meta(dt)

        for field in ("owner", "modified_by"):
            check_link("User", row.get(field))

        for f in meta.fields:
            value = row.get(f.fieldname)

            if not value:
                continue

            if f.fieldtype == "Link":
                check_link(f.options, value)

            elif f.fieldtype == "Dynamic Link":
                check_link(row.get(f.options), value)

            elif f.fieldtype in ("Table", "Table MultiSelect"):
                for child in value:
                    check_row(f.options, child)

    for dt, rows in data.items():
        names = [str(row["name"]) for row in rows]

        if len(names) != len(set(names)):
            issues.append(dt + ": duplicate IDs")

        if len(rows) != manifest["record_counts"].get(dt):
            issues.append(dt + ": count mismatch")

        for row in rows:
            check_row(dt, row)

    settings = json.loads(
        (root / "crm_settings.json").read_text(encoding="utf-8")
    )

    return {
        "checksum": "PASS",
        "total_records": sum(len(rows) for rows in data.values()),
        "counts": {dt: len(rows) for dt, rows in data.items()},
        "missing_links": {
            dt: len(v) for dt, v in missing.items()
        },
        "external_references": {
            dt: len(v) for dt, v in external.items()
        },
        "issues": issues,
        "brand_logo": settings.get("brand_logo"),
        "favicon": settings.get("favicon"),
        "ok": not missing and not issues,
        "database_writes": 0,
        "restore_tested": False
    }
