from secrets import randbelow
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils.password import check_password, update_password

from cellphones_c360.api import registration
from cellphones_c360.api.access import require_enabled_api_account
from cellphones_c360.api.employee_administration import list_employees, set_employee_enabled, set_employee_role


class TestC360RegistrationRequest(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.email = f"registration-{frappe.generate_hash(length=12)}@example.com"
        self.payload = {
            "full_name": "Registration Test",
            "email": self.email,
            "phone": f"09{randbelow(10**8):08d}",
            "department": "Sales",
        }
        self.addCleanup(frappe.set_user, "Administrator")

    def _submit(self):
        frappe.set_user("Guest")
        try:
            self.assertEqual(registration.submit(**self.payload), {"accepted": True})
        finally:
            frappe.set_user("Administrator")
        return frappe.db.get_value(registration.DOCTYPE, {"email": self.email}, "name")

    def test_submit_validates_and_deduplicates(self):
        with self.assertRaises(frappe.ValidationError):
            registration.submit(**dict(self.payload, email="invalid"))
        registration.submit(**self.payload, website="bot")
        self.assertFalse(frappe.db.exists(registration.DOCTYPE, {"email": self.email}))
        name = self._submit()
        self.assertEqual(self._submit(), name)
        self.assertEqual(frappe.db.get_value(registration.DOCTYPE, name, "status"), "Pending")
        self.assertFalse(frappe.db.exists("User", self.email))

    def test_review_requires_administrator_and_rejection_never_creates_user(self):
        name = self._submit()
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            registration.review(name, "Approved", "Not authorized", "Sales User")
        frappe.set_user("Administrator")
        self.assertEqual(registration.review(name, "Rejected", "Policy decision")["status"], "Rejected")
        self.assertFalse(frappe.db.exists("User", self.email))
        with self.assertRaises(frappe.ValidationError):
            registration.review(name, "Approved", "Second review", "Sales User")

    def test_approval_is_idempotent_and_denies_privileged_roles(self):
        name = self._submit()
        with self.assertRaises(frappe.ValidationError):
            registration.review(name, "Approved", "Invalid role", "System Manager")
        with patch.object(frappe, "sendmail", return_value=SimpleNamespace(name=None)):
            # Simulate no outgoing mail without delivering email for an integration test account.
            result = registration.review(name, "Approved", "Verified", "Sales User")
        self.assertEqual(result, {"status": "Approved", "invitation_status": "Failed"})
        user = frappe.get_doc("User", self.email)
        self.assertTrue(user.enabled)
        self.assertIn("Sales User", {item.role for item in user.roles})
        self.assertNotIn("System Manager", {item.role for item in user.roles})
        self.assertEqual(registration.review(name, "Approved", "Repeated", "Sales Manager"), result)
        self.assertEqual(frappe.db.get_value(registration.DOCTYPE, name, "assigned_role"), "Sales User")
        frappe.db.set_value("User", self.email, "enabled", 0)
        with self.assertRaises(frappe.ValidationError):
            registration.retry_invitation(name)

        previous_request = getattr(frappe.local, "request", None)
        try:
            frappe.local.request = SimpleNamespace(path="/api/resource/CRM%20Lead")
            frappe.set_user(self.email)
            with self.assertRaises(frappe.PermissionError):
                require_enabled_api_account()
        finally:
            frappe.local.request = previous_request
            frappe.set_user("Administrator")

    def test_existing_user_remains_unchanged(self):
        name = self._submit()
        user = frappe.get_doc({
            "doctype": "User", "email": self.email, "first_name": "Existing",
            "enabled": 0, "send_welcome_email": 0,
        }).insert()
        with self.assertRaises(frappe.ValidationError):
            registration.review(name, "Approved", "Refuse collision", "Sales User")
        self.assertFalse(frappe.db.get_value("User", user.name, "enabled"))
        self.assertEqual(frappe.db.get_value(registration.DOCTYPE, name, "status"), "Pending")

    def test_administrator_changes_native_employee_role_and_enabled_state(self):
        user = frappe.get_doc({
            "doctype": "User", "email": self.email, "first_name": "Synthetic employee",
            "user_type": "System User", "send_welcome_email": 0, "roles": [{"role": "Sales User"}],
        }).insert()
        employee = list_employees(search=self.email)["items"][0]
        self.assertTrue(employee.manageable)
        self.assertIn("Sales Manager", set_employee_role(user.name, "Sales Manager")["roles"])
        self.assertNotIn("Sales User", frappe.get_roles(user.name))
        self.assertFalse(set_employee_enabled(user.name, False)["enabled"])
        self.assertFalse(user.reload().enabled)
        with self.assertRaises(frappe.PermissionError):
            set_employee_enabled("Administrator", False)

    def test_password_setup_and_email_retry(self):
        name = self._submit()
        password = frappe.generate_hash(length=32)
        with self.assertRaises(frappe.AuthenticationError):
            check_password(self.email, password)

        with patch.object(frappe, "sendmail", side_effect=frappe.OutgoingEmailError):
            result = registration.review(name, "Approved", "Verified", "Sales User")
        self.assertEqual(result["invitation_status"], "Failed")

        queue = frappe.get_doc({"doctype": "Email Queue", "status": "Not Sent"})
        queue.name = frappe.generate_hash(length=12)
        queue.db_insert()
        with patch.object(frappe, "sendmail", return_value=queue) as send:
            self.assertEqual(registration.retry_invitation(name)["invitation_status"], "Queued")
            self.assertEqual(registration.retry_invitation(name)["invitation_status"], "Queued")
            send.assert_called_once()
            self.assertEqual(send.call_args.kwargs["recipients"], [self.email])
            self.assertIn("/update-password?key=", send.call_args.kwargs["args"]["link"])

        update_password(self.email, password)
        self.assertEqual(check_password(self.email, password), self.email)
