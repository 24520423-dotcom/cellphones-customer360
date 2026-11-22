
# Copyright (c) 2026, CellphoneS CRM Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CustomerOrder(Document):

    def validate(self):
        self.calculate_order_total()

    def calculate_order_total(self):
        total = 0

        if not self.get("items"):
            frappe.throw(
                _("Đơn hàng phải có ít nhất một sản phẩm.")
            )

        for item in self.items:
            quantity = flt(item.quantity)
            unit_price = flt(item.unit_price)

            # Kiểm tra số lượng hợp lệ
            if quantity <= 0 or not quantity.is_integer():
                frappe.throw(
                    _("Số lượng sản phẩm phải là số nguyên lớn hơn 0.")
                )

            # Kiểm tra đơn giá hợp lệ
            if unit_price < 0:
                frappe.throw(
                    _("Đơn giá sản phẩm không được âm.")
                )

            # Tính thành tiền từng sản phẩm
            item.amount = quantity * unit_price

            # Cộng tổng tiền đơn hàng
            total += item.amount

        self.total_amount = total
