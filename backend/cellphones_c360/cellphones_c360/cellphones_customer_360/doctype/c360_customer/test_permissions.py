from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from crm.api import check_app_permission

from cellphones_c360.api.administration import get_access as get_administration_access
from cellphones_c360.api.after_sales import list_tickets, record_demo_proposal
from cellphones_c360.api.customer360 import get_customer_360, list_customers
from cellphones_c360.api.customers import get_access
from cellphones_c360.api.merge import preview
from cellphones_c360.api.orders import list_orders
from cellphones_c360.permissions import MARKETING, MERGE_APPROVER, OPERATIONS, SERVICE


class TestC360Permissions(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        self.email = f"c360-permission-{uuid4().hex}@example.test"

    def user(self, *roles):
        return frappe.get_doc({
            "doctype": "User", "email": f"c360-role-{uuid4().hex}@example.test",
            "first_name": "C360 Role Test", "user_type": "System User", "send_welcome_email": 0,
            "roles": [{"role": role} for role in roles],
        }).insert().name

    def customer(self, **values):
        return frappe.get_doc({
            "doctype": "C360 Customer", "customer_name": "C360 Permission Demo", **values,
        }).insert()

    def test_owner_scope_for_sales_user_and_manager(self):
        seller, other, manager = self.user("Sales User"), self.user("Sales User"), self.user("Sales Manager")
        frappe.set_user(seller)
        self.assertTrue(check_app_permission())
        self.assertTrue(get_access()["canCreate"])
        self.assertIn("email", {field["fieldname"] for field in get_access()["fields"]})
        customer = self.customer(email=self.email)
        self.assertEqual(get_customer_360(customer.name)["customer"]["email"], self.email)
        frappe.set_user(other)
        self.assertEqual(list_customers(search=customer.name)["total"], 0)
        with self.assertRaises(frappe.PermissionError):
            get_customer_360(customer.name)
        frappe.set_user(manager)
        self.assertTrue(check_app_permission())
        self.assertEqual(get_customer_360(customer.name)["customer"]["name"], customer.name)

    def test_department_assignment_and_field_permissions(self):
        ops, service, marketing = self.user(OPERATIONS), self.user(SERVICE), self.user(MARKETING)
        self.assertTrue(frappe.db.exists("Role Profile", OPERATIONS))
        assigned = self.customer(email=self.email, marketing_consent=1)
        outside = self.customer()
        order = frappe.get_doc({
            "doctype": "Customer Order", "customer": assigned.name, "sales_channel": "Store",
            "fulfillment_owner": ops, "items": [{"product_name": "C360 Demo item", "quantity": 1, "unit_price": 20}],
        }).insert()
        order.update({
            "order_status": "Confirmed", "payment_method": "COD", "fulfillment_method": "Delivery",
        }).save()
        ticket = frappe.get_doc({
            "doctype": "Customer Support Ticket", "customer": assigned.name, "ticket_type": "Other",
            "subject": "C360 Permission Ticket", "description": "Synthetic request", "assigned_to": service,
            "related_order": order.name,
        }).insert()
        frappe.set_user(ops)
        self.assertTrue(check_app_permission())
        self.assertEqual({row.name for row in list_orders()["items"]}, {order.name})
        self.assertIsNone(get_customer_360(assigned.name)["customer"]["email"])
        self.assertIsNone(list_customers(search=assigned.name)["items"][0]["phone_masked"])
        self.assertEqual(list_customers(search=self.email)["total"], 0)
        with self.assertRaises(frappe.PermissionError):
            get_customer_360(outside.name)
        order.reload().update({"fulfillment_status": "Preparing"}).save()
        with self.assertRaises(frappe.PermissionError):
            order.update({"payment_status": "Paid"}).save()

        frappe.set_user(service)
        self.assertTrue(check_app_permission())
        self.assertEqual({row.name for row in list_tickets()["items"]}, {ticket.name})
        self.assertEqual(get_customer_360(assigned.name)["customer"]["email"], self.email)
        with self.assertRaises(frappe.PermissionError):
            get_customer_360(outside.name)

        frappe.set_user(marketing)
        self.assertTrue(check_app_permission())
        self.assertIsNone(get_customer_360(assigned.name)["customer"]["email"])
        self.assertTrue(record_demo_proposal(assigned.name, "Synthetic approved proposal")["comment"])
        with self.assertRaises(frappe.PermissionError):
            get_customer_360(outside.name)
        with self.assertRaises(frappe.PermissionError):
            list_orders()

    def test_user_permission_allows_first_service_intake(self):
        service = self.user(SERVICE)
        customer = self.customer()
        frappe.get_doc({
            "doctype": "User Permission", "user": service, "allow": "C360 Customer",
            "for_value": customer.name, "apply_to_all_doctypes": 1,
        }).insert()
        frappe.set_user(service)
        self.assertEqual(get_customer_360(customer.name)["customer"]["name"], customer.name)
        ticket = frappe.get_doc({
            "doctype": "Customer Support Ticket", "customer": customer.name, "ticket_type": "Other",
            "subject": "First demo support request", "description": "Synthetic service intake",
        }).insert()
        self.assertIn(ticket.name, {row.name for row in list_tickets(customer=customer.name)["items"]})

    def test_administrator_and_merge_approval(self):
        source = self.customer(email=self.email)
        target = self.customer()
        self.assertTrue(check_app_permission())
        self.assertTrue(get_administration_access()["administration"])
        self.assertTrue(get_access(source.name)["canEdit"])
        self.assertTrue(preview(source.name, target.name)["can_merge"])
        self.assertIn(source.name, {row["customer_id"] for row in list_customers(search=source.name)["items"]})

        ordinary = self.user("Sales Manager")
        approved = self.user("Sales Manager", MERGE_APPROVER)
        administrator = self.user("System Manager")
        frappe.set_user(ordinary)
        self.assertFalse(preview(source.name, target.name)["can_merge"])
        frappe.set_user(approved)
        self.assertTrue(preview(source.name, target.name)["can_merge"])
        frappe.set_user(administrator)
        self.assertTrue(check_app_permission())
        self.assertTrue(get_access(source.name)["canEdit"])
        self.assertTrue(preview(source.name, target.name)["can_merge"])
