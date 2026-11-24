from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from cellphones_c360.api import crm_links, intake, merge
from cellphones_c360.api.customer360 import get_customer_360, get_customer_timeline
from cellphones_c360.permissions import MERGE_APPROVER


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
            "items": [{"product_name": "Demo", "quantity": 1, "unit_price": 100}],
        }).insert()
        self.ticket = frappe.get_doc({
            "doctype": "Customer Support Ticket", "subject": "Example request", "ticket_type": "Technical Support",
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

    def test_sales_manager_requires_approver_and_preserves_consent(self):
        manager = frappe.get_doc({
            "doctype": "User", "first_name": "Merge permission demo",
            "email": f"c360-approval-{uuid4().hex}@example.test", "send_welcome_email": 0,
            "roles": [{"role": "Sales Manager"}],
        }).insert()
        lead = crm_links.create_linked_lead(self.source.name, {"first_name": "Merge Demo"})["name"]
        deal = crm_links.create_linked_deal(self.source.name, {
            "status": frappe.get_list("CRM Deal Status", order_by="position", pluck="name")[0],
        })
        self.source.reload()
        self.source.marketing_consent = 1
        self.source.save()
        frappe.set_user(manager.name)
        with self.assertRaises(frappe.PermissionError):
            self.merge()
        frappe.set_user("Administrator")
        manager.add_roles(MERGE_APPROVER)
        frappe.set_user(manager.name)
        self.assertTrue(merge.preview(self.source.name, self.target.name)["can_merge"])
        with self.assertRaises(frappe.ValidationError):
            self.merge(selected={"marketing_consent": "source"})
        self.merge()
        self.target.reload()
        self.assertFalse(self.target.marketing_consent)
        self.assertEqual(self.source.reload().customer_status, "Inactive")
        self.assertEqual(self.source.merged_into, self.target.name)
        records = crm_links.related_records(self.target)
        self.assertEqual({doc.name for doc in records["CRM Lead"]}, {lead})
        self.assertEqual({doc.name for doc in records["CRM Deal"]}, {deal})
        self.assertEqual(self.order.reload().customer, self.target.name)
        self.assertEqual(self.ticket.reload().customer, self.target.name)
        self.assertEqual(frappe.db.get_value(
            intake.DOCTYPE, self.source_data["source_document"], "customer",
        ), self.target.name)
        self.assertTrue(any(item["type"] == "merge" for item in get_customer_timeline(self.target.name)["items"]))
