import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from cellphones_c360.api.analytics import get_access, get_analytics_overview


class TestCustomerAnalytics(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")

    def test_empty_period_zero_denominator_and_access(self):
        result = get_analytics_overview(from_date="1900-01-01", to_date="1900-01-02")
        self.assertEqual(result["leads"]["total"], 0)
        self.assertEqual(result["orders"]["confirmedReceipts"], 0)
        self.assertIsNone(result["deals"]["winRate"])
        self.assertIsNone(result["tickets"]["resolutionRate"])
        with self.assertRaises(frappe.ValidationError):
            get_analytics_overview(from_date="2026-11-24", to_date="2026-11-01")
        frappe.set_user("Guest")
        self.assertFalse(get_access()["canRead"])
        self.assertTrue(all(value is None for value in get_analytics_overview().values()))

    def test_only_paid_completed_order_counts_as_receipt(self):
        def kpis():
            return get_analytics_overview(from_date=today(), to_date=today())["orders"]

        before = kpis()
        customer = frappe.get_doc({"doctype": "C360 Customer", "customer_name": "Analytics test"}).insert()
        values = {
            "doctype": "Customer Order", "customer": customer.name, "sales_channel": "Store",
            "items": [{"product_name": "Analytics Demo", "quantity": 2, "unit_price": 210000}],
        }
        order = frappe.get_doc(values).insert()
        frappe.get_doc(values).insert()
        order.update({
            "order_status": "Confirmed", "payment_method": "Direct", "fulfillment_method": "Pickup",
        }).save()
        order.update({"order_status": "Processing", "payment_status": "Paid"}).save()
        self.assertEqual(kpis()["confirmedReceipts"], before["confirmedReceipts"])
        order.update({"order_status": "Completed", "fulfillment_status": "Picked Up"}).save()
        after = kpis()
        self.assertEqual(after["confirmedReceipts"] - before["confirmedReceipts"], 420000)
        self.assertEqual(after["validValue"] - before["validValue"], 420000)
        self.assertEqual(after["total"] - before["total"], 2)
