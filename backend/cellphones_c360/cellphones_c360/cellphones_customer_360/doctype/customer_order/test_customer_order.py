# Copyright (c) 2026, CellphoneS CRM Team and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from cellphones_c360.api.orders import list_orders


class TestCustomerOrder(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        self.customer = frappe.get_doc({
            "doctype": "C360 Customer", "customer_name": f"C360 Order Test {uuid4().hex[:10]}",
        }).insert()

    def order(self, **updates):
        return frappe.get_doc({
            "doctype": "Customer Order", "customer": self.customer.name, "sales_channel": "Store",
            "items": [{"product_name": "Demo accessory", "quantity": 2, "unit_price": 120000}],
            "total_amount": 1,
            **updates,
        })

    def test_pickup_payment_and_filters(self):
        order = self.order().insert()
        self.assertEqual(order.total_amount, 240000)
        order.update({
            "order_status": "Confirmed", "payment_method": "Direct", "fulfillment_method": "Pickup",
        }).save()
        order.update({
            "order_status": "Processing", "payment_status": "Paid", "fulfillment_status": "Ready for Pickup",
        }).save()
        self.assertTrue(order.paid_at)
        order.order_status = "Completed"
        with self.assertRaises(frappe.ValidationError):
            order.save()
        order.reload().update({"order_status": "Completed", "fulfillment_status": "Picked Up"}).save()
        self.assertTrue(order.completed_at)
        results = list_orders(
            search=self.customer.customer_name, status="Completed", channel="Store", from_date=today(), to_date=today(),
        )
        self.assertEqual([row.name for row in results["items"]], [order.name])
        self.assertEqual(results["items"][0].payment_status, "Paid")
        order.items[0].unit_price = 1
        with self.assertRaises(frappe.ValidationError):
            order.save()

    def test_failed_cod_delivery_and_invalid_order(self):
        for quantity, unit_price in ((0, 100), (1.5, 100), (1, -100), (1, "invalid")):
            with self.subTest(quantity=quantity, unit_price=unit_price), self.assertRaises(frappe.ValidationError):
                self.order(items=[{"product_name": "Demo", "quantity": quantity, "unit_price": unit_price}]).insert()
        with self.assertRaises(frappe.ValidationError):
            self.order(order_status="Completed").insert()

        order = self.order().insert()
        order.update({
            "order_status": "Confirmed", "payment_method": "COD", "fulfillment_method": "Delivery",
        }).save()
        order.update({"order_status": "Processing", "fulfillment_status": "In Transit"}).save()
        order.update({"order_status": "Cancelled", "fulfillment_status": "Failed"}).save()
        self.assertEqual(order.reload().payment_status, "Unpaid")
        self.assertFalse(order.completed_at)
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            list_orders()
