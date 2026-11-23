"""Immutable source/reference metadata per imported customer event.

The API alone assigns status. Staff with appropriate permissions may review pending
records and link them manually; this controller prevents contradictory links.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class C360CustomerIntake(Document):
    def validate(self):
        if self.status in ("Created", "Linked") and not self.customer:
            frappe.throw(_("Bản ghi đã xử lý phải liên kết đến Customer."))
        if self.status == "Needs Review" and self.customer:
            frappe.throw(_("Bản ghi chờ xác minh không được tự động liên kết Customer."))
        if self.customer and self.candidate_customer and self.customer != self.candidate_customer:
            frappe.throw(_("Customer và Candidate Customer không nhất quán."))
