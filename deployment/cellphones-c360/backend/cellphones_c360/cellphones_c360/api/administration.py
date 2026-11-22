import frappe


@frappe.whitelist(methods=["GET"])
def get_access():
    return {
        "administration": bool(
            "System Manager" in frappe.get_roles()
            and frappe.has_permission("User", "read")
        )
    }
