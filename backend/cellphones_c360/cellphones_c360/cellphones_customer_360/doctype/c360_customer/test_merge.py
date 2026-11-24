from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from cellphones_c360.api import intake, merge
from cellphones_c360.api.customer360 import get_customer_360


class TestCustomerMerge(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        self.source_data = intake.process_records([{
            "source_channel": "Store",
            "source_record_id": uuid4().hex,
            "customer_name": "Merge test source",
            "email": f"c360-merge-{uuid4().hex}@example.test",
        }])["items"][0]
        self.source = frappe.get_doc(merge.DOCTYPE, self.source_data["customer"])
        self.target = frappe.get_doc({"doctype": merge.DOCTYPE, "customer_name": "Merge test golden"}).insert()
        self.contact = frappe.get_doc({"doctype": "Contact", "first_name": "Merge Test Contact"}).insert()
        self.source.crm_contact = self.contact.name
        self.source.save()
        self.order = frappe.get_doc({
            "doctype": "Customer Order", "customer": self.source.name, "sales_channel": "Store",
            "order_status": "Completed", "items": [{"product_name": "Demo", "quantity": 1, "unit_price": 100}],
        }).insert()
        self.ticket = frappe.get_doc({
            "doctype": "Customer Support Ticket", "subject": "Example request", "ticket_type": "Warranty",
            "customer": self.source.name, "related_order": self.order.name, "description": "Synthetic ticket",
        }).insert()

    def merge(self, **overrides):
        return merge.merge_customers(**{
            "source": self.source.name,
            "target": self.target.name,
            "source_modified": self.source.modified,
            "target_modified": self.target.modified,
            "reason": "Verified synthetic merge",
            "verified": True,
            "selected": {"email": "source"},
            **overrides,
        })

    def test_moves_related_documents_and_retains_archived_source(self):
        self.assertTrue(merge.preview(self.source.name, self.target.name)["can_merge"])
        result = self.merge()
        self.assertEqual(result["customer"], self.target.name)
        self.assertEqual(result["moved"], dict.fromkeys(merge.MERGE_DOCTYPES, 1))
        self.assertEqual(self.target.reload().email, self.source.email)
        self.assertEqual(self.target.crm_links[0].link_name, self.contact.name)
        self.assertEqual(self.order.reload().customer, self.target.name)
        self.assertEqual(self.ticket.reload().customer, self.target.name)
        self.assertEqual(self.ticket.related_order, self.order.name)
        self.assertEqual(
            frappe.db.get_value(intake.DOCTYPE, self.source_data["source_document"], "customer"),
            self.target.name,
        )
        self.assertEqual(self.source.reload().merged_into, self.target.name)
        self.assertEqual(self.source.merge_reason, "Verified synthetic merge")
        self.assertEqual(get_customer_360(self.source.name)["customer"]["merged_into"], self.target.name)
        with self.assertRaises(frappe.PermissionError):
            self.source.save()

    def test_rolls_back_partially_moved_documents(self):
        move = merge._move

        def fail_on_ticket(doc, customer):
            if doc.doctype == "Customer Support Ticket":
                raise frappe.ValidationError("Simulated failure after moving the order")
            move(doc, customer)

        with patch.object(merge, "_move", side_effect=fail_on_ticket), self.assertRaises(frappe.ValidationError):
            self.merge()
        self.assertFalse(self.source.reload().merged_into)
        self.assertFalse(self.target.reload().email)
        self.assertFalse(self.target.crm_links)
        self.assertEqual(self.order.reload().customer, self.source.name)
        self.assertEqual(self.ticket.reload().customer, self.source.name)

    def test_requires_explicit_verification_and_merge_role(self):
        with self.assertRaises(frappe.ValidationError):
            self.merge(verified=False)
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            self.merge()
