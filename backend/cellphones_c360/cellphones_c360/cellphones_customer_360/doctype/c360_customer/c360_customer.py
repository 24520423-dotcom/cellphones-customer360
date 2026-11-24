import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import validate_email_address

PHONE_PATTERN = re.compile(r"0(?:[35789][0-9]{8}|2[0-9]{9})")
CRM_DOCTYPES = ("Contact", "CRM Lead", "CRM Deal")
ARCHIVE_FIELDS = ("merged_into", "merged_at", "merged_by", "merge_reason")


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


def normalize_source(value):
    channel = " ".join((value or "").split())
    options = frappe.get_meta("C360 Customer").get_field("source_channel").options.splitlines()
    return next((option for option in options if option.casefold() == channel.casefold()), channel)


def lock_customer_identity_writes():
    # A shared, existing InnoDB row keeps the duplicate check and save in the same serial order.
    frappe.db.get_value("DocType", "C360 Customer", "name", for_update=True)


def check_customer_link(customer):
    if not customer:
        return
    doc = frappe.get_doc("C360 Customer", customer, for_update=True)
    if not (doc.has_permission("read") or doc.has_permission("select")):
        frappe.throw(_("You cannot link this customer."), frappe.PermissionError)
    if doc.get("merged_into"):
        frappe.throw(_("Choose the current customer profile. This profile was merged."))


def find_identity_matches(phone, email, exclude=None):
    if not phone and not email:
        return []

    # Current read includes records submitted while this transaction was waiting for the lock.
    active_only = "AND COALESCE(merged_into, '') = ''" if frappe.get_meta("C360 Customer").has_field("merged_into") else ""
    return frappe.db.sql(
        f"""
        SELECT name,
               (NULLIF(%(phone)s, '') = phone_number) AS phone_match,
               (NULLIF(%(email)s, '') = email) AS email_match
        FROM `tabC360 Customer`
        WHERE name != %(excluded)s
          AND (phone_number = NULLIF(%(phone)s, '') OR email = NULLIF(%(email)s, ''))
          {active_only}
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
        previous = self.get_doc_before_save()
        if not self.flags.merging_customer and (
            any(self.get(field) for field in ARCHIVE_FIELDS) or (previous and previous.get("merged_into"))
        ):
            frappe.throw(_("Archived customers can only be changed by the merge workflow."), frappe.PermissionError)

        self.customer_name = " ".join((self.customer_name or "").split())
        if self.has_value_changed("phone_number"):
            self.phone_number = normalize_phone(self.phone_number) or None
        if self.has_value_changed("email"):
            self.email = normalize_email(self.email) or None
        if self.has_value_changed("source_channel"):
            self.source_channel = normalize_source(self.source_channel) or None

        old_links = set(customer_crm_links(previous)) if previous else set()
        for doctype, link in set(customer_crm_links(self)) - old_links:
            if doctype not in CRM_DOCTYPES:
                frappe.throw(_("Only Contact, CRM Lead and CRM Deal can be linked here."))
            if not any(frappe.has_permission(doctype, perm, doc=link) for perm in ("read", "select")):
                frappe.throw(_("You cannot link this {0}.").format(_(doctype)), frappe.PermissionError)

        self.check_duplicate_customer()

    def check_duplicate_customer(self):
        if self.get("merged_into"):
            return
        phone = self.phone_number if self.has_value_changed("phone_number") else None
        email = self.email if self.has_value_changed("email") else None
        if find_identity_matches(phone, email, self.name):
            frappe.throw(
                _("A customer already uses this phone number or email. Search Customer 360 and verify the identity before continuing."),
                title=_("Possible Duplicate Customer"),
            )


def customer_crm_links(doc):
    links = [
        (doctype, doc.get(field))
        for field, doctype in (("crm_contact", "Contact"), ("crm_lead", "CRM Lead"))
        if doc.get(field)
    ]
    links.extend(
        (row.link_doctype, row.link_name) for row in (doc.get("crm_links") or [])
        if row.link_doctype and row.link_name
    )
    return list(dict.fromkeys(links))
