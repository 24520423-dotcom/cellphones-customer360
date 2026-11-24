import frappe


@frappe.whitelist(methods=["GET"])
def get_access():
    roles = set(frappe.get_roles())
    return {
        "administration": frappe.session.user == "Administrator" and frappe.has_permission("User", "read"),
        "nativeSales": bool(roles & {"System Manager", "Sales Manager", "Sales User"}),
        "customer360": bool(frappe.has_permission("C360 Customer", "read")),
    }
