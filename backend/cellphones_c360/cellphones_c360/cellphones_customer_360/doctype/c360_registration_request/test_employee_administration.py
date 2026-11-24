from functools import partial
from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.core.doctype.user.user import User
from frappe.tests.utils import FrappeTestCase

from cellphones_c360.api import employee_administration as employees, merge
from cellphones_c360.permissions import MARKETING, MERGE_APPROVER, OPERATIONS, SERVICE
from crm.api import user as native_users
from crm.api.session import get_users


class TestEmployeeAdministration(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        self.prefix = f"c360-employees-{uuid4().hex[:10]}"
        self.addCleanup(self.rollback_fixtures)
        self.enterContext(patch.dict(frappe.flags, {"mute_emails": True}))
        # A native notification can otherwise commit fixtures before FrappeTestCase rolls back.
        self.enterContext(patch.object(
            frappe.db, "commit", side_effect=AssertionError("Unexpected commit in employee administration test"),
        ))

    def rollback_fixtures(self):
        frappe.db.rollback()
        self.assertFalse(frappe.db.exists("User", {"name": ("like", self.prefix + "-%")}))

    def create(self, label, role, *, enabled=False, merge_approver=False):
        return employees.create_employee(
            f"Employee {label}", f"{self.prefix}-{label}@example.test", role, enabled, merge_approver,
        )

    def save(self, account, *, role=None, enabled=None, merge_approver=None):
        return employees.save_employee(
            account["name"], role or account["role"],
            account["enabled"] if enabled is None else enabled,
            account["merge_effective"] if merge_approver is None else merge_approver,
            account["modified"],
        )

    def test_creates_lists_and_filters_each_role(self):
        with patch.object(User, "send_welcome_mail_to_user") as send:
            for index, role in enumerate(employees.PRIMARY_ROLES):
                with self.subTest(role=role):
                    item = self.create(str(index), role, enabled=index % 2 == 0)
                    self.assertEqual(item["role"], role)
                    self.assertEqual(item["enabled"], index % 2 == 0)
                    self.assertFalse(native_users.has_password(item["name"]))
                    roster = employees.list_employees(self.prefix, role=role)
                    self.assertEqual([row.name for row in roster["items"]], [item["name"]])
                    self.assertTrue(roster["items"][0].manageable)
            self.assertEqual(send.call_count, 3)
        self.assertEqual(len(employees.list_employees(self.prefix)["items"]), 6)
        with self.assertRaises(frappe.ValidationError):
            self.create("invalid", "Sales User", merge_approver=True)
        with self.assertRaises(frappe.ValidationError):
            self.create("invalid-role", MERGE_APPROVER)

    def test_updates_access_revokes_sessions_and_changes_crm_bootstrap(self):
        account = self.create("operations", OPERATIONS)
        with patch.object(User, "send_welcome_mail_to_user") as send:
            account = self.save(account, enabled=True)
            send.assert_called_once()
        self.assertEqual(account["invitation"], "queued")
        frappe.set_user(account["name"])
        self.assertEqual(get_users()[1][0].role, OPERATIONS)
        self.assertFalse(merge._has_merge_role())
        frappe.set_user("Administrator")

        with patch.object(employees, "_revoke_sessions") as revoke:
            manager = self.save(account, role="Sales Manager", merge_approver=True)
            revoke.assert_not_called()
            callbacks = [callback for callback in frappe.db.after_commit._functions
                         if isinstance(callback, partial) and callback.func is revoke]
            self.assertEqual(len(callbacks), 1)
            callbacks[0]()
            revoke.assert_called_once_with(account["name"])
        self.assertTrue(manager["merge_effective"])
        frappe.set_user(manager["name"])
        self.assertEqual(next(row.role for row in get_users()[1] if row.name == manager["name"]), "Sales Manager")
        self.assertTrue(merge._has_merge_role())
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.TimestampMismatchError):
            self.save(account, role=MARKETING)
        manager = self.save(manager, merge_approver=False)
        self.assertNotIn(MERGE_APPROVER, frappe.get_roles(manager["name"]))
        self.assertFalse(self.save(manager, enabled=False)["enabled"])

    def test_preserves_assignments_when_disabling_or_changing_role(self):
        with patch.object(User, "send_welcome_mail_to_user"):
            account = self.create("assignee", "Sales Manager", enabled=True)
        name = account["name"]
        customer = frappe.get_doc({"doctype": "C360 Customer", "customer_name": "Synthetic staff assignment"}).insert()
        statuses = frappe.get_list("CRM Deal Status", order_by="position", pluck="name")
        with patch.object(frappe, "sendmail"):
            lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Synthetic Staff", "lead_owner": name}).insert()
            deal = frappe.get_doc({"doctype": "CRM Deal", "organization_name": "Synthetic Staff",
                                   "status": statuses[0], "deal_owner": name}).insert()
        order = frappe.get_doc({
            "doctype": "Customer Order", "customer": customer.name, "sales_channel": "Store",
            "fulfillment_owner": name,
            "items": [{"product_name": "Synthetic item", "quantity": 1, "unit_price": 500}],
        }).insert()
        ticket = frappe.get_doc({
            "doctype": "Customer Support Ticket", "customer": customer.name, "ticket_type": "Other",
            "description": "Synthetic request", "subject": "Synthetic staff assignment", "assigned_to": name,
        }).insert()
        for row, field in zip((lead, deal, order, ticket), ("lead_owner", "deal_owner", "fulfillment_owner", "assigned_to")):
            self.assertEqual(row.get(field), name)
        self.assertEqual(set(employees.get_employee(name)["assignments"].values()), {1})
        self.save(account, role=SERVICE, enabled=False)
        for row, field in zip((lead, deal, order, ticket), ("lead_owner", "deal_owner", "fulfillment_owner", "assigned_to")):
            self.assertEqual(row.reload().get(field), name)

    def test_protects_profiles_administrator_and_old_native_routes(self):
        simple = frappe.get_doc({
            "doctype": "User", "email": f"{self.prefix}-simple@example.test", "first_name": "Simple profile",
            "user_type": "System User", "role_profile_name": OPERATIONS, "send_welcome_email": 0,
        }).insert()
        detail = employees.get_employee(simple.name)
        self.assertTrue(detail["manageable"])
        self.assertEqual(self.save(detail, enabled=False)["role_profile_name"], OPERATIONS)
        self.assertIsNone(self.save(employees.get_employee(simple.name), role=SERVICE)["role_profile_name"])

        profile = frappe.get_doc({
            "doctype": "Role Profile", "role_profile": self.prefix,
            "roles": [{"role": OPERATIONS}, {"role": "Sales User"}],
        }).insert()
        user = frappe.get_doc({
            "doctype": "User", "email": f"{self.prefix}-profile@example.test", "first_name": "Profile test",
            "user_type": "System User", "role_profile_name": profile.name, "send_welcome_email": 0,
        }).insert()
        protected = employees.list_employees(user.email)["items"][0]
        self.assertFalse(protected.manageable)
        for name in (user.name, "Administrator"):
            with self.subTest(name=name), self.assertRaises(frappe.PermissionError):
                employees.set_employee_enabled(name, False)

        approver = self.create("approved", "Sales Manager", merge_approver=True)
        manager = self.create("manager", "Sales Manager")
        seller = self.create("seller", "Sales User")
        marketer = self.create("marketing", MARKETING)
        for actor in (manager, seller, marketer):
            frappe.set_user(actor["name"])
            with self.assertRaises(frappe.PermissionError):
                employees.list_employees()
            with self.assertRaises(frappe.PermissionError):
                employees.set_employee_enabled(seller["name"], False)
        with patch.dict(frappe.flags, {"in_test": False}):
            for actor in (seller, marketer):
                frappe.set_user(actor["name"])
                with self.assertRaises(frappe.PermissionError):
                    native_users.update_user_role(seller["name"], "Sales User")
        frappe.set_user(manager["name"])
        for name, role in ((approver["name"], "Sales User"), (manager["name"], "System Manager")):
            with self.assertRaises(frappe.PermissionError):
                native_users.update_user_role(name, role)
        with self.assertRaises(frappe.PermissionError):
            native_users.remove_crm_roles_from_user(approver["name"])

    def test_handles_invitation_failure_without_exposing_password_material(self):
        with patch.object(User, "send_welcome_mail_to_user", side_effect=frappe.OutgoingEmailError):
            account = self.create("no-mail", SERVICE, enabled=True)
        self.assertEqual(account["invitation"], "failed")
        self.assertTrue(frappe.db.exists("User", account["name"]))
        self.assertNotIn("reset_password_key", account)
        with patch.object(User, "send_welcome_mail_to_user") as send:
            self.assertEqual(employees.invite_employee(account["name"]), {"invitation": "queued"})
            send.assert_called_once()
