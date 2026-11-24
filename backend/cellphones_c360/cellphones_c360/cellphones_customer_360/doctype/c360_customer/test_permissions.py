from uuid import uuid4

import frappe
from frappe.client import get as get_record, set_value
from frappe.tests.utils import FrappeTestCase
from crm.api import check_app_permission
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request, Response

from cellphones_c360.api.access import InvalidTransition, sanitize_api_error
from cellphones_c360.api.administration import get_access as get_administration_access
from cellphones_c360.api.after_sales import list_tickets, record_demo_proposal
from cellphones_c360.api.analytics import get_analytics_overview
from cellphones_c360.api.customer360 import get_customer_360, get_customer_timeline, list_customers
from cellphones_c360.api.customers import get_access
from cellphones_c360.api.employee_administration import set_employee_role
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
        with self.assertRaises(frappe.DoesNotExistError) as outside:
            get_customer_360(customer.name)
        with self.assertRaises(frappe.DoesNotExistError) as missing:
            get_customer_360(f"CUST-{uuid4().hex}")
        self.assertEqual(str(outside.exception), str(missing.exception))
        path = "/api/resource/C360 Customer"
        bodies = []
        for name, status in ((customer.name, 403), ("absent-customer", 404)):
            request = Request(EnvironBuilder(path=f"{path}/{name}").get_environ())
            response = Response('{"exception":"Traceback with internal identifier"}',
                                mimetype="application/json", status=status)
            sanitize_api_error(request, response)
            self.assertEqual(response.status_code, 404)
            self.assertNotIn(name, response.get_data(as_text=True))
            bodies.append(response.get_json())
        self.assertEqual(*bodies)
        with self.assertRaises(frappe.DoesNotExistError):
            get_customer_timeline(customer.name)
        frappe.set_user(manager)
        self.assertTrue(check_app_permission())
        self.assertEqual(get_customer_360(customer.name)["customer"]["name"], customer.name)
        self.assertEqual(set_value(customer.doctype, customer.name, {
            "customer_name": "Manager edited demo",
        }).customer_name, "Manager edited demo")
        self.assertIn("customers", get_analytics_overview())
        with self.assertRaises(frappe.PermissionError):
            set_employee_role(manager, "Administrator")

    def test_department_assignment_and_field_permissions(self):
        ops, service, marketing = self.user(OPERATIONS), self.user(SERVICE), self.user(MARKETING)
        self.assertTrue(frappe.db.exists("Role Profile", OPERATIONS))
        assigned = self.customer(email=self.email, phone_number="0900003124", marketing_consent=1)
        outside = self.customer()
        order = frappe.get_doc({
            "doctype": "Customer Order", "customer": assigned.name, "sales_channel": "Store",
            "fulfillment_owner": ops, "items": [{"product_name": "C360 Demo item", "quantity": 1, "unit_price": 20}],
        }).insert()
        order.update({
            "order_status": "Confirmed", "payment_method": "COD", "fulfillment_method": "Delivery",
        }).save()
        outside_order = frappe.get_doc({
            "doctype": "Customer Order", "customer": outside.name, "sales_channel": "Store",
            "items": [{"product_name": "Unassigned item", "quantity": 1, "unit_price": 30}],
        }).insert()
        ticket = frappe.get_doc({
            "doctype": "Customer Support Ticket", "customer": assigned.name, "ticket_type": "Other",
            "subject": "C360 Permission Ticket", "description": "Synthetic request", "assigned_to": service,
            "related_order": order.name,
        }).insert()
        frappe.set_user(ops)
        self.assertTrue(check_app_permission())
        self.assertEqual({row.name for row in list_orders()["items"]}, {order.name})
        self.assertIsNone(get_customer_360(assigned.name)["customer"]["email"])
        private_fields = get_record(assigned.doctype, assigned.name)
        self.assertFalse(private_fields.get("email"))
        self.assertFalse(private_fields.get("phone_number"))
        self.assertIsNone(list_customers(search=assigned.name)["items"][0]["phone_masked"])
        self.assertEqual(list_customers(search=self.email)["total"], 0)
        with self.assertRaises(frappe.DoesNotExistError):
            get_customer_360(outside.name)
        order.reload()
        form_data = frappe.parse_json(frappe.as_json(order.as_dict()))
        form_data.update({
            "order_status": "Processing",
            "fulfillment_status": "Preparing",
        })
        updated = frappe.get_doc(form_data).save()
        self.assertEqual((updated.order_status, updated.fulfillment_status), ("Processing", "Preparing"))
        with self.assertRaises(InvalidTransition):
            set_value(order.doctype, order.name, {"order_status": "Draft"})
        request = Request(EnvironBuilder(path=f"/api/resource/Customer Order/{order.name}").get_environ())
        response = Response("{}", mimetype="application/json", status=InvalidTransition.http_status_code)
        sanitize_api_error(request, response)
        self.assertEqual(response.get_json()["exc_type"], "InvalidTransition")
        item = order.items[0].as_dict()
        prohibited = {
            "payment_method": "Direct",
            "payment_status": "Paid",
            "fulfillment_method": "Pickup",
            "fulfillment_owner": service,
            "total_amount": 1000,
            "items": [{**item, "quantity": 2, "unit_price": 50}],
        }
        for field, value in prohibited.items():
            with self.subTest(field=field), self.assertRaises(frappe.PermissionError):
                set_value(order.doctype, order.name, {field: value})
        with self.assertRaises(frappe.PermissionError):
            set_value(order.doctype, order.name, {"items": [{**item, "creation": "2000-01-01 00:00:00"}]})
        with self.assertRaises(frappe.PermissionError):
            set_value(outside_order.doctype, outside_order.name, {"order_status": "Cancelled"})
        self.assertFalse(frappe.has_permission(outside_order.doctype, "read", doc=outside_order))

        frappe.set_user(service)
        self.assertTrue(check_app_permission())
        self.assertEqual({row.name for row in list_tickets()["items"]}, {ticket.name})
        self.assertEqual(get_customer_360(assigned.name)["customer"]["email"], self.email)
        with self.assertRaises(frappe.DoesNotExistError):
            get_customer_360(outside.name)

        frappe.set_user(marketing)
        self.assertTrue(check_app_permission())
        self.assertIsNone(get_customer_360(assigned.name)["customer"]["email"])
        self.assertTrue(record_demo_proposal(assigned.name, "Synthetic approved proposal")["comment"])
        with self.assertRaises(frappe.DoesNotExistError):
            get_customer_360(outside.name)
        with self.assertRaises(frappe.PermissionError):
            list_orders()
        frappe.set_user("Administrator")
        assigned.reload()
        assigned.marketing_consent = 0
        assigned.save()
        frappe.set_user(marketing)
        self.assertEqual(list_customers(search=assigned.name)["total"], 0)
        with self.assertRaises(frappe.DoesNotExistError):
            record_demo_proposal(assigned.name, "Synthetic withdrawn consent")
        with self.assertRaises(frappe.DoesNotExistError):
            get_customer_timeline(assigned.name)
        frappe.set_user("Guest")
        self.assertFalse(check_app_permission())
        with self.assertRaises(frappe.PermissionError):
            get_customer_360(assigned.name)

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
