import json
from pathlib import Path

import frappe
from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

from cellphones_c360.api import crm_links, intake
from cellphones_c360.care import create_for_order
from cellphones_c360.cellphones_customer_360.doctype.c360_source_record.c360_source_record import source_key
from cellphones_c360.permissions import DEPARTMENTS


def _customer(scenario):
    name = source_key(scenario["channel"], scenario["source_record_id"])
    customer = frappe.db.get_value(intake.DOCTYPE, name, "customer")
    doc = frappe.get_doc(intake.CUSTOMER, customer)
    if not doc.email or not doc.email.endswith("@example.test") or doc.get("merged_into"):
        frappe.throw("Demo workflow requires an active synthetic customer.")
    return doc


def _sales(customer, lessons):
    results = []
    for row in lessons:
        email = row["email"]
        if not email.endswith("@example.test"):
            frappe.throw("Demo Lead requires an example.test address.")
        existing = crm_links.related_records(customer.reload())["CRM Lead"]
        lead = next((doc.name for doc in existing if doc.email == email), None)
        if not lead:
            status = frappe.db.get_value("CRM Lead Status", {"type": "Open"}, "name", order_by="position")
            lead = crm_links.create_linked_lead(customer.name, {
                "first_name": row["first_name"], "email": email, "status": status,
            })["name"]
        deal = None
        if row.get("deal_type"):
            deal = frappe.db.get_value("CRM Deal", {"lead": lead}, "name")
            if not deal:
                deal = convert_to_deal(lead=lead, if_converted="Return Existing")
                doc = frappe.get_doc("CRM Deal", deal)
                status = frappe.db.get_value("CRM Deal Status", {"type": row["deal_type"]}, "name", order_by="position")
                if not status:
                    frappe.throw("Required demo Deal stage is missing.")
                if doc.status != status:
                    doc.status = status
                    if row["deal_type"] == "Lost":
                        reason = frappe.db.get_value("CRM Lost Reason", {}, "name", order_by="name")
                        if not reason:
                            reason = frappe.get_doc({
                                "doctype": "CRM Lost Reason", "lost_reason": row["lost_reason"],
                            }).insert().name
                        doc.lost_reason = reason
                        doc.lost_notes = row["lost_notes"]
                    doc.save()
        results.append({"lead": lead, "deal": deal})
    return results


def _orders(customer, sales, entries):
    orders = {}
    for row in entries:
        key = row["key"]
        if not key.startswith("DEMO-"):
            frappe.throw("A demo order requires a DEMO- reference.")
        parents = frappe.get_all("Customer Order Item", filters={
            "product_code": key, "parenttype": "Customer Order", "parentfield": "items",
        }, pluck="parent")
        if parents:
            order = frappe.get_doc("Customer Order", parents[0])
            if len(parents) != 1 or order.customer != customer.name:
                frappe.throw("Demo order reference is already assigned elsewhere.")
        else:
            deal = sales[row["deal_index"]]["deal"] if "deal_index" in row else None
            order = frappe.get_doc({
                "doctype": "Customer Order", "customer": customer.name,
                "order_date": row["order_date"], "sales_channel": row["sales_channel"],
                "crm_deal": deal,
                "items": [{"product_code": key, **row["item"]}],
            }).insert()
            if row["outcome"] != "Draft":
                order.update({
                    "order_status": "Confirmed", "payment_method": row["payment_method"],
                    "fulfillment_method": row["fulfillment_method"],
                }).save()
                order.update({"order_status": "Processing", "fulfillment_status": row["processing_status"]}).save()
                order.update({
                    "order_status": row["outcome"], "fulfillment_status": row["fulfillment_status"],
                    "payment_status": row["payment_status"],
                }).save()
        orders[key] = order.name
        if order.order_status == "Completed":
            create_for_order(order.name)
    return orders


def _support(customer, orders, entries):
    tickets = []
    for row in entries:
        subject = row["subject"]
        if not subject.startswith("DEMO "):
            frappe.throw("A demo Ticket requires a DEMO subject.")
        name = frappe.db.get_value("Customer Support Ticket", {
            "customer": customer.name, "subject": subject,
        }, "name")
        if not name:
            ticket = frappe.get_doc({
                "doctype": "Customer Support Ticket", "subject": subject, "customer": customer.name,
                "related_order": orders.get(row.get("order")), "ticket_type": row["type"],
                "description": row["description"],
            }).insert()
            if row.get("resolution"):
                ticket.update({"assigned_to": "Administrator", "ticket_status": "In Progress"}).save()
                ticket.update({"ticket_status": "Resolved", "resolution": row["resolution"]}).save()
                ticket.update({"ticket_status": "Closed"}).save()
            name = ticket.name
        tickets.append(name)
    return tickets


def _employees(entries):
    results = []
    for item in entries:
        if not item["email"].endswith("@example.test") or item["role"] not in ("Sales User", "Sales Manager", *DEPARTMENTS):
            frappe.throw("Demo employees require an example.test address and a supported demo role.")
        if frappe.db.exists("Role", item["role"]) and not frappe.db.exists("User", item["email"]):
            frappe.get_doc({
                "doctype": "User", "email": item["email"], "first_name": item["first_name"],
                "enabled": 0, "user_type": "System User", "send_welcome_email": 0,
                "roles": [{"role": item["role"]}],
            }).insert()
        results.append({"email": item["email"], "available_role": bool(frappe.db.exists("Role", item["role"]))})
    return results


def seed_directory(directory):
    if frappe.session.user != "Administrator":
        frappe.throw("Run this demo seed from the administration console.", frappe.PermissionError)
    directory = Path(directory)
    files = ("customers_online.csv", "customers_offline.csv", "customers_duplicates.csv")
    receipts = {name: intake.process_csv((directory / name).read_text(encoding="utf-8")) for name in files}
    created = {
        row["customer"] for response in receipts.values() for row in response["items"]
        if row["status"] == "Created" and not row["replay"]
    }
    workflow = json.loads((directory / "demo-workflows.json").read_text(encoding="utf-8"))
    scenarios = []
    for scenario in workflow["customers"]:
        customer = _customer(scenario)
        if customer.name in created and scenario.get("marketing_consent"):
            customer.marketing_consent = 1
            customer.save()
        sales = _sales(customer, scenario.get("leads", []))
        orders = _orders(customer, sales, scenario.get("orders", []))
        tickets = _support(customer, orders, scenario.get("tickets", []))
        scenarios.append({"customer": customer.name, "sales": sales, "orders": orders, "tickets": tickets})
    return {"receipts": receipts, "scenarios": scenarios, "employees": _employees(workflow["staff"])}
