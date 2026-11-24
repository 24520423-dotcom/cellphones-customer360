from collections import Counter
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import frappe
from frappe.model import get_permitted_fields
from frappe.utils import cint, get_datetime, now_datetime

from cellphones_c360.api.orders import is_confirmed_purchase
from cellphones_c360.api.segments import ONLINE, ORDER_FIELDS, SEGMENTS, summarize_many

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

    income = None
    payment_fields = ["order_status", "payment_status", "total_amount", "paid_at"]
    if _readable("Customer Order", payment_fields):
        income = sum((
            _amount(row.total_amount) or Decimal(0)
            for row in _rows(
                "Customer Order", payment_fields,
                _window("paid_at", start, end) + [("order_status", "=", "Completed"), ("payment_status", "=", "Paid")],
            )
            if is_confirmed_purchase(row)
        ), Decimal(0))
    return {
        "total": sum(statuses.values()),
        "completed": statuses["Completed"],
        "cancelled": statuses["Cancelled"],
        "validValue": value if valid == amounts else None,
        "confirmedReceipts": income,
        "averageValue": value / valid if valid and valid == amounts else None,
        "repeatCustomers": sum(count >= 2 for count in customers.values()),
        "byStatus": _counts(statuses),
        "trend": _counts(trend, chronological=True),
    }, customers


def _identity(start, end):
    """Current status of received records; backlog is deliberately not period-limited."""
    doctype = "C360 Source Record"
    if not _readable(doctype, ["processing_status", "received_at"]):
        return None
    statuses = Counter(row.processing_status for row in _rows(
        doctype, ["processing_status"], _window("received_at", start, end),
    ))
    pending = sum(1 for _ in _rows(doctype, ["name"], [
        ("processing_status", "=", "Needs Review"),
    ]))
    return {
        "total": sum(statuses.values()),
        "created": statuses["Created"],
        "linked": statuses["Linked"],
        "needsReview": statuses["Needs Review"],
        "invalid": statuses["Invalid"],
        "currentPending": pending,
        "byStatus": _counts(statuses),
    }


def _interaction_channels(customers, end):
    """Channel mix of visible profiles, using origin, linked intake and valid orders."""
    source_fields = ["customer", "source_channel", "processing_status", "received_at"]
    order_fields = ["customer", "sales_channel", "order_status", "order_date"]
    if not (_readable("C360 Source Record", source_fields)
            and _readable("Customer Order", order_fields)):
        return None
    channels = {row.name: {row.source_channel} if row.source_channel else set() for row in customers}
    names = list(channels)
    for offset in range(0, len(names), 500):
        batch = names[offset:offset + 500]
        for row in _rows("C360 Source Record", source_fields,
                         _window("received_at", None, end) + [
                             ("customer", "in", batch),
                             ("processing_status", "in", ["Created", "Linked"]),
                         ]):
            if row.customer in channels and row.source_channel:
                channels[row.customer].add(row.source_channel)
        for row in _rows("Customer Order", order_fields,
                         _window("order_date", None, end) + [
                             ("customer", "in", batch),
                             ("order_status", "in", sorted(VALID_ORDERS)),
                         ]):
            if row.customer in channels and row.sales_channel:
                channels[row.customer].add(row.sales_channel)
    counts = Counter({"Online only": 0, "Offline only": 0, "Omnichannel": 0, "Unspecified": 0})
    for values in channels.values():
        online = bool(values & ONLINE)
        offline = "Store" in values
        key = ("Omnichannel" if online and offline else "Online only" if online
               else "Offline only" if offline else "Unspecified")
        counts[key] += 1
    return _counts(counts)


def _customers(start, end, order_counts):
    fields = ["name", "creation", "source_channel", "customer_type"]
    if not _readable("C360 Customer", fields):
        return None

    sources, types, channels, segment_counts = Counter(), Counter(), Counter(), Counter()
    total = new = buyers = 0
    identity_fields = ["phone_number", "email"]
    can_review_identities = _readable("C360 Customer", identity_fields)
    filters = _window("creation", None, end) + [("merged_into", "is", "not set")]
    rows = list(_rows("C360 Customer", fields + (identity_fields if can_review_identities else []), filters))
    for offset in range(0, len(rows), 500):
        batch = rows[offset:offset + 500]
        classifications = summarize_many(batch, as_of=(end - timedelta(days=1)).date())
        for row in batch:
            total += 1
            segment_counts.update(classifications[row.name]["segments"])
            if order_counts is not None:
                count = order_counts[row.name]
                buyers += count >= 1
            if not start or get_datetime(row.creation) >= start:
                new += 1
                _group(sources, row.source_channel)
                _group(types, row.customer_type)
                channels["Online" if row.source_channel in ONLINE else "Offline" if row.source_channel == "Store" else "Unspecified"] += 1

    needs_review = None
    if _readable("C360 Source Record", ["processing_status", "received_at"]):
        needs_review = sum(1 for _ in _rows("C360 Source Record", ["name"],
            _window("received_at", start, end) + [("processing_status", "=", "Needs Review")]))
    duplicate_customers = None
    if can_review_identities:
        usage = {
            field: Counter(row[field].casefold() for row in rows if row.get(field))
            for field in identity_fields
        }
        duplicate_customers = sum(
            any(row.get(field) and usage[field][row[field].casefold()] > 1 for field in identity_fields)
            for row in rows
        )

    return {
        "total": total,
        "new": new,
        "withOrders": buyers if order_counts is not None else None,
        "repeat": segment_counts["returning"] if _readable("Customer Order", ORDER_FIELDS) else None,
        "bySource": _counts(sources),
        "byChannel": _counts(channels),
        "interactionChannels": _interaction_channels(rows, end),
        "byType": _counts(types),
        "segments": _counts(Counter({SEGMENTS[key]: value for key, value in segment_counts.items()})),
        "pendingIdentityReviews": needs_review,
        "duplicateCustomers": duplicate_customers,
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
    converted_leads = set()
    won = lost = 0
    pipeline_value = Decimal(0)
    complete = bool(types)
    known_outcomes = bool(types)
    for row in _rows("CRM Deal", fields, _window("creation", start, end)):
        _group(stages, row.status)
        if lead_names is not None and row.lead in lead_names:
            converted_leads.add(row.lead)
        category = types.get(row.status)
        if category == "Won":
            won += 1
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
        "conversionRate": len(converted_leads) / len(lead_names) if lead_names else None,
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
        "backlog": statuses["Open"] + statuses["Pending"] + statuses["In Progress"],
        "resolved": statuses["Resolved"] + statuses["Closed"],
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
def get_analytics_overview(period="all", activities=0, from_date=None, to_date=None):
    if from_date or to_date:
        try:
            first = date.fromisoformat(from_date or "")
            last = date.fromisoformat(to_date or "")
            if first > last:
                raise ValueError
            start = datetime.combine(first, time.min)
            end = datetime.combine(last + timedelta(days=1), time.min)
        except (TypeError, ValueError, OverflowError):
            frappe.throw("Khoảng ngày không hợp lệ.", frappe.ValidationError)
    else:
        start, end = _preset_window(period)
    orders, customers_with_orders = _orders(start, end)
    leads, lead_names = _leads(start, end)
    result = {
        "customers": _customers(start, end, customers_with_orders),
        "identity": _identity(start, end),
        "leads": leads,
        "deals": _deals(start, end, lead_names),
        "orders": orders,
        "tickets": _tickets(start, end),
    }
    if cint(activities):
        result["activities"] = _activities(start, end)
    return result


@frappe.whitelist(methods=["GET"])
def get_access():
    return {"canRead": any(
        frappe.has_permission(doctype, "read")
        for doctype in ("C360 Customer", "Customer Order", "Customer Support Ticket", "CRM Lead", "CRM Deal")
    )}


def _preset_window(period):
    if period not in PERIODS:
        frappe.throw("Khoảng thời gian không hợp lệ.", frappe.ValidationError)
    today = now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
    end = today + timedelta(days=1)
    days = PERIODS[period]
    start = end - timedelta(days=days) if days else None
    return start, end
