import frappe
from frappe.sessions import clear_sessions
from frappe.utils import cint

from cellphones_c360.api.access import require_session_csrf
from cellphones_c360.api.registration import ROLES

IMPLICIT_ROLES = {"All", "Desk User", "Guest"}
REPORT_ROLES = ("Administrator", *ROLES)
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


def _eligible(name, roles, user_type, role_profile):
    assigned = set(roles)
    return bool(
        name not in ("Administrator", "Guest")
        and user_type == "System User"
        and not role_profile
        and assigned.intersection(ROLES)
        and assigned.issubset(set(ROLES) | IMPLICIT_ROLES)
    )


def _role_choices():
    return [role for role in ROLES if frappe.db.exists("Role", {"name": role, "disabled": 0})]


@frappe.whitelist(methods=["POST"])
def list_employees(search="", page=1):
    _authorize("list_employees")
    if not isinstance(search, str) or len(search) > 140:
        frappe.throw("Từ khóa không hợp lệ.", frappe.ValidationError)
    page = max(1, min(cint(page), 10000))
    pattern = "%" + search.strip() + "%"
    rows = frappe.get_list(
        "User", filters={"user_type": "System User"},
        or_filters={"full_name": ("like", pattern), "email": ("like", pattern)},
        fields=["name", "full_name", "email", "enabled", "creation", "role_profile_name", "user_type"],
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
        row.roles = sorted(set(by_user[row.name]))
        row.manageable = _eligible(row.name, row.roles, row.user_type, row.role_profile_name)
        row.pop("role_profile_name", None)
        row.pop("user_type", None)
    _audit("C360 Administration: viewed employee list")
    return {"items": employees, "has_more": len(rows) > 20, "roles": _role_choices()}


def _employee(name):
    if not isinstance(name, str) or not name or len(name) > 140:
        frappe.throw("Mã nhân viên không hợp lệ.", frappe.ValidationError)
    user = frappe.get_doc("User", name, for_update=True)
    roles = [row.role for row in user.roles]
    if not _eligible(user.name, roles, user.user_type, user.role_profile_name):
        frappe.throw("Tài khoản này được bảo vệ khỏi thay đổi trong Administration.", frappe.PermissionError)
    return user, roles


@frappe.whitelist(methods=["POST"])
def set_employee_role(name, role):
    _authorize("set_employee_role")
    if role not in _role_choices():
        frappe.throw("Chọn Sales User hoặc Sales Manager.", frappe.ValidationError)
    user, roles = _employee(name)
    previous = sorted(set(roles).intersection(ROLES))
    if previous != [role]:
        retained = [row for row in user.roles if row.role not in ROLES]
        user.set("roles", retained)
        user.append("roles", {"role": role})
        user.save()
    _audit(f"C360 Administration: employee role {', '.join(previous)} -> {role}", user.name)
    return {"name": user.name, "roles": sorted({row.role for row in user.roles})}


def _revoke_sessions(name):
    try:
        clear_sessions(user=name, force=True)
    except Exception:
        frappe.logger("c360_administration").exception("Failed to revoke employee sessions")


@frappe.whitelist(methods=["POST"])
def set_employee_enabled(name, enabled):
    _authorize("set_employee_enabled")
    if type(enabled) is not bool:
        frappe.throw("Trạng thái phải là boolean.", frappe.ValidationError)
    user, _ = _employee(name)
    previous = bool(user.enabled)
    if previous != enabled:
        user.enabled = int(enabled)
        user.save()
        if not enabled:
            frappe.db.after_commit.add(lambda: _revoke_sessions(user.name))
    _audit(f"C360 Administration: employee enabled {previous} -> {enabled}", user.name)
    return {"name": user.name, "enabled": bool(user.enabled)}


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
