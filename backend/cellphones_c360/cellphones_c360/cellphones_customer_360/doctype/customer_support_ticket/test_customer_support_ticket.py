# Copyright (c) 2026, CellphoneS CRM Team and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, get_datetime

from cellphones_c360.api.after_sales import list_tickets, record_demo_proposal
from cellphones_c360.care import create_for_order


class TestCustomerSupportTicket(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        self.customer = frappe.get_doc({
            "doctype": "C360 Customer", "customer_name": f"Support Test {uuid4().hex[:10]}",
        }).insert()
        self.order = frappe.get_doc({
            "doctype": "Customer Order", "customer": self.customer.name, "sales_channel": "Store",
            "items": [{"product_name": "Demo unit", "quantity": 1, "unit_price": 250000}],
        }).insert()

    def complete_order(self):
        self.order.update({
            "order_status": "Confirmed", "payment_method": "Direct", "fulfillment_method": "Pickup",
        }).save()
        self.order.update({"order_status": "Processing"}).save()
        self.order.update({
            "order_status": "Completed", "fulfillment_status": "Picked Up", "payment_status": "Paid",
        }).save()

    def ticket(self, **values):
        return frappe.get_doc({
            "doctype": "Customer Support Ticket", "customer": self.customer.name,
            "related_order": self.order.name, "subject": "Synthetic warranty", "ticket_type": "Warranty",
            "description": "Demo after-sales issue", **values,
        })

    def test_warranty_progress_and_dates(self):
        with self.assertRaises(frappe.ValidationError):
            self.ticket().insert()
        self.complete_order()
        ticket = self.ticket().insert()
        with self.assertRaises(frappe.ValidationError):
            ticket.update({"ticket_status": "In Progress"}).save()
        ticket.reload().update({"ticket_status": "In Progress", "assigned_to": "Administrator"}).save()
        with self.assertRaises(frappe.ValidationError):
            ticket.update({"ticket_status": "Resolved"}).save()
        ticket.reload().update({"ticket_status": "Resolved", "resolution": "Verified replacement"}).save()
        self.assertTrue(ticket.resolved_date)
        ticket.update({"ticket_status": "Closed"}).save()
        self.assertEqual([row.name for row in list_tickets(status="Closed", customer=self.customer.name)["items"]],
                         [ticket.name])

        other = frappe.get_doc({"doctype": "C360 Customer", "customer_name": "Other Test Customer"}).insert()
        with self.assertRaises(frappe.ValidationError):
            self.ticket(customer=other.name).insert()

    def test_follow_up_is_due_in_three_days_and_idempotent(self):
        self.assertIsNone(create_for_order(self.order.name))
        self.complete_order()
        task = create_for_order(self.order.name)
        self.assertEqual(task, create_for_order(self.order.name))
        stored = frappe.get_doc("CRM Task", task)
        self.assertEqual(stored.reference_docname, self.order.name)
        self.assertEqual(stored.due_date, get_datetime(add_days(self.order.completed_at, 3)))

    def test_demo_proposal_requires_consent(self):
        with self.assertRaises(frappe.PermissionError):
            record_demo_proposal(self.customer.name, "Demo recommendation")
        self.customer.marketing_consent = 1
        self.customer.save()
        result = record_demo_proposal(self.customer.name, "Demo recommendation")
        self.assertTrue(frappe.db.exists("Comment", result["comment"]))
