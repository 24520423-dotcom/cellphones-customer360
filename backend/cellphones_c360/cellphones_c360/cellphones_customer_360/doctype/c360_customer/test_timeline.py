from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from cellphones_c360.api import intake
from cellphones_c360.api.customer360 import get_customer_360, get_customer_timeline


class TestCustomerTimeline(FrappeTestCase):
    def test_permission_pagination_history_and_order_metrics(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        customer_id = intake.process_records([{
            "source_channel": "Store", "source_record_id": uuid4().hex, "customer_name": "Timeline Demo",
        }])["items"][0]["customer"]
        customer = frappe.get_doc("C360 Customer", customer_id)
        customer.customer_name = "Updated Timeline Demo"
        customer.save(ignore_version=False)
        order = frappe.get_doc({
            "doctype": "Customer Order", "customer": customer_id, "sales_channel": "Store",
            "items": [{"product_name": "Timeline Demo product", "quantity": 1, "unit_price": 900}],
        }).insert()
        frappe.get_doc({
            "doctype": "FCRM Note", "title": "Timeline Demo note", "content": "Synthetic note",
            "reference_doctype": "C360 Customer", "reference_docname": customer_id,
        }).insert()
        frappe.get_doc({
            "doctype": "CRM Task", "title": "Timeline Demo task", "reference_doctype": "Customer Order",
            "reference_docname": order.name,
        }).insert()
        first = get_customer_timeline(customer_id, page_size=2)
        second = get_customer_timeline(customer_id, page=2, page_size=2)
        complete = get_customer_timeline(customer_id, page_size=100)
        self.assertGreaterEqual(first["total"], 6)
        self.assertEqual(first["items"] + second["items"], complete["items"][:4])
        self.assertTrue({"customer", "intake", "change", "order", "task", "note"}.issubset(
            {event["type"] for event in complete["items"]},
        ))
        self.assertEqual(get_customer_360(customer_id)["summary"], {
            "recorded_order_value": 900, "confirmed_spend": 0,
        })
        with self.assertRaises(frappe.ValidationError):
            get_customer_timeline(customer_id, page=0)
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            get_customer_timeline(customer_id)
