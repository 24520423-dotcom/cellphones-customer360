from itertools import count

import frappe
from frappe.model import get_permitted_fields

from cellphones_c360.api.crm_links import related_records, visible_doc
from cellphones_c360.api.orders import is_confirmed_purchase
from cellphones_c360.api.segments import SEGMENTS, UNRESOLVED_TICKET_STATES, summarize, summarize_many
from cellphones_c360.api.timeline import build_timeline, iso_timestamp


@frappe.whitelist()
def get_customer_360(customer_id):
    # 1. Lấy hồ sơ khách hàng
    customer = frappe.get_doc("C360 Customer", customer_id)
    customer.check_permission("read")
    customer.apply_fieldlevel_read_permissions()
    merged_into = visible_doc("C360 Customer", customer.get("merged_into"))
    crm = related_records(customer)
    contacts = crm["Contact"]

    customer_data = {
        "name": customer.name,
        "customer_name": customer.get("customer_name"),
        "phone_number": customer.get("phone_number"),
        "email": customer.get("email"),
        "customer_type": customer.get("customer_type"),
        "customer_status": customer.get("customer_status"),
        "source_channel": customer.get("source_channel"),
        "marketing_consent": customer.get("marketing_consent"),
        "crm_contact": next((row.name for row in contacts if row.name == customer.get("crm_contact")), None),
        "crm_lead": next((row.name for row in crm["CRM Lead"] if row.name == customer.get("crm_lead")), None),
        "modified": str(customer.modified),
        "created_at": iso_timestamp(customer.creation),
        "modified_at": iso_timestamp(customer.modified),
        "is_merged": bool(customer.get("merged_into")),
        "merged_into": merged_into.name if merged_into else None,
    }

    leads = [
        {
            "name": lead.name,
            "lead_name": lead.lead_name,
            "email": lead.email,
            "mobile_no": lead.mobile_no,
            "status": lead.status,
            "lead_owner": lead.lead_owner,
            "converted": lead.converted,
        }
        for lead in crm["CRM Lead"]
    ]
    deals = crm["CRM Deal"]

    # 4. Lấy lịch sử đơn hàng của khách hàng
    orders = []

    can_read_orders = frappe.has_permission("Customer Order", "read")
    order_names = (
        frappe.get_list(
            "Customer Order",
            filters={"customer": customer.name},
            pluck="name",
            order_by="creation desc",
            page_length=0,
        )
        if can_read_orders else []
    )

    for order_name in order_names:
        order = visible_doc("Customer Order", order_name)
        if not order:
            continue

        order_items = []

        for item in order.items or []:
            order_items.append({
                "product_code": item.product_code,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
            })

        orders.append({
            "name": order.name,
            "order_date": order.order_date,
            "sales_channel": order.sales_channel,
            "order_status": order.order_status,
            "payment_status": order.get("payment_status"),
            "fulfillment_method": order.get("fulfillment_method"),
            "fulfillment_status": order.get("fulfillment_status"),
            "paid_at": order.get("paid_at"),
            "completed_at": order.get("completed_at"),
            "total_amount": order.total_amount,
            "items": order_items,
        })

    # 5. Lấy lịch sử hỗ trợ khách hàng
    can_read_tickets = frappe.has_permission("Customer Support Ticket", "read")
    tickets = (
        frappe.get_list(
            "Customer Support Ticket",
            filters={"customer": customer.name},
            fields=["name", "subject", "ticket_type", "priority", "ticket_status",
                    "created_date", "related_order", "description", "assigned_to",
                    "resolution", "resolved_date"],
            order_by="created_date desc, name desc",
            page_length=0,
        )
        if can_read_tickets else []
    )

    # 6. Lấy thông tin liên hệ CRM Contact
    contact_data = None

    contact = contacts[0] if contacts else None
    if contact:
        contact_data = {
            "name": contact.name,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email_ids": [
                {
                    "email_id": row.email_id,
                    "is_primary": row.is_primary
                }
                for row in (contact.email_ids or [])
            ],
            "phone_nos": [
                {
                    "phone": row.phone,
                    "is_primary_phone": row.is_primary_phone
                }
                for row in (contact.phone_nos or [])
            ],
        }

    can_read_amounts = can_read_orders and "total_amount" in get_permitted_fields(
        "Customer Order", permission_type="read",
    )
    can_read_payment = {"order_status", "payment_status", "paid_at"}.issubset(
        get_permitted_fields("Customer Order", permission_type="read"),
    )
    segments = summarize(
        customer,
        [frappe._dict(order) for order in orders] if can_read_amounts and can_read_payment else None,
        any(ticket.get("ticket_status") in UNRESOLVED_TICKET_STATES for ticket in tickets),
    ) if not customer_data["is_merged"] else {"segments": [], "rfm": None}
    return {
        **segments,
        "segment_labels": SEGMENTS,
        "summary": {
            "recorded_order_value": sum(order["total_amount"] or 0 for order in orders) if can_read_amounts else None,
            "confirmed_spend": sum(
                order["total_amount"] or 0 for order in orders if is_confirmed_purchase(order)
            ) if can_read_amounts and can_read_payment else None,
        },
        "customer": customer_data,
        "contact": contact_data,
        "contacts": [{"name": row.name, "full_name": row.full_name} for row in contacts],
        "lead": leads[0] if leads else None,
        "leads": leads,
        "deals": deals,
        "orders": orders,
        "can_read_orders": bool(can_read_orders),
        "tickets": tickets,
        "can_read_tickets": bool(can_read_tickets),
    }

@frappe.whitelist()
def list_customers(search="", page=1, page_size=20, segment=""):
    # 1. Kiểm tra đăng nhập
    if frappe.session.user == "Guest":
        frappe.throw("Vui lòng đăng nhập.", frappe.PermissionError)

    # 2. Kiểm tra quyền đọc khách hàng
    if not frappe.has_permission("C360 Customer", "read"):
        frappe.throw("Không có quyền xem khách hàng.", frappe.PermissionError)
    if segment and segment not in SEGMENTS:
        frappe.throw("Phân khúc không hợp lệ.", frappe.ValidationError)

    # 3. Chuẩn hóa tham số phân trang
    page = max(1, frappe.utils.cint(page))
    page_size = max(1, min(100, frappe.utils.cint(page_size)))
    start = (page - 1) * page_size

    # 4. Tìm kiếm theo tên, số điện thoại hoặc email
    conditions = {}
    if frappe.get_meta("C360 Customer").has_field("merged_into"):
        conditions["merged_into"] = ("is", "not set")

    search_filters = []
    readable = set(get_permitted_fields("C360 Customer", permission_type="read"))
    if search and search.strip():
        keyword = f"%{search.strip()}%"
        search_filters = [
            [field, "like", keyword] for field in ("name", "customer_name", "phone_number", "email")
            if field in readable
        ]

    # 5. Lấy danh sách theo quyền của người đăng nhập
    criteria = {"filters": conditions, "or_filters": search_filters}
    fields = [field for field in ("name", "customer_name", "phone_number", "modified", "creation", "source_channel")
              if field in readable]
    if segment:
        customers = []
        total = 0
        classification = {}
        for offset in count(0, 500):
            batch = frappe.get_list("C360 Customer", fields=fields, start=offset, page_length=500,
                                    order_by="modified desc, name desc", **criteria)
            summaries = summarize_many(batch)
            for row in batch:
                if segment not in summaries[row.name]["segments"]:
                    continue
                if start <= total < start + page_size:
                    customers.append(row)
                    classification[row.name] = summaries[row.name]
                total += 1
            if len(batch) < 500:
                break
    else:
        customers = frappe.get_list("C360 Customer", fields=fields, start=start, page_length=page_size,
                                    order_by="modified desc, name desc", **criteria)
        classification = summarize_many(customers)
        counts = frappe.get_list("C360 Customer", fields=["count(name) as total"], page_length=1, **criteria)
        total = counts[0].total if counts else 0

    # 7. Chuẩn hóa dữ liệu hồ sơ Customer 360
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
            "updated_at_iso": iso_timestamp(customer.modified),
            "segments": classification[customer.name]["segments"],
        })

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "segment_labels": SEGMENTS,
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
        "segments": data["segments"],
        "owner": None,
        "updated_at": None,
        "leads": data["leads"],
        "deals": data["deals"],
        "orders": data["orders"],
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
    if not customer_id:
        frappe.throw("Thiếu mã khách hàng.", frappe.ValidationError)
    customer = frappe.get_doc("C360 Customer", customer_id)
    customer.check_permission("read")
    customer.apply_fieldlevel_read_permissions()
    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        frappe.throw("Tham số phân trang không hợp lệ.", frappe.ValidationError)
    if page < 1 or not 1 <= page_size <= 100:
        frappe.throw("Tham số phân trang không hợp lệ.", frappe.ValidationError)

    events = build_timeline(customer)
    start = (page - 1) * page_size
    return {"items": events[start:start + page_size], "total": len(events), "page": page, "page_size": page_size}


@frappe.whitelist(methods=["GET"])
def get_session_csrf_token():
    if frappe.session.user == "Guest":
        frappe.throw(
            "Vui lòng đăng nhập.",
            frappe.PermissionError
        )

    return frappe.sessions.get_csrf_token()
