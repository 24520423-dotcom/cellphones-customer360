
# Copyright (c) 2026, CellphoneS CRM Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class CustomerSupportTicket(Document):

    def validate(self):
        self.validate_related_order()
        self.validate_resolution()
        self.set_resolved_date()
        self.validate_resolved_date()

    def validate_related_order(self):
        # Không bắt buộc Ticket phải có đơn hàng
        if not self.related_order:
            return

        # Lấy khách hàng của đơn hàng liên quan
        order_customer = frappe.db.get_value(
            "Customer Order",
            self.related_order,
            "customer"
        )

        if not order_customer:
            frappe.throw(
                _("Đơn hàng liên quan không tồn tại.")
            )

        # Kiểm tra đơn hàng có thuộc đúng khách hàng
        if order_customer != self.customer:
            frappe.throw(
                _(
                    "Đơn hàng {0} không thuộc khách hàng "
                    "được chọn trong Ticket."
                ).format(self.related_order)
            )

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
        # Chỉ tự ghi ngày khi chuyển sang Resolved
        if self.ticket_status != "Resolved":
            return

        # Không ghi đè thời điểm đã được lưu
        if self.resolved_date:
            return

        self.resolved_date = now_datetime()

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
