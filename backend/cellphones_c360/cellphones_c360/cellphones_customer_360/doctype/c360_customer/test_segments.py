from datetime import date

import frappe
from frappe.tests.utils import FrappeTestCase

from cellphones_c360.api.customer360 import list_customers
from cellphones_c360.api.segments import summarize


class TestCustomerSegments(FrappeTestCase):
    def test_rfm_counts_verified_purchases(self):
        customer = frappe._dict({"creation": "2026-01-01", "source_channel": "Zalo"})
        orders = [
            frappe._dict(order_status="Completed", payment_status="Paid", paid_at="2026-11-01", total_amount=12_000_000),
            frappe._dict(order_status="Completed", payment_status="Paid", paid_at="2026-11-18", total_amount=9_000_000),
            frappe._dict(order_status="Cancelled", payment_status="Refunded", paid_at="2026-11-17", total_amount=8_000_000),
            frappe._dict(order_status="Draft", payment_status="Unpaid", paid_at=None, total_amount=1_000_000),
        ]
        summary = summarize(customer, orders, has_open_support=True, as_of=date(2026, 11, 24))
        self.assertEqual(set(summary["segments"]), {"current", "online", "returning", "high_value", "open_support"})
        self.assertEqual(summary["rfm"], {"recency_days": 6, "frequency": 2, "monetary": 21_000_000})
        self.assertIsNone(summarize(customer, None)["rfm"])
        self.assertIn("inactive", summarize(customer, [], as_of=date(2026, 11, 24))["segments"])

    def test_permission_aware_offline_filter(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        name = "C360 Segment Offline Test"
        customer = frappe.get_doc({
            "doctype": "C360 Customer", "customer_name": name, "source_channel": "Store",
        }).insert()
        result = list_customers(search=name, segment="offline")
        self.assertEqual([row["customer_id"] for row in result["items"]], [customer.name])
        self.assertIn("offline", result["items"][0]["segments"])
        self.assertEqual(list_customers(search=name, segment="returning")["total"], 0)
