
import re

import frappe
from frappe import _
from frappe.model.document import Document


class C360Customer(Document):

    def validate(self):
        self.normalize_customer_data()
        self.check_duplicate_customer()

    def normalize_customer_data(self):
        # Chuẩn hóa số điện thoại
        if self.phone_number:
            self.phone_number = re.sub(
                r"[\s.\-()]",
                "",
                self.phone_number.strip()
            )

            if self.phone_number.startswith("+84"):
                self.phone_number = "0" + self.phone_number[3:]
            elif self.phone_number.startswith("84"):
                self.phone_number = "0" + self.phone_number[2:]

        # Chuẩn hóa email
        if self.email:
            self.email = self.email.strip().lower()


    def check_duplicate_customer(self):
        if not self.phone_number and not self.email:
            return

        filters = []

        if self.phone_number:
            filters.append(
                ["phone_number", "=", self.phone_number]
            )

        if self.email:
            filters.append(
                ["email", "=", self.email]
            )

        existing_customers = frappe.get_all(
            "C360 Customer",
            filters=[
                ["name", "!=", self.name or ""]
            ],
            or_filters=filters,
            fields=[
                "name",
                "customer_name",
                "phone_number",
                "email"
            ]
        )

        for customer in existing_customers:
            phone_match = bool(
                self.phone_number
                and customer.phone_number == self.phone_number
            )

            email_match = bool(
                self.email
                and customer.email
                and customer.email.lower() == self.email
            )

            if phone_match and email_match:
                reason = "Trùng số điện thoại và email"
            elif phone_match:
                reason = "Trùng số điện thoại"
            elif email_match:
                reason = "Trùng email"
            else:
                continue

            frappe.throw(
                _(
                    "{0}. Khách hàng có thể đã tồn tại: "
                    "{1} (Mã hồ sơ: {2}). "
                    "Vui lòng kiểm tra trước khi tạo mới."
                ).format(
                    reason,
                    customer.customer_name,
                    customer.name
                ),
                title=_("Possible Duplicate Customer")
            )
