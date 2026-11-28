
# Copyright (c) 2026, CellphoneS CRM Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

from cellphones_c360.api.access import InvalidTransition
from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
    check_customer_link,
    lock_customer_identity_writes,
)

ORDER_REQUIRED = {"Warranty", "Return", "Exchange"}
TRANSITIONS = {
    "Open": {"In Progress", "Pending"},
    "In Progress": {"Pending", "Resolved"},
    "Pending": {"In Progress", "Resolved"},
    "Resolved": {"Closed", "In Progress"},
}


class CustomerSupportTicket(Document):
    def check_if_latest(self):
        lock_customer_identity_writes()
        super().check_if_latest()

    def validate(self):
        if self.has_value_changed("customer"):
            check_customer_link(self.customer)
        self.validate_related_order()
        self.validate_assignment()
        self.validate_status()
        self.validate_resolution()
        self.set_resolved_date()
        self.validate_resolved_date()

    def validate_related_order(self):
        requires_purchase = self.ticket_type in ORDER_REQUIRED
        changed = any(self.has_value_changed(field) for field in ("customer", "related_order", "ticket_type"))
        if not self.related_order:
            if changed and requires_purchase:
                frappe.throw(_("Select a completed order for warranty, return or exchange."))
            return

        order = frappe.get_doc("Customer Order", self.related_order, for_update=True)
        if changed:
            order.check_permission("read")
        if order.customer != self.customer:
            frappe.throw(_("The related order must belong to this customer."))
        if changed and requires_purchase:
            if order.order_status != "Completed":
                frappe.throw(_("Select a completed order for warranty, return or exchange."))
            purchase_date = order.get("completed_at") or order.order_date
            if purchase_date and self.created_date and get_datetime(self.created_date) < get_datetime(purchase_date):
                frappe.throw(_("The support request cannot predate the purchase."))

    def validate_assignment(self):
        if not self.assigned_to or not self.has_value_changed("assigned_to"):
            return
        user = frappe.db.get_value("User", self.assigned_to, ("enabled", "user_type"), as_dict=True)
        if not user or not user.enabled or user.user_type != "System User" or not frappe.has_permission(
            self.doctype, "write", user=self.assigned_to,
        ):
            frappe.throw(_("Assign the ticket to an active employee with support permissions."))

    def validate_status(self):
        previous = self.get_doc_before_save()
        if not previous:
            if self.ticket_status != "Open":
                frappe.throw(_("New tickets must start in Open."))
            return
        if self.ticket_status == previous.ticket_status:
            return
        if self.ticket_status not in TRANSITIONS.get(previous.ticket_status, ()):
            frappe.throw(_("This ticket status transition is not allowed."), InvalidTransition)
        if self.ticket_status in {"In Progress", "Resolved", "Closed"} and not self.assigned_to:
            frappe.throw(_("Assign the ticket before progressing it."))

    def validate_resolution(self):
        # Ticket đã giải quyết phải có nội dung xử lý
        if self.ticket_status in ["Resolved", "Closed"]:
            if not (self.resolution or "").strip():
                frappe.throw(
                    _(
                        "Vui lòng nhập Resolution trước khi "
                        "chuyển Ticket sang Resolved hoặc Closed."
                    )
                )

    def set_resolved_date(self):
        previous = self.get_doc_before_save()
        if self.ticket_status == "Resolved" and self.has_value_changed("ticket_status"):
            self.resolved_date = now_datetime()
        elif self.ticket_status in {"Resolved", "Closed"} and previous:
            self.resolved_date = previous.resolved_date
        else:
            self.resolved_date = None

    def validate_resolved_date(self):
        if not self.resolved_date or not self.created_date:
            return

        if get_datetime(self.resolved_date) < get_datetime(
            self.created_date
        ):
            frappe.throw(
                _(
                    "Resolved Date không được sớm hơn "
                    "Created Date."
                )
            )
