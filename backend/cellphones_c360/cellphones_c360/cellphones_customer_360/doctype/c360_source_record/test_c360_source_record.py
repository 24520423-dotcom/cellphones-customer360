from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from cellphones_c360.api import intake


class TestC360SourceRecord(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        self.token = uuid4().hex
        self.data = {
            "source_channel": " Website ",
            "source_record_id": self.token,
            "received_at": "2026-11-21T09:00:00+07:00",
            "customer_name": "  Khách Demo   A ",
            "phone_number": "028.0000.0456",
            "email": f"INTAKE-{self.token}@EXAMPLE.TEST",
            "purchase_interest": 1,
        }

    def process(self, **values):
        return intake.process_records([{**self.data, **values}])["items"][0]

    def test_create_replay_link_and_verify_conflicts(self):
        created = self.process()
        self.assertEqual(created["status"], "Created")
        self.assertTrue(created["purchase_interest"])
        customer = frappe.get_doc(intake.CUSTOMER, created["customer"])
        self.assertEqual(customer.customer_name, "Khách Demo A")
        self.assertEqual(customer.phone_number, "02800000456")
        self.assertEqual(created["customer"], self.process(customer_name="Replay")["customer"])
        self.assertTrue(self.process()["replay"])

        linked = self.process(source_channel="Store", phone_number="+84 (28) 0000 0456")
        self.assertEqual(linked["status"], "Linked")
        self.assertEqual(linked["customer"], created["customer"])
        conflict = self.process(source_channel="Zalo", email="other@example.test")
        self.assertEqual(conflict["status"], "Needs Review")
        self.assertIsNone(conflict["customer"])
        resolved = intake.resolve_record(conflict["source_document"], customer.name, "Test verified identity")
        self.assertEqual(resolved["customer"], customer.name)
        log = frappe.get_doc(intake.DOCTYPE, conflict["source_document"])
        self.assertEqual(log.reviewed_by, "Administrator")
        self.assertEqual(log.review_reason, "Test verified identity")

    def test_invalid_row_does_not_discard_others(self):
        rows = [
            {**self.data, "source_record_id": self.token + "-invalid", "phone_number": "123"},
            {**self.data, "source_record_id": ""},
            {**self.data, "phone_number": ""},
        ]
        results = intake.process_records(rows)["items"]
        self.assertEqual([row["status"] for row in results], ["Invalid", "Invalid", "Created"])
        self.assertTrue(frappe.db.exists(intake.DOCTYPE, results[0]["source_document"]))
        self.assertEqual(frappe.db.get_value(intake.DOCTYPE, results[0]["source_document"], "customer"), None)

    def test_csv_schema_and_permissions(self):
        schema = "source_channel,source_record_id,received_at,customer_name,phone_number,email,customer_type,purchase_interest"
        row = f"App,{self.token},,Khách Demo App,,{self.token}@example.test,Individual,0"
        self.assertEqual(intake.process_csv(f"\ufeff{schema}\n{row}\n")["items"][0]["status"], "Created")
        with self.assertRaises(frappe.ValidationError):
            intake.process_csv("source_channel,source_record_id\nApp,1")
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            intake.process_csv(f"{schema}\n{row}\n")
