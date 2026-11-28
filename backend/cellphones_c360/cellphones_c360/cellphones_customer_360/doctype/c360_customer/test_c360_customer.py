# Copyright (c) 2026, CellphoneS CRM Team and Contributors
# See license.txt

from uuid import uuid4

import frappe
from frappe import client
from frappe.tests.utils import FrappeTestCase

from cellphones_c360.api import customers


class TestC360Customer(FrappeTestCase):
    def setUp(self):
        self.original_user = frappe.session.user
        frappe.set_user("Administrator")
        self.addCleanup(frappe.set_user, self.original_user)
        self.email = f"c360-test-{uuid4().hex}@example.test"

    def insert_customer(self, **values):
        return client.insert({
            "doctype": "C360 Customer",
            "customer_name": "Demo customer",
            **values,
        })

    def test_create_uses_live_metadata_and_normalizes(self):
        fields = {field["fieldname"]: field for field in customers.get_access()["fields"]}
        self.assertTrue(fields["customer_name"]["required"])
        self.assertIn("Store", fields["source_channel"]["options"])
        created = self.insert_customer(
            customer_name="  Demo   customer  ",
            email=f" {self.email.upper()} ",
            source_channel=" store ",
        )
        stored = frappe.get_doc("C360 Customer", created["name"])
        self.assertEqual(stored.customer_name, "Demo customer")
        self.assertEqual(stored.email, self.email)
        self.assertEqual(stored.source_channel, "Store")

    def test_rejects_invalid_customer(self):
        for values in ({"customer_name": "  "}, {"email": "a@@example.test"}, {"phone_number": "123"}):
            with self.subTest(values=values), self.assertRaises(frappe.ValidationError):
                self.insert_customer(**values)

    def test_detects_duplicate_without_disclosing_record(self):
        created = self.insert_customer(customer_name="Distinct test identity", email=self.email)
        with self.assertRaises(frappe.ValidationError) as error:
            self.insert_customer(email=self.email.upper())
        self.assertNotIn(created["name"], str(error.exception))
        self.assertNotIn(created["customer_name"], str(error.exception))

    def test_guest_has_no_create_permission(self):
        frappe.set_user("Guest")
        self.assertFalse(customers.get_access()["canCreate"])
        with self.assertRaises(frappe.PermissionError):
            self.insert_customer(email=self.email)

    def test_edit_preserves_contact_and_records_version(self):
        contact = frappe.get_doc({"doctype": "Contact", "first_name": "C360 Test Contact"}).insert()
        customer = self.insert_customer(crm_contact=contact.name, email=self.email)
        name = customer["name"]
        self.assertTrue(customers.get_access(name)["canEdit"])
        original_test_flag = frappe.flags.in_test
        frappe.flags.in_test = False
        try:
            customers.update_customer(name, {"customer_name": "Renamed customer"}, customer["modified"])
        finally:
            frappe.flags.in_test = original_test_flag

        stored = frappe.get_doc("C360 Customer", name)
        self.assertEqual(stored.customer_name, "Renamed customer")
        self.assertEqual(stored.crm_contact, contact.name)
        self.assertTrue(frappe.db.exists("Version", {"ref_doctype": stored.doctype, "docname": name}))

    def test_edit_rejects_unchanged_revision_and_protected_fields(self):
        customer = self.insert_customer(email=self.email)
        name, modified = customer["name"], customer["modified"]
        with self.assertRaises(frappe.PermissionError):
            customers.update_customer(name, {"name": "wrong-id"}, modified)

        customers.update_customer(name, {"customer_name": "First editor"}, modified)
        with self.assertRaises(frappe.TimestampMismatchError):
            customers.update_customer(name, {"customer_name": "Stale editor"}, modified)
        self.assertEqual(frappe.db.get_value("C360 Customer", name, "customer_name"), "First editor")

    def test_edit_checks_duplicate_excluding_current_customer(self):
        first = self.insert_customer(email=self.email)
        second = self.insert_customer()
        customers.update_customer(first["name"], {"email": self.email.upper()}, first["modified"])
        with self.assertRaises(frappe.ValidationError):
            customers.update_customer(second["name"], {"email": self.email}, second["modified"])

    def test_candidate_types_and_vietnamese_phone_equivalence(self):
        customer = self.insert_customer(
            customer_name=f"C360 duplicate {uuid4().hex}", phone_number="+84 (28) 3999 0123",
            email=self.email,
        )
        self.assertEqual(customer["phone_number"], "02839990123")
        same_phone = customers.find_duplicates(phone_number="84.28.3999.0123", email=self.email)
        self.assertIn(["phone_number", "email"], [item.matched_fields for item in same_phone])
        with self.assertRaises(frappe.ValidationError):
            self.insert_customer(phone_number="028 3999 0123")

        same_name = self.insert_customer(customer_name=customer["customer_name"])
        candidates = customers.find_duplicates(customer=same_name["name"])
        self.assertEqual([(row.name, row.matched_fields) for row in candidates], [
            (customer["name"], ["customer_name"]),
        ])
