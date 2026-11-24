from hashlib import sha256

import frappe
from frappe import _
from frappe.model.document import Document


def source_key(channel, reference):
    return "SRC-" + sha256(f"{channel}\n{reference}".encode()).hexdigest()


class C360SourceRecord(Document):
    def autoname(self):
        self.name = source_key(self.source_channel, self.source_record_id)

    def validate(self):
        if not self.flags.processing_intake:
            frappe.throw(_("Use the Customer 360 intake workflow to process source records."), frappe.PermissionError)
