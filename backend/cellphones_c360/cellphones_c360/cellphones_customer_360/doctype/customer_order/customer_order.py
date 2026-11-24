
# Copyright (c) 2026, CellphoneS CRM Team and contributors
# For license information, please see license.txt

from math import isfinite

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from cellphones_c360.api.crm_links import related_records
from cellphones_c360.permissions import OPERATIONS, department, validate_operations_order

from cellphones_c360.cellphones_customer_360.doctype.c360_customer.c360_customer import (
    check_customer_link,
    lock_customer_identity_writes,
)

ORDER_TRANSITIONS = {
    "Draft": {"Confirmed", "Cancelled"},
    "Confirmed": {"Processing", "Cancelled"},
    "Processing": {"Completed", "Cancelled"},
}
PAYMENT_TRANSITIONS = {
    "Unpaid": {"Pending", "Paid"},
    "Pending": {"Unpaid", "Paid"},
    "Paid": {"Refunded"},
}
FULFILLMENT = {
    "Pickup": {"Awaiting Fulfillment", "Preparing", "Ready for Pickup", "Picked Up"},
    "Delivery": {"Awaiting Fulfillment", "Preparing", "In Transit", "Delivered", "Failed"},
}
HANDOVER = {"Pickup": "Picked Up", "Delivery": "Delivered"}


class CustomerOrder(Document):
    def check_if_latest(self):
        lock_customer_identity_writes()
        super().check_if_latest()

    def validate(self):
        if self.has_value_changed("customer"):
            check_customer_link(self.customer)
        if self.meta.has_field("fulfillment_owner"):
            validate_operations_order(self)
        if self.meta.has_field("payment_status"):
            self.validate_workflow()
            self.validate_deal()
        self.calculate_order_total()

    def before_rename(self, old, new, merge=False):
        if department() == OPERATIONS:
            frappe.throw(_("Operations cannot rename an order."), frappe.PermissionError)

    def validate_workflow(self):
        previous = self.get_doc_before_save()
        if not previous and self.order_status != "Draft":
            frappe.throw(_("Create an order in Draft before confirming it."))
        if previous:
            if self.order_status != previous.order_status and self.order_status not in ORDER_TRANSITIONS.get(previous.order_status, ()):
                frappe.throw(_("This order status transition is not allowed."))
            if (
                previous.payment_status and self.payment_status != previous.payment_status
                and self.payment_status not in PAYMENT_TRANSITIONS.get(previous.payment_status, ())
            ):
                frappe.throw(_("This payment status transition is not allowed."))
            if previous.order_status != "Draft" and self.item_values() != previous.item_values():
                frappe.throw(_("Products and prices are fixed after order confirmation."))
            if not self.flags.merging_customer and self.has_value_changed("customer") and (
                previous.order_status != "Draft"
                or frappe.db.exists("Customer Support Ticket", {"related_order": self.name})
            ):
                frappe.throw(_("This order already has history associated with the selected customer."))

        if self.has_value_changed("order_status") and self.order_status in {"Confirmed", "Processing", "Completed"}:
            if not self.payment_method or not self.fulfillment_method:
                frappe.throw(_("Choose a payment and fulfillment method before progressing the order."))
            self.fulfillment_status = self.fulfillment_status or "Awaiting Fulfillment"
        if self.fulfillment_status and self.fulfillment_status not in FULFILLMENT.get(self.fulfillment_method, ()):
            frappe.throw(_("The fulfillment status does not match the selected method."))
        if self.order_status == "Draft" and (self.fulfillment_status or self.payment_status not in ("Unpaid", None, "")):
            frappe.throw(_("Confirm the order before proceeding with payment or fulfillment."))
        if self.order_status == "Cancelled" and self.payment_status == "Paid":
            frappe.throw(_("Record the refund before cancelling a paid order."))
        if self.order_status == "Completed" and (
            self.has_value_changed("order_status") or self.has_value_changed("fulfillment_status")
            or self.has_value_changed("fulfillment_method")
        ) and self.fulfillment_status != HANDOVER.get(self.fulfillment_method):
            frappe.throw(_("Record the completed handover before completing the order."))

        self.paid_at = (
            now_datetime() if self.payment_status == "Paid" and self.has_value_changed("payment_status")
            else previous.paid_at if previous else None
        )
        self.completed_at = (
            now_datetime() if self.order_status == "Completed" and self.has_value_changed("order_status")
            else previous.completed_at if previous else None
        )
        if self.meta.has_field("care_task"):
            self.care_task = previous.get("care_task") if previous else None

    def item_values(self):
        return [
            (item.product_code or "", item.product_name, flt(item.quantity), flt(item.unit_price))
            for item in self.items
        ]

    def validate_deal(self):
        if not self.crm_deal or not self.customer or not (
            self.has_value_changed("crm_deal") or self.has_value_changed("customer")
        ):
            return
        customer = frappe.get_doc("C360 Customer", self.customer)
        customer.apply_fieldlevel_read_permissions()
        if self.crm_deal not in {deal.name for deal in related_records(customer)["CRM Deal"]}:
            frappe.throw(_("Choose a Deal already linked to this customer."))

    def calculate_order_total(self):
        total = 0

        if not self.get("items"):
            frappe.throw(
                _("Đơn hàng phải có ít nhất một sản phẩm.")
            )

        for item in self.items:
            try:
                quantity = float(item.quantity)
                unit_price = float(item.unit_price)
            except (TypeError, ValueError):
                frappe.throw(_("Quantity and unit price must be numeric."))

            # Kiểm tra số lượng hợp lệ
            if not isfinite(quantity) or quantity <= 0 or not quantity.is_integer():
                frappe.throw(
                    _("Số lượng sản phẩm phải là số nguyên lớn hơn 0.")
                )

            # Kiểm tra đơn giá hợp lệ
            if not isfinite(unit_price) or unit_price < 0:
                frappe.throw(
                    _("Đơn giá sản phẩm không được âm.")
                )

            # Tính thành tiền từng sản phẩm
            amount = quantity * unit_price
            if not isfinite(amount):
                frappe.throw(_("The item amount is out of range."))
            item.amount = flt(amount, item.precision("amount"))

            # Cộng tổng tiền đơn hàng
            total += item.amount

        self.total_amount = total
