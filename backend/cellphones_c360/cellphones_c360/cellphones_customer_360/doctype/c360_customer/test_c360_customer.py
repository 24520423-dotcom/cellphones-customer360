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
