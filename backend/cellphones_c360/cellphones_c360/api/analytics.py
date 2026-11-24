from collections import Counter
from datetime import timedelta
from decimal import Decimal

import frappe
from frappe.model import get_permitted_fields
from frappe.utils import cint, get_datetime, now_datetime

PERIODS = {"all": None, "7d": 7, "30d": 30, "90d": 90}
VALID_ORDERS = {"Confirmed", "Processing", "Completed"}


def _readable(doctype, fields):
    return frappe.has_permission(doctype, "read") and set(fields).issubset(
        get_permitted_fields(doctype, permission_type="read") + ["name", "creation", "owner"]
    )


def _rows(doctype, fields, filters=()):
    start = 0
    while True:
        page = frappe.get_list(
            doctype,
            fields=fields,
            filters=list(filters),
            order_by="name asc",
            start=start,
            page_length=500,
        )
        yield from page
        if len(page) < 500:
            return
        start += len(page)


def _window(field, start, end):
    return [(field, "<", end)] + ([(field, ">=", start)] if start else [])


def _counts(counter, chronological=False):
    labels = sorted(counter) if chronological else sorted(counter, key=lambda key: (-counter[key], key))
    return [{"label": label, "count": counter[label]} for label in labels]


def _group(counter, value):
    counter[value or "Chưa xác định"] += 1


def _amount(value):
    return Decimal(str(value)) if value is not None else None


def _orders(start, end):
    fields = ["order_date", "order_status", "total_amount", "customer"]
    if not _readable("Customer Order", fields):
        return None, None

    statuses, trend, customers = Counter(), Counter(), Counter()
    valid = amounts = 0
    value = Decimal(0)
    for row in _rows("Customer Order", fields, _window("order_date", start, end)):
        _group(statuses, row.order_status)
        if row.order_date:
            trend[str(row.order_date)[:10]] += 1
        if row.order_status not in VALID_ORDERS:
            continue
        valid += 1
        if row.customer:
            customers[row.customer] += 1
        amount = _amount(row.total_amount)
        if amount is not None:
            value += amount
            amounts += 1

    return {
        "total": sum(statuses.values()),
        "validValue": value if valid == amounts else None,
        "averageValue": value / valid if valid and valid == amounts else None,
        "repeatCustomers": sum(count >= 2 for count in customers.values()),
        "byStatus": _counts(statuses),
        "trend": _counts(trend, chronological=True),
    }, customers


def _customers(start, end, order_counts):
    fields = ["name", "creation", "source_channel", "customer_type"]
    if not _readable("C360 Customer", fields):
        return None

    sources, types = Counter(), Counter()
    total = new = buyers = repeat = 0
    for row in _rows("C360 Customer", fields, _window("creation", None, end)):
        total += 1
        if order_counts is not None:
            count = order_counts[row.name]
            buyers += count >= 1
            repeat += count >= 2
        if not start or get_datetime(row.creation) >= start:
            new += 1
            _group(sources, row.source_channel)
            _group(types, row.customer_type)

    return {
        "total": total,
        "new": new,
        "withOrders": buyers if order_counts is not None else None,
        "repeat": repeat if order_counts is not None else None,
        "bySource": _counts(sources),
        "byType": _counts(types),
    }


def _leads(start, end):
    fields = ["name", "status", "source"]
    if not _readable("CRM Lead", fields):
        return None, None

    statuses, sources = Counter(), Counter()
    names = set()
    for row in _rows("CRM Lead", fields, _window("creation", start, end)):
        names.add(row.name)
        _group(statuses, row.status)
        _group(sources, row.source)
    return {
        "total": len(names),
        "byStatus": _counts(statuses),
        "bySource": _counts(sources),
    }, names


def _deals(start, end, lead_names):
    fields = ["status", "lead", "expected_deal_value", "currency"]
    if not _readable("CRM Deal", fields):
        return None

    status_fields = ["name", "type"]
    types = (
        {row.name: row.type for row in _rows("CRM Deal Status", status_fields)}
        if _readable("CRM Deal Status", status_fields)
        else {}
    )
    stages = Counter()
    won_leads = set()
    won = lost = 0
    pipeline_value = Decimal(0)
    complete = bool(types)
    known_outcomes = bool(types)
    for row in _rows("CRM Deal", fields, _window("creation", start, end)):
        _group(stages, row.status)
        category = types.get(row.status)
        if category == "Won":
            won += 1
            if lead_names is not None and row.lead in lead_names:
                won_leads.add(row.lead)
        elif category == "Lost":
            lost += 1
        elif category in {"Open", "Ongoing", "On Hold"}:
            amount = _amount(row.expected_deal_value)
            if amount is None or (amount and row.currency != "VND"):
                complete = False
            else:
                pipeline_value += amount
        else:
            known_outcomes = False
            complete = False

    return {
        "total": sum(stages.values()),
        "won": won if known_outcomes else None,
        "lost": lost if known_outcomes else None,
        "pipelineValue": pipeline_value if complete else None,
        "winRate": won / (won + lost) if known_outcomes and won + lost else None,
        "conversionRate": len(won_leads) / len(lead_names) if known_outcomes and lead_names else None,
        "byStage": _counts(stages),
    }


def _tickets(start, end):
    fields = ["created_date", "resolved_date", "ticket_status", "ticket_type"]
    if not _readable("Customer Support Ticket", fields):
        return None

    statuses, types, trend = Counter(), Counter(), Counter()
    durations = hours = 0
    for row in _rows("Customer Support Ticket", fields, _window("created_date", start, end)):
        _group(statuses, row.ticket_status)
        _group(types, row.ticket_type)
        opened = get_datetime(row.created_date)
        trend[opened.date().isoformat()] += 1
        if row.ticket_status in {"Resolved", "Closed"} and row.resolved_date:
            closed = get_datetime(row.resolved_date)
            if opened <= closed:
                durations += 1
                hours += (closed - opened).total_seconds() / 3600

    total = sum(statuses.values())
    return {
        "total": total,
        "resolutionRate": (statuses["Resolved"] + statuses["Closed"]) / total if total else None,
        "averageResolutionHours": hours / durations if durations else None,
        "byStatus": _counts(statuses),
        "byType": _counts(types),
        "trend": _counts(trend, chronological=True),
    }


ACTIVITIES = (
    ("CRM Call Log", "Cuộc gọi", "start_time", "type", "status", "owner", None),
    ("CRM Task", "Công việc", "creation", "title", "status", "assigned_to", None),
    ("CRM Deal", "Deal", "creation", "organization_name", "status", "deal_owner", None),
    ("Customer Order", "Đơn hàng", "order_date", "name", "order_status", "owner", "customer"),
    ("Customer Support Ticket", "Hậu mãi", "created_date", "subject", "ticket_status", "assigned_to", "customer"),
)


def _activities(start, end):
    activities = []
    for doctype, label, date_field, title, status, owner, customer in ACTIVITIES:
        fields = list(dict.fromkeys(field for field in ("name", date_field, title, status, owner, customer) if field))
        if not _readable(doctype, fields):
            continue
        for row in frappe.get_list(
            doctype, fields=fields, filters=_window(date_field, start, end),
            order_by=f"{date_field} desc, name desc", page_length=10,
        ):
            activities.append({
                "id": f"{doctype}/{row.name}",
                "type": label,
                "title": row.get(title) or row.name,
                "status": row.get(status),
                "employee": row.get(owner),
                "customer": row.get(customer) if customer else None,
                "date": get_datetime(row.get(date_field)).isoformat(),
            })
    return sorted(activities, key=lambda item: item["date"], reverse=True)[:10]


@frappe.whitelist(methods=["GET"])
def get_analytics_overview(period="all", activities=0):
    if period not in PERIODS:
        frappe.throw("Khoảng thời gian không hợp lệ.", frappe.ValidationError)
    today = now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
    end = today + timedelta(days=1)
    days = PERIODS[period]
    start = end - timedelta(days=days) if days else None
    orders, customers_with_orders = _orders(start, end)
    leads, lead_names = _leads(start, end)
    result = {
        "customers": _customers(start, end, customers_with_orders),
        "leads": leads,
        "deals": _deals(start, end, lead_names),
        "orders": orders,
        "tickets": _tickets(start, end),
    }
    if cint(activities):
        result["activities"] = _activities(start, end)
    return result
