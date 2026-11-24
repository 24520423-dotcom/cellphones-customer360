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
ORDER_STATUS_FIELDS = {"order_status", "fulfillment_status"}
MANAGEMENT_ROLES = {"System Manager", "Sales Manager"}


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
    if user == "Administrator" or roles.intersection(MANAGEMENT_ROLES):
        return None
    return next((role for role in DEPARTMENTS if role in roles), None)


def is_operations_order_editor(user=None):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    return user != "Administrator" and OPERATIONS in roles and not roles.intersection(MANAGEMENT_ROLES)


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
    if doctype == ORDER and is_operations_order_editor(user):
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
    if not is_operations_order_editor():
        return
    previous = doc.get_doc_before_save()
    protected_fields = set(doc.meta.get_valid_columns()).intersection(
        {"owner", "docstatus", *(field.fieldname for field in doc.meta.fields)}
    ) - ORDER_STATUS_FIELDS
    if not previous or any(
        doc.has_value_changed(field) for field in protected_fields
    ) or _order_items(doc) != _order_items(previous):
        frappe.throw(_("Operations can change only Order Status and Fulfillment Status."), frappe.PermissionError)


def _order_items(doc):
    return [
        {field: value for field, value in item.get_valid_dict().items() if field not in {"modified", "modified_by"}}
        for item in doc.get("items")
    ]
