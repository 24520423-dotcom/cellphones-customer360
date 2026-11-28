from collections import defaultdict
from decimal import Decimal

import frappe
from frappe.model import get_permitted_fields
from frappe.utils import getdate

from cellphones_c360.api.orders import is_confirmed_purchase

SEGMENTS = {
    "new": "New", "current": "Existing", "returning": "Returning",
    "high_value": "High Value", "inactive": "Inactive",
    "online": "Online", "offline": "Offline", "open_support": "Open Support",
}
ONLINE = {"Website", "App", "Facebook", "Zalo", "Hotline"}
UNRESOLVED_TICKET_STATES = {"Open", "Pending", "In Progress"}
NEW_DAYS = 30
INACTIVE_DAYS = 180
HIGH_VALUE = Decimal(20_000_000)
ORDER_FIELDS = ("customer", "order_status", "payment_status", "paid_at", "total_amount")


def summarize(customer, orders, has_open_support=False, as_of=None):
    as_of = getdate(as_of)
    created = getdate(customer.creation)
    labels = ["new" if (as_of - created).days < NEW_DAYS else "current"]
    if customer.source_channel in ONLINE:
        labels.append("online")
    elif customer.source_channel == "Store":
        labels.append("offline")
    if has_open_support:
        labels.append("open_support")

    rfm = None
    if orders is not None:
        purchases = [
            order for order in orders
            if is_confirmed_purchase(order) and getdate(order.paid_at) <= as_of
        ]
        last_purchase = max((getdate(order.paid_at) for order in purchases), default=None)
        monetary = sum((Decimal(str(order.total_amount or 0)) for order in purchases), Decimal(0))
        rfm = {
            "recency_days": (as_of - last_purchase).days if last_purchase else None,
            "frequency": len(purchases),
            "monetary": monetary,
        }
        if len(purchases) >= 2:
            labels.append("returning")
        if monetary >= HIGH_VALUE:
            labels.append("high_value")
        if (as_of - (last_purchase or created)).days >= INACTIVE_DAYS:
            labels.append("inactive")
    return {"segments": labels, "rfm": rfm}


def summarize_many(customers, as_of=None):
    if not customers:
        return {}
    names = [customer.name for customer in customers]
    orders = defaultdict(list)
    may_read_orders = frappe.has_permission("Customer Order", "read") and set(ORDER_FIELDS).issubset(
        get_permitted_fields("Customer Order", permission_type="read"),
    )
    if may_read_orders:
        for row in frappe.get_list(
            "Customer Order", fields=list(ORDER_FIELDS), page_length=0, filters={"customer": ("in", names)},
        ):
            orders[row.customer].append(row)

    open_support = set()
    if frappe.has_permission("Customer Support Ticket", "read") and {"customer", "ticket_status"}.issubset(
        get_permitted_fields("Customer Support Ticket", permission_type="read"),
    ):
        open_support.update(frappe.get_list(
            "Customer Support Ticket", pluck="customer", page_length=0,
            filters={"customer": ("in", names), "ticket_status": ("in", sorted(UNRESOLVED_TICKET_STATES))},
        ))
    return {
        customer.name: summarize(
            customer, orders.get(customer.name, []) if may_read_orders else None,
            customer.name in open_support, as_of=as_of,
        )
        for customer in customers
    }
