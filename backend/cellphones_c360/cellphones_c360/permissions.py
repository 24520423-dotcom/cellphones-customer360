import frappe
from frappe import _

SERVICE = "C360 Customer Service"
OPERATIONS = "C360 Operations"
MARKETING = "C360 Marketing"
MERGE_APPROVER = "C360 Merge Approver"
DEPARTMENTS = (SERVICE, OPERATIONS, MARKETING)
CUSTOMER = "C360 Customer"
ORDER = "Customer Order"
TICKET = "Customer Support Ticket"


def install_roles():
    for role in (*DEPARTMENTS, MERGE_APPROVER):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()
    for role in DEPARTMENTS:
        if not frappe.db.exists("Role Profile", role):
            frappe.get_doc({
                "doctype": "Role Profile", "role_profile": role,
                "roles": [{"role": role}],
            }).insert()


def department(user=None):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if user == "Administrator" or roles.intersection({"System Manager", "Sales Manager"}):
        return None
    return next((role for role in DEPARTMENTS if role in roles), None)


def _grant(customer, user_sql, doctype):
    return f"""EXISTS (
        SELECT 1 FROM `tabUser Permission` AS grant_row
        WHERE grant_row.user = {user_sql} AND grant_row.allow = 'C360 Customer'
          AND grant_row.for_value = {customer}
          AND COALESCE(grant_row.applicable_for, '') IN ('', '{doctype}')
    )"""


def _assigned_customer(customer, user_sql, doctype, role):
    grant = _grant(customer, user_sql, doctype)
    if role == SERVICE:
        return f"""({grant} OR EXISTS (
            SELECT 1 FROM `tabCustomer Support Ticket` AS work
            WHERE work.customer = {customer}
              AND (work.assigned_to = {user_sql}
                   OR (COALESCE(work.assigned_to, '') = '' AND work.owner = {user_sql}))
        ))"""
    return f"""({grant} OR EXISTS (
        SELECT 1 FROM `tabCustomer Order` AS work
        WHERE work.customer = {customer} AND work.fulfillment_owner = {user_sql}
    ))"""


def _scope(doctype, user):
    role = department(user)
    if not role:
        return None
    user_sql = frappe.db.escape(user)
    table = f"`tab{doctype}`"
    if doctype == CUSTOMER:
        if role == MARKETING:
            return f"{table}.marketing_consent = 1 AND COALESCE({table}.merged_into, '') = ''"
        return _assigned_customer(f"{table}.name", user_sql, doctype, role)
    if role == MARKETING:
        return "1 = 0"
    if doctype == ORDER and role == OPERATIONS:
        return f"{table}.fulfillment_owner = {user_sql}"
    if doctype == TICKET and role == SERVICE:
        return (
            f"({table}.assigned_to = {user_sql} OR "
            f"(COALESCE({table}.assigned_to, '') = '' AND {table}.owner = {user_sql}))"
        )
    return _assigned_customer(f"{table}.customer", user_sql, doctype, role)


def customer_query(user=None):
    return _scope(CUSTOMER, user or frappe.session.user)


def order_query(user=None):
    return _scope(ORDER, user or frappe.session.user)


def ticket_query(user=None):
    return _scope(TICKET, user or frappe.session.user)


def document_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    scope = _scope(doc.doctype, user)
    if scope is None:
        return None
    if doc.is_new():
        return None
    allowed = frappe.db.sql(
        f"SELECT 1 FROM `tab{doc.doctype}` WHERE name = %s AND ({scope})",
        doc.name,
    )
    return None if allowed else False


def validate_operations_order(doc):
    if department() != OPERATIONS:
        return
    previous = doc.get_doc_before_save()
    if not previous or any(
        doc.has_value_changed(field)
        for field in ("customer", "crm_deal", "order_date", "sales_channel", "payment_method",
                      "payment_status", "fulfillment_owner")
    ) or doc.item_values() != previous.item_values():
        frappe.throw(_("Operations can change fulfillment and order status only."), frappe.PermissionError)
