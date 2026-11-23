"""Link validation between CRM Lead, Deal and C360 Customer."""
import frappe
from frappe import _


def validate_deal_customer(doc, method=None):
    """A Deal with a Lead may not point to another Customer.

    Legacy deals stay untouched unless the lead has an explicit C360 Customer
    link; new deals can still be created without a customer.
    """
    if not doc.get("lead") or not frappe.get_meta("CRM Lead").has_field("custom_c360_customer"):
        return
    lead_customer = frappe.db.get_value("CRM Lead", doc.lead, "custom_c360_customer")
    if not lead_customer:
        return
    if doc.get("custom_c360_customer") and doc.custom_c360_customer != lead_customer:
        frappe.throw(_("Customer của Deal khác Customer đã liên kết với Lead."), frappe.ValidationError)
    if frappe.get_meta("CRM Deal").has_field("custom_c360_customer"):
        doc.custom_c360_customer = lead_customer
