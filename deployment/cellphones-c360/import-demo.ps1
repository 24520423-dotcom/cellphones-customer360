param(
    [string]$Container = "crm-frappe-1",
    [string]$Site = "crm.localhost",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$data = (Resolve-Path (Join-Path $PSScriptRoot "../../data")).Path
$bundle = @{}
foreach ($file in @("customers_online.csv", "customers_offline.csv", "customers_duplicates.csv", "demo-workflows.json")) {
    $bundle[$file] = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $data $file)))
}
$env:C360_DEMO_BUNDLE = $bundle | ConvertTo-Json -Compress
$env:C360_DEMO_SITE = $Site
$env:C360_DEMO_APPLY = if ($Apply) { "1" } else { "0" }
$runner = @'
from base64 import b64decode
from collections import Counter
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import frappe
from cellphones_c360.demo import seed_directory

frappe.init(site=os.environ["C360_DEMO_SITE"])
frappe.connect()
try:
    frappe.set_user("Administrator")
    with TemporaryDirectory(prefix="c360-demo-") as directory:
        for name, payload in json.loads(os.environ["C360_DEMO_BUNDLE"]).items():
            Path(directory, name).write_bytes(b64decode(payload))
        result = seed_directory(directory)
        replay = seed_directory(directory)
        if result["scenarios"] != replay["scenarios"] or not all(
            row["replay"] for receipt in replay["receipts"].values() for row in receipt["items"]
        ):
            raise RuntimeError("Demo replay returned different records")
    for name, receipt in result["receipts"].items():
        print(name, dict(Counter(row["status"] for row in receipt["items"])))
    print("Workflow records:", len(result["scenarios"]))
    print("Demo employee roles available:", sum(row["available_role"] for row in result["employees"]))
    if os.environ["C360_DEMO_APPLY"] == "1":
        frappe.db.commit()
        print("Demo applied.")
    else:
        frappe.db.rollback()
        print("Trial and replay passed. Database changes rolled back.")
finally:
    frappe.db.rollback()
    frappe.destroy()
'@
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($runner))
try {
    & docker exec -u frappe -w /home/frappe/frappe-bench/sites -e C360_DEMO_BUNDLE -e C360_DEMO_SITE -e C360_DEMO_APPLY $Container bash -c "echo $encoded | base64 -d | ../env/bin/python -"
    if ($LASTEXITCODE -ne 0) { throw "Demo import failed with code $LASTEXITCODE." }
} finally {
    Remove-Item Env:C360_DEMO_BUNDLE, Env:C360_DEMO_SITE, Env:C360_DEMO_APPLY -ErrorAction SilentlyContinue
}
