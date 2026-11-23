from datetime import date, datetime, time

import frappe
from frappe.utils import get_datetime

from cellphones_c360.api.leads import get_linked_history


def _visible_doc(doctype, name):
    if not name or not frappe.has_permission(doctype, "read"):
        return None

    try:
        doc = frappe.get_doc(doctype, name)
    except frappe.DoesNotExistError:
        return None
    if not doc.has_permission("read"):
        return None

    doc.apply_fieldlevel_read_permissions()
    return doc


def _customer_links(customer):
    """Resolve all accessible Leads/Deals for the same C360 Customer.

    ``crm_lead`` is retained for backward compatibility with old records;
    ``custom_c360_customer`` supports the new 1:N relationship.
    """
    customer_id = customer.name
    lead_ids = set()
    if frappe.has_permission("CRM Lead", "read"):
        meta = frappe.get_meta("CRM Lead")
        if meta.has_field("custom_c360_customer"):
            lead_ids.update(frappe.get_list(
                "CRM Lead", filters={"custom_c360_customer": customer_id},
                pluck="name", page_length=0,
            ))
        if customer.crm_lead:
            legacy = _visible_doc("CRM Lead", customer.crm_lead)
            if legacy:
                # Don't leak a Lead that has been explicitly assigned elsewhere.
                assigned = legacy.get("custom_c360_customer") if meta.has_field("custom_c360_customer") else None
                if not assigned or assigned == customer_id:
                    lead_ids.add(legacy.name)

    deal_ids = set()
    if frappe.has_permission("CRM Deal", "read"):
        deal_meta = frappe.get_meta("CRM Deal")
        if deal_meta.has_field("custom_c360_customer"):
            deal_ids.update(frappe.get_list(
                "CRM Deal", filters={"custom_c360_customer": customer_id},
                pluck="name", page_length=0,
            ))
        if lead_ids:
            deal_ids.update(frappe.get_list(
                "CRM Deal", filters={"lead": ["in", sorted(lead_ids)]},
                pluck="name", page_length=0,
            ))
    return sorted(lead_ids), sorted(deal_ids)


@frappe.whitelist(methods=["GET"])
def get_customer_360(customer_id):
    """Permission-aware, aggregated customer profile for the existing React UI."""
    customer = frappe.get_doc("C360 Customer", customer_id)
    customer.check_permission("read")
    customer.apply_fieldlevel_read_permissions()

    customer_data = {
        "name": customer.name,
        "customer_name": customer.customer_name,
        "phone_number": customer.phone_number,
        "email": customer.email,
        "customer_type": customer.customer_type,
        "customer_status": customer.customer_status,
        "source_channel": customer.source_channel,
        "crm_contact": customer.crm_contact,
        "crm_lead": customer.crm_lead,
        "modified": customer.modified,
    }

    lead_ids, deal_ids = _customer_links(customer)
    leads = []
    for name in lead_ids:
        lead = _visible_doc("CRM Lead", name)
        if lead:
            leads.append({
                "name": lead.name,
                "lead_name": lead.get("lead_name"),
                "email": lead.get("email"),
                "mobile_no": lead.get("mobile_no"),
                "status": lead.get("status"),
                "source": lead.get("source"),
                "creation": lead.get("creation"),
                "lead_owner": lead.get("lead_owner"),
                "converted": lead.get("converted"),
            })
    leads.sort(key=lambda item: item["name"])

    deals = []
    if frappe.has_permission("CRM Deal", "read"):
        fields = ["name", "lead", "status", "deal_owner", "probability", "expected_deal_value",
                  "total", "net_total", "creation", "closed_date"]
        meta = frappe.get_meta("CRM Deal")
        fields = [f for f in fields if f in ("name", "creation") or meta.has_field(f)]
        if deal_ids:
            deals = frappe.get_list(
                "CRM Deal", filters={"name": ["in", deal_ids]},
                fields=fields, order_by="creation desc", page_length=0,
            )

    orders = []
    if frappe.has_permission("Customer Order", "read"):
        order_ids = frappe.get_list(
            "Customer Order", filters={"customer": customer.name},
            pluck="name", order_by="creation desc", page_length=0,
        )
        for name in order_ids:
            order = _visible_doc("Customer Order", name)
            if not order:
                continue
            orders.append({
                "name": order.name,
                "order_date": order.order_date,
                "sales_channel": order.sales_channel,
                "order_status": order.order_status,
                "total_amount": order.total_amount,
                "items": [{
                    "product_code": item.product_code,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "amount": item.amount,
                } for item in (order.items or [])],
            })

    tickets = []
    if frappe.has_permission("Customer Support Ticket", "read"):
        tickets = frappe.get_list(
            "Customer Support Ticket", filters={"customer": customer.name},
            fields=["name", "subject", "ticket_type", "priority", "ticket_status",
                    "created_date", "related_order", "description", "assigned_to",
                    "resolution", "resolved_date"],
            order_by="created_date desc, name desc", page_length=0,
        )

    contact_data = None
    contact = _visible_doc("Contact", customer.crm_contact) if customer.crm_contact else None
    if contact:
        contact_data = {
            "name": contact.name,
            "first_name": contact.get("first_name"),
            "last_name": contact.get("last_name"),
            "email_ids": [{"email_id": row.email_id, "is_primary": row.is_primary}
                          for row in (contact.email_ids or [])],
            "phone_nos": [{"phone": row.phone, "is_primary_phone": row.is_primary_phone}
                          for row in (contact.phone_nos or [])],
        }

    return {
        "customer": customer_data,
        "contact": contact_data,
        "lead": leads[0] if leads else None,  # legacy callers
        "leads": leads,
        "deals": deals,
        "orders": orders,
        "tickets": tickets,
    }

@frappe.whitelist()
def list_customers(search="", page=1, page_size=20):
    # 1. Kiểm tra đăng nhập
    if frappe.session.user == "Guest":
        frappe.throw("Vui lòng đăng nhập.", frappe.PermissionError)

    # 2. Kiểm tra quyền đọc khách hàng
    if not frappe.has_permission("C360 Customer", "read"):
        frappe.throw("Không có quyền xem khách hàng.", frappe.PermissionError)

    # 3. Chuẩn hóa tham số phân trang
    page = max(1, frappe.utils.cint(page))
    page_size = max(1, min(100, frappe.utils.cint(page_size)))
    start = (page - 1) * page_size

    # 4. Tìm kiếm theo tên, số điện thoại hoặc email
    filters = []

    if search and search.strip():
        keyword = f"%{search.strip()}%"
        filters = [
            ["customer_name", "like", keyword],
            ["phone_number", "like", keyword],
            ["email", "like", keyword],
        ]

    # 5. Lấy danh sách theo quyền của người đăng nhập
    customers = frappe.get_list(
        "C360 Customer",
        fields=[
            "name",
            "customer_name",
            "phone_number",
            "email",
            "modified",
        ],
        or_filters=filters if filters else None,
        start=start,
        page_length=page_size,
        order_by="modified desc",
    )

    # 6. Đếm tổng số khách phù hợp
    # Cùng bộ lọc và quyền với danh sách
    total = len(
        frappe.get_list(
            "C360 Customer",
            fields=["name"],
            or_filters=filters if filters else None,
            limit_page_length=0,
        )
    )

    # 7. Chuẩn hóa dữ liệu cho React
    items = []

    for customer in customers:
        phone = customer.phone_number or ""

        items.append({
            "customer_id": customer.name,
            "display_name": customer.customer_name,
            "phone_masked": (
                "*" * max(0, len(phone) - 3) + phone[-3:]
                if phone else None
            ),
            "lead_count": None,
            "deal_count": None,
            "updated_at": str(customer.modified),
        })

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }

@frappe.whitelist()
def get_customer_profile(customer_id):
    if not customer_id:
        frappe.throw("Thiếu customer_id", frappe.ValidationError)

    # Tái sử dụng API Customer 360 hiện tại
    data = get_customer_360(customer_id)

    customer = data["customer"]
    return {
        "customer_id": customer["name"],
        "display_name": customer["customer_name"],
        "phone": customer["phone_number"],
        "email": customer["email"],
        "segments": [],
        "owner": None,
        "updated_at": str(customer.get("modified")) if customer.get("modified") else None,
        "leads": data["leads"],
        "deals": data["deals"],
        "orders": [
            {
                **order,
                "order_id": order["name"],
                "product": ", ".join(item.get("product_name") or "" for item in order.get("items", [])
                                     if item.get("product_name")),
                "purchased_at": order["order_date"],
                "channel": order["sales_channel"],
                "total": order["total_amount"],
                "status": order["order_status"],
            }
            for order in data["orders"]
        ],
        "after_sales_requests": [
            {
                "request_id": ticket["name"],
                "subject": ticket["subject"],
                "category": ticket["ticket_type"],
                "status": ticket["ticket_status"],
                "assigned_to": ticket["assigned_to"],
                "created_at": str(ticket["created_date"])
                    if ticket["created_date"] else None,
            }
            for ticket in data["tickets"]
        ],
    }


@frappe.whitelist()
def get_customer_timeline(customer_id, page=1, page_size=20):
    if frappe.session.user == "Guest":
        frappe.throw("Vui lòng đăng nhập", frappe.PermissionError)

    if not customer_id:
        frappe.throw("Thiếu customer_id", frappe.ValidationError)

    customer = frappe.get_doc("C360 Customer", customer_id)
    customer.check_permission("read")
    customer.apply_fieldlevel_read_permissions()

    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        frappe.throw("Tham số phân trang không hợp lệ", frappe.ValidationError)

    if page < 1 or not 1 <= page_size <= 100:
        frappe.throw("page hoặc page_size không hợp lệ", frappe.ValidationError)

    events = []

    def format_datetime(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return datetime.combine(value, time.min).isoformat()
        return get_datetime(value).isoformat()

    # 1. Lịch sử đơn hàng
    if frappe.has_permission("Customer Order", "read"):
        orders = frappe.get_list(
            "Customer Order",
            filters={"customer": customer_id},
            fields=[
                "name", "order_date", "order_status",
                "total_amount", "creation"
            ],
            limit_page_length=0
        )

        for order in orders:
            occurred_at = order.order_date or order.creation

            events.append({
                "id": f"order-{order.name}",
                "type": "order",
                "summary": (
                    f"Đơn hàng {order.name} - "
                    f"Trạng thái: {order.order_status}"
                ),
                "occurred_at": format_datetime(occurred_at),
                "related_doctype": "Customer Order",
                "related_name": order.name
            })

    # 2. Lịch sử yêu cầu hỗ trợ
    if frappe.has_permission("Customer Support Ticket", "read"):
        tickets = frappe.get_list(
            "Customer Support Ticket",
            filters={"customer": customer_id},
            fields=[
                "name", "subject", "ticket_status",
                "created_date", "creation"
            ],
            limit_page_length=0
        )

        for ticket in tickets:
            occurred_at = ticket.created_date or ticket.creation

            events.append({
                "id": f"ticket-{ticket.name}",
                "type": "support",
                "summary": (
                    f"Yêu cầu hỗ trợ: {ticket.subject} - "
                    f"Trạng thái: {ticket.ticket_status}"
                ),
                "occurred_at": format_datetime(occurred_at),
                "related_doctype": "Customer Support Ticket",
                "related_name": ticket.name
            })

    lead_ids, deal_ids = _customer_links(customer)
    references = {"CRM Lead": lead_ids, "CRM Deal": deal_ids}
    for item in get_linked_history(references):
        events.append({
            "id": item["id"],
            "type": item["kind"],
            "summary": " · ".join(value for value in (item["type"], item["title"], item["status"]) if value),
            "occurred_at": item["date"],
            "related_doctype": item["reference_type"],
            "related_name": item["reference_name"],
        })

    # Retain every confirmed source touchpoint, not only the first channel.
    if frappe.has_permission("C360 Customer Intake", "read"):
        intake_rows = frappe.get_list(
            "C360 Customer Intake", filters={"customer": customer_id, "status": ["in", ["Created", "Linked"]]},
            fields=["name", "source_channel", "source_reference", "received_at"],
            page_length=0,
        )
        for record in intake_rows:
            events.append({
                "id": f"intake-{record.name}",
                "type": "intake",
                "summary": f"Tiếp nhận từ {record.source_channel}: {record.source_reference}",
                "occurred_at": format_datetime(record.received_at),
                "related_doctype": "C360 Customer Intake",
                "related_name": record.name,
            })

    # 3. Sắp xếp mới nhất trước
    events.sort(
        key=lambda event: (
            event["occurred_at"] or "",
            event["id"]
        ),
        reverse=True
    )

    # 4. Phân trang
    total = len(events)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": events[start:end],
        "page": page,
        "page_size": page_size,
        "total": total
    }

@frappe.whitelist(methods=["GET"])
def get_session_csrf_token():
    if frappe.session.user == "Guest":
        frappe.throw(
            "Vui lòng đăng nhập.",
            frappe.PermissionError
        )

    return frappe.sessions.get_csrf_token()
