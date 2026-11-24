from functools import partial

import frappe
from frappe import _
from frappe.sessions import clear_sessions
from frappe.utils import cint, validate_email_address

from cellphones_c360.api.access import require_session_csrf
from cellphones_c360.api.registration import ROLES
from cellphones_c360.permissions import DEPARTMENTS, MERGE_APPROVER

IMPLICIT_ROLES = {"All", "Desk User", "Guest"}
PRIMARY_ROLES = ("System Manager", "Sales Manager", "Sales User", *DEPARTMENTS)
REPORT_ROLES = ("Administrator", *PRIMARY_ROLES, MERGE_APPROVER)
ASSIGNMENTS = (
    ("CRM Lead", "lead_owner"), ("CRM Deal", "deal_owner"),
    ("Customer Order", "fulfillment_owner"), ("Customer Support Ticket", "assigned_to"),
)
DOCTYPES = ("CRM Lead", "CRM Deal", "C360 Customer", "Customer Order", "Customer Support Ticket",
            "CRM Call Log", "CRM Task", "User", "C360 Registration Request")
OPERATIONS = ("select", "read", "create", "write", "delete", "submit", "cancel",
              "amend", "report", "export", "import", "share", "print", "email")


def _authorize(action):
    if frappe.session.user != "Administrator":
        frappe.logger("c360_administration").warning(
            "Denied administration action=%s actor=%s", action, frappe.session.user
        )
        frappe.throw("Chỉ Administrator được quản lý nhân viên và quyền.", frappe.PermissionError)
    require_session_csrf()


def _audit(subject, target=None):
    log = {
        "doctype": "Activity Log",
        "user": frappe.session.user,
        "subject": subject,
        "status": "Success",
    }
    if target:
        log.update(reference_doctype="User", reference_name=target)
    frappe.get_doc(log).insert(ignore_permissions=True)


def _primary(roles):
    return next((role for role in PRIMARY_ROLES if role in roles), None)


def _eligible(user, roles):
    assigned = set(roles) - IMPLICIT_ROLES
    primary = _primary(assigned)
    if user.name in ("Administrator", "Guest") or user.user_type != "System User" or not primary:
        return False
    if not assigned.issubset(set(PRIMARY_ROLES) | {MERGE_APPROVER}):
        return False
    departments = assigned.intersection(DEPARTMENTS)
    if departments and (len(departments) > 1 or assigned.difference(DEPARTMENTS)):
        return False
    if user.get("role_profiles"):
        return False
    if profile := user.role_profile_name:
        if profile != primary or assigned != {primary} or not frappe.db.exists("Role Profile", profile):
            return False
        return {row.role for row in frappe.get_cached_doc("Role Profile", profile).roles} == {primary}
    return True


def _role_choices():
    available = frappe.get_all("Role", filters={"name": ("in", PRIMARY_ROLES), "disabled": 0}, pluck="name")
    return [role for role in PRIMARY_ROLES if role in available]


def _role_state(row, roles):
    role = _primary(roles)
    return {
        "role": role,
        "roles": sorted(roles),
        "manageable": _eligible(row, roles),
        "merge_approver": MERGE_APPROVER in roles,
        "merge_effective": role == "Sales Manager" and MERGE_APPROVER in roles,
    }


@frappe.whitelist(methods=["POST"])
def list_employees(search="", page=1, role=None):
    _authorize("list_employees")
    if not isinstance(search, str) or len(search) > 140:
        frappe.throw("Từ khóa không hợp lệ.", frappe.ValidationError)
    page = max(1, min(cint(page), 10000))
    if role and role not in (*PRIMARY_ROLES, MERGE_APPROVER):
        frappe.throw(_("Choose a valid role filter."))
    pattern = "%" + search.strip() + "%"
    filters = {"user_type": "System User"}
    if role:
        users = frappe.qb.DocType("User")
        has_role = frappe.qb.DocType("Has Role")
        # Filter the primary role, even when native CRM assigned lower sales roles too.
        higher_roles = PRIMARY_ROLES[:PRIMARY_ROLES.index(role)] if role in PRIMARY_ROLES else ()
        membership = (frappe.qb.from_(has_role).select(has_role.parent)
                      .where((has_role.parenttype == "User") & (has_role.parentfield == "roles")))
        query = frappe.qb.from_(users).select(users.name).where(users.name.isin(membership.where(has_role.role == role)))
        if higher_roles:
            query = query.where(users.name.notin(membership.where(has_role.role.isin(higher_roles))))
        filtered_names = [name for (name,) in query.run()]
        if role == "System Manager":
            filtered_names.append("Administrator")
        if not filtered_names:
            return {"items": [], "has_more": False, "roles": _role_choices()}
        filters["name"] = ("in", filtered_names)
    rows = frappe.get_list(
        "User", filters=filters,
        or_filters={"full_name": ("like", pattern), "email": ("like", pattern)},
        fields=["name", "full_name", "email", "enabled", "creation", "role_profile_name", "user_type", "user_image"],
        order_by="creation desc, name asc", start=(page - 1) * 20, page_length=21,
    )
    employees = rows[:20]
    by_user = {row.name: [] for row in employees}
    if by_user:
        assigned = frappe.get_all(
            "Has Role", filters={"parent": ("in", list(by_user)), "parenttype": "User", "parentfield": "roles"},
            fields=["parent", "role"],
        )
        for entry in assigned:
            by_user[entry.parent].append(entry.role)
    for row in employees:
        roles = set(by_user[row.name]) if row.name != "Administrator" else {"System Manager"}
        row.update(_role_state(row, roles))
        row.pop("user_type", None)
    _audit("C360 Administration: viewed employee list")
    return {"items": employees, "has_more": len(rows) > 20, "roles": _role_choices()}


def _employee(name, *, for_update=False):
    if not isinstance(name, str) or not name or len(name) > 140:
        frappe.throw("Mã nhân viên không hợp lệ.", frappe.ValidationError)
    if for_update:
        # Serialize changes so two administrators cannot remove the final System Manager.
        frappe.db.get_value("User", "Administrator", "name", for_update=True)
    user = frappe.get_doc("User", name, for_update=for_update)
    roles = {row.role for row in user.roles}
    if not _eligible(user, roles):
        frappe.throw(_("Manage this protected account in Desk."), frappe.PermissionError)
    return user, roles


def _validate_access(role, enabled, merge_approver):
    if type(enabled) is not bool or type(merge_approver) is not bool:
        frappe.throw(_("Enabled and Merge Approver must be boolean."))
    if role not in _role_choices():
        frappe.throw(_("Choose an enabled CRM role."))
    if merge_approver and (role != "Sales Manager" or not frappe.db.exists(
        "Role", {"name": MERGE_APPROVER, "disabled": 0},
    )):
        frappe.throw(_("Merge Approver requires the Sales Manager role."))


def _details(user):
    from crm.api.user import has_password

    return {
        "name": user.name, "email": user.email, "full_name": user.full_name, "enabled": bool(user.enabled),
        "modified": str(user.modified), "role_profile_name": user.role_profile_name,
        "can_invite": bool(user.enabled and not has_password(user.name)),
        "assignments": {doctype: frappe.db.count(doctype, {field: user.name}) for doctype, field in ASSIGNMENTS},
        **_role_state(user, {row.role for row in user.roles}),
    }


@frappe.whitelist(methods=["POST"])
def get_employee(name):
    _authorize("get_employee")
    user, _ = _employee(name)
    return _details(user)


def _send_invitation(user):
    frappe.db.savepoint("employee_invitation")
    try:
        user.flags.delay_emails = True
        user.send_welcome_mail_to_user()
    except frappe.OutgoingEmailError:
        frappe.db.rollback(save_point="employee_invitation")
        frappe.clear_last_message()
        return "failed"
    return "queued"


@frappe.whitelist(methods=["POST"])
def create_employee(full_name, email, role, enabled, merge_approver=False):
    _authorize("create_employee")
    _validate_access(role, enabled, merge_approver)
    if (not isinstance(full_name, str) or not isinstance(email, str)
        or not 1 < len(full_name.strip()) <= 140 or not 1 < len(email.strip()) <= 140
        or any(ord(char) < 32 for char in full_name)):
        frappe.throw(_("Enter a full name and valid email address."))
    email = email.strip().lower()
    if validate_email_address(email) != email:
        frappe.throw(_("Enter a valid email address."))
    if frappe.db.exists("User", email):
        frappe.throw(_("This email address already has a Frappe account."))
    if frappe.db.exists("CRM Invitation", {"email": email, "status": "Pending"}):
        frappe.throw(_("This email has a pending CRM invitation. Resolve that invitation before creating a user."))
    roles = [{"role": role}]
    if merge_approver:
        roles.append({"role": MERGE_APPROVER})
    user = frappe.get_doc({
        "doctype": "User", "email": email, "first_name": full_name.strip(), "enabled": int(enabled),
        "user_type": "System User", "roles": roles, "send_welcome_email": 0, "default_app": "crm",
    }).insert()
    _audit("C360 Administration: created employee", user.name)
    invitation = _send_invitation(user) if enabled else None
    return {**_details(user), "invitation": invitation}


@frappe.whitelist(methods=["POST"])
def invite_employee(name):
    _authorize("invite_employee")
    user, _ = _employee(name, for_update=True)
    if not _details(user)["can_invite"]:
        frappe.throw(_("Only enabled accounts without a password can receive a setup invitation."))
    result = _send_invitation(user)
    _audit(f"C360 Administration: employee invitation {result}", user.name)
    return {"invitation": result}


def _revoke_sessions(name):
    try:
        clear_sessions(user=name, force=True)
    except Exception:
        frappe.logger("c360_administration").exception("Failed to revoke employee sessions")


def _guard_system_manager(user, role, enabled):
    roles = frappe.qb.DocType("Has Role")
    users = frappe.qb.DocType("User")
    if user.enabled and _primary({row.role for row in user.roles}) == "System Manager" and (
        role != "System Manager" or not enabled
    ):
        others = (frappe.qb.from_(roles).join(users).on(users.name == roles.parent).select(users.name)
                  .where((roles.parenttype == "User") & (roles.parentfield == "roles")
                         & (roles.role == "System Manager") & (users.enabled == 1)
                         & (users.user_type == "System User") & users.name.notin((user.name, "Administrator")))
                  .limit(1).for_update().run())
        if not others:
            frappe.throw(_("Keep at least one enabled System Manager besides Administrator."))


def _save_access(user, roles, enabled, *, role=None, merge_approver=False):
    previous_role = _primary(roles)
    _guard_system_manager(user, role or previous_role, enabled)
    enabled_changed = bool(user.enabled) != enabled
    role_changed = role is not None and (
        previous_role != role or (MERGE_APPROVER in roles) != merge_approver
    )
    if role_changed:
        user.role_profile_name = None
        user.set("roles", [row for row in user.roles if row.role in IMPLICIT_ROLES])
        user.append("roles", {"role": role})
        if merge_approver:
            user.append("roles", {"role": MERGE_APPROVER})
    if enabled_changed or role_changed:
        user.enabled = int(enabled)
        user.save()
        frappe.db.after_commit.add(partial(_revoke_sessions, user.name))
        _audit(
            f"C360 Administration: employee role {previous_role} -> {role or previous_role}, "
            f"merge approval {MERGE_APPROVER in roles} -> {merge_approver if role else MERGE_APPROVER in roles}, "
            f"enabled -> {enabled}",
            user.name,
        )
    return _details(user)


@frappe.whitelist(methods=["POST"])
def save_employee(name, role, enabled, merge_approver, modified):
    _authorize("save_employee")
    _validate_access(role, enabled, merge_approver)
    user, roles = _employee(name, for_update=True)
    if str(user.modified) != modified:
        frappe.throw(_("This account changed. Reload it before saving."), frappe.TimestampMismatchError)
    activated = enabled and not user.enabled
    result = _save_access(user, roles, enabled, role=role, merge_approver=merge_approver)
    if activated and result["can_invite"] and not user.last_reset_password_key_generated_on:
        invitation = _send_invitation(user)
        result.update(invitation=invitation, modified=str(user.modified))
    return result


@frappe.whitelist(methods=["POST"])
def set_employee_role(name, role):
    _authorize("set_employee_role")
    if role not in ROLES:
        frappe.throw(_("Choose Sales User or Sales Manager."))
    user, roles = _employee(name, for_update=True)
    if not set(ROLES).intersection(roles) or not roles.issubset(set(ROLES) | IMPLICIT_ROLES):
        frappe.throw(_("Use CRM Settings to manage this account."), frappe.PermissionError)
    _validate_access(role, bool(user.enabled), False)
    return _save_access(user, roles, bool(user.enabled), role=role)


@frappe.whitelist(methods=["POST"])
def set_employee_enabled(name, enabled):
    _authorize("set_employee_enabled")
    if type(enabled) is not bool:
        frappe.throw("Trạng thái phải là boolean.", frappe.ValidationError)
    user, roles = _employee(name, for_update=True)
    return _save_access(user, roles, enabled)


@frappe.whitelist(methods=["POST"])
def permission_matrix():
    _authorize("permission_matrix")
    records = {}
    for doctype in DOCTYPES:
        meta = frappe.get_meta(doctype)
        records[doctype] = [
            {
                "role": rule.role, "level": rule.permlevel, "owner_only": bool(rule.if_owner),
                "operations": [op for op in OPERATIONS if rule.get(op)],
            }
            for rule in meta.permissions
            if rule.role in REPORT_ROLES or rule.role in IMPLICIT_ROLES
        ]
    _audit("C360 Administration: viewed permission matrix")
    return {"roles": REPORT_ROLES, "rules": records, "implicit_roles": sorted(IMPLICIT_ROLES)}


@frappe.whitelist(methods=["POST"])
def list_roles(search="", page=1):
    _authorize("list_roles")
    if not isinstance(search, str) or len(search) > 140:
        frappe.throw("Từ khóa không hợp lệ.", frappe.ValidationError)

    page = max(1, min(cint(page), 10000))
    roles = frappe.get_list(
        "Role", filters={"name": ("like", "%" + search.strip() + "%")},
        fields=["name", "disabled", "is_custom"],
        order_by="name asc", start=(page - 1) * 20, page_length=21,
    )
    counts = {row.name: set() for row in roles[:20]}
    if counts:
        assignments = frappe.get_all(
            "Has Role", filters={"role": ("in", list(counts)), "parenttype": "User", "parentfield": "roles"},
            fields=["role", "parent"],
        )
        users = {row.parent for row in assignments}
        employees = set(frappe.get_list(
            "User", filters={"name": ("in", list(users)), "user_type": "System User"},
            pluck="name", page_length=0,
        )) if users else set()
        for assignment in assignments:
            if assignment.parent in employees:
                counts[assignment.role].add(assignment.parent)
    for role in roles[:20]:
        role.employee_count = len(counts[role.name])

    _audit("C360 Administration: viewed role list")
    return {"items": roles[:20], "has_more": len(roles) > 20}
