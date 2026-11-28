import frappe
from frappe import _
from frappe.utils import add_days, get_datetime

ORDER = "Customer Order"


def create_for_order(name):
    order = frappe.get_doc(ORDER, name, for_update=True)
    order.check_permission("write")
    if order.care_task:
        return order.care_task
    if order.order_status != "Completed" or not order.completed_at:
        return None

    due = get_datetime(add_days(order.completed_at, 3))
    task = frappe.get_doc({
        "doctype": "CRM Task",
        "title": _("Post-purchase follow-up · {0}").format(order.name),
        "reference_doctype": ORDER,
        "reference_docname": order.name,
        "start_date": due.date(),
        "due_date": due,
        "status": "Todo",
        "priority": "Medium",
    }).insert()
    order.db_set("care_task", str(task.name), update_modified=False)
    return str(task.name)


def schedule_follow_ups():
    orders = frappe.get_all(
        ORDER, filters={"order_status": "Completed", "completed_at": ("is", "set"),
                        "care_task": ("is", "not set")},
        pluck="name", order_by="completed_at, name", page_length=100,
    )
    for name in orders:
        savepoint = "c360_care_order"
        frappe.db.savepoint(savepoint)
        try:
            create_for_order(name)
        except (frappe.ValidationError, frappe.DoesNotExistError):
            frappe.db.rollback(save_point=savepoint)
            frappe.log_error(title=_("Could not schedule customer care"))
