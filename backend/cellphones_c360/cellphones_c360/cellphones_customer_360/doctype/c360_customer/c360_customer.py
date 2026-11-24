import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import validate_email_address

PHONE_PATTERN = re.compile(r"0(?:[35789][0-9]{8}|2[0-9]{9})")


def normalize_phone(value):
    phone = re.sub(r"[\s.\-()]", "", value or "")
    if phone.startswith(("+84", "84")):
        phone = "0" + phone.split("84", 1)[1]
    if phone and not PHONE_PATTERN.fullmatch(phone):
        frappe.throw(_("Enter a valid Vietnamese mobile or landline number."))
    return phone


def normalize_email(value):
    email = (value or "").strip().lower()
    if email and (
        not re.fullmatch(r"[^@\s,;<>]+@[^@\s,;<>]+", email)
        or validate_email_address(email) != email
    ):
        frappe.throw(_("Enter one valid email address."))
    return email


def lock_customer_identity_writes():
    # A shared, existing InnoDB row keeps the duplicate check and save in the same serial order.
    frappe.db.get_value("DocType", "C360 Customer", "name", for_update=True)


def find_identity_matches(phone, email, exclude=None):
    if not phone and not email:
        return []

    # Current read includes records submitted while this transaction was waiting for the lock.
    return frappe.db.sql(
        """
        SELECT name,
               (NULLIF(%(phone)s, '') = phone_number) AS phone_match,
               (NULLIF(%(email)s, '') = email) AS email_match
        FROM `tabC360 Customer`
        WHERE name != %(excluded)s
          AND (phone_number = NULLIF(%(phone)s, '') OR email = NULLIF(%(email)s, ''))
        ORDER BY name
        FOR UPDATE
        """,
        {"phone": phone or "", "email": email or "", "excluded": exclude or ""},
        as_dict=True,
    )


class C360Customer(Document):
    def check_if_latest(self):
        lock_customer_identity_writes()
        super().check_if_latest()

    def validate(self):
        self.customer_name = " ".join((self.customer_name or "").split())
        if self.has_value_changed("phone_number"):
            self.phone_number = normalize_phone(self.phone_number) or None
        if self.has_value_changed("email"):
            self.email = normalize_email(self.email) or None
        if self.has_value_changed("source_channel"):
            channel = " ".join((self.source_channel or "").split())
            options = self.meta.get_field("source_channel").options.splitlines()
            self.source_channel = next(
                (option for option in options if option.casefold() == channel.casefold()), channel
            ) or None

        for fieldname, doctype in (("crm_contact", "Contact"), ("crm_lead", "CRM Lead")):
            link = self.get(fieldname)
            if link and self.has_value_changed(fieldname):
                if not any(frappe.has_permission(doctype, perm, doc=link) for perm in ("read", "select")):
                    frappe.throw(_("You cannot link this {0}.").format(_(doctype)), frappe.PermissionError)

        self.check_duplicate_customer()

    def check_duplicate_customer(self):
        phone = self.phone_number if self.has_value_changed("phone_number") else None
        email = self.email if self.has_value_changed("email") else None
        if find_identity_matches(phone, email, self.name):
            frappe.throw(
                _("A customer already uses this phone number or email. Search Customer 360 and verify the identity before continuing."),
                title=_("Possible Duplicate Customer"),
            )
