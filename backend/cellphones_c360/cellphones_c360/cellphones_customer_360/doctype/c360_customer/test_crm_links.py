from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

from cellphones_c360.api import crm_links
from cellphones_c360.api.customer360 import get_customer_360


class TestCustomerCRMLinks(FrappeTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, frappe.session.user)
        frappe.set_user("Administrator")
        self.customer = frappe.get_doc({
            "doctype": crm_links.CUSTOMER, "customer_name": "CRM Integration Demo",
        }).insert()
        self.lead_status = frappe.get_list("CRM Lead Status", order_by="position", pluck="name")[0]
        self.deal_status = frappe.get_list("CRM Deal Status", order_by="position", pluck="name")[0]

    def create_lead(self, label):
        return crm_links.create_linked_lead(self.customer.name, {
            "first_name": label, "email": f"c360-crm-{uuid4().hex}@example.test",
            "status": self.lead_status,
        })["name"]

    def test_converted_and_repeat_sales_share_same_customer(self):
        first = self.create_lead("Initial purchase")
        second = self.create_lead("Repeat purchase")
        converted = convert_to_deal(lead=first, if_converted="Return Existing")
        self.assertEqual(convert_to_deal(lead=first, if_converted="Return Existing"), converted)
        standalone = crm_links.create_linked_deal(self.customer.name, {"status": self.deal_status})
        self.assertFalse(frappe.db.get_value("CRM Deal", standalone, "lead"))
        records = crm_links.related_records(self.customer.reload())
        self.assertEqual({doc.name for doc in records["CRM Lead"]}, {first, second})
        self.assertEqual({row.name for row in records["CRM Deal"]}, {converted, standalone})
        profile = get_customer_360(self.customer.name)
        self.assertEqual({lead["name"] for lead in profile["leads"]}, {first, second})
        self.assertEqual({deal.name for deal in profile["deals"]}, {converted, standalone})

    def test_native_linked_lead_normalizes_repeated_salutation(self):
        name = crm_links.create_linked_lead(self.customer.name, {
            "salutation": "Miss", "first_name": "miss  Miss Sample",
            "last_name": "Miss", "status": self.lead_status,
        })["name"]
        lead = frappe.get_doc("CRM Lead", name)
        self.assertEqual(lead.first_name, "Sample")
        self.assertEqual(lead.lead_name, "Miss Sample Miss")
        lead.save()
        self.assertEqual(lead.reload().lead_name, "Miss Sample Miss")
        self.assertEqual(crm_links.related_records(self.customer.reload())["CRM Lead"][0].name, name)

    def test_native_contact_table_resolves_deal(self):
        contact = frappe.get_doc({"doctype": "Contact", "first_name": "Shared Contact Demo"}).insert()
        crm_links.link_record(self.customer.name, contact.doctype, contact.name)
        crm_links.link_record(self.customer.name, contact.doctype, contact.name)
        second = frappe.get_doc({"doctype": crm_links.CUSTOMER, "customer_name": "Other demo"}).insert()
        deal = crm_links.create_linked_deal(second.name, {
            "status": self.deal_status, "contact": contact.name,
        })
        records = crm_links.related_records(self.customer.reload())
        self.assertEqual(len(self.customer.crm_links), 1)
        self.assertEqual({row.name for row in records["CRM Deal"]}, {deal})
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            crm_links.link_record(second.name, contact.doctype, contact.name)
