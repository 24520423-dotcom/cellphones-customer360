# API Contract – CellphoneS Customer 360

> Phiên bản: 2.0 – bản cập nhật theo kiến trúc Frappe CRM native, chờ nhóm rà soát kỹ thuật.  
> Ngày: 24/11/2026.  
> Hệ thống: Frappe Framework 15.126.1, Frappe CRM 1.92.0, Custom App `cellphones_c360` 0.0.1, Vue.js và frappe-ui.  
> Base URL phát triển: `http://crm.localhost:8000`.

## 1. Mục đích và phạm vi

Thống nhất giao tiếp giữa giao diện Frappe CRM và backend Frappe/Custom App. Ưu tiên sử dụng chức năng và API gốc cho nghiệp vụ CRM tiêu chuẩn; chỉ mở rộng khi cần nghiệp vụ Customer 360 của nhóm. Không yêu cầu xây dựng lại frontend hoặc hệ thống đăng nhập độc lập.

Contract 1.0 ngày 17/11/2026 là tài liệu đề xuất theo kiến trúc frontend cũ. Các endpoint đề xuất trong v1.0 không mặc nhiên tồn tại. Phiên bản này mô tả các API đã xác định trong luồng tích hợp hiện tại và giữ các yêu cầu nghiệp vụ chưa hoàn tất ở trạng thái cần rà soát. Phân công triển khai và thay đổi contract cần nhóm thống nhất qua commit/PR.

| Trạng thái | Ý nghĩa |
|---|---|
| VERIFIED-UI | Đã quan sát dữ liệu hiển thị qua giao diện Frappe CRM, bằng Administrator; chưa chứng minh mọi role hay mọi HTTP method |
| VERIFIED-GET | Đã kiểm thử đọc dữ liệu qua REST trên site ở lần kiểm tra trước |
| AVAILABLE / UNTESTED | Có chức năng/API nền tảng nhưng chưa kiểm thử cụ thể trong phạm vi hiện tại |
| REVIEW | Có module hoặc DocType liên quan; cần đối chiếu mã nguồn, tham số, response và quyền trước khi xác nhận endpoint |
| PLANNED | Yêu cầu nghiệp vụ hoặc tích hợp chưa hoàn thành |

## 2. Quy ước chung

| Loại | Đường dẫn | HTTP response envelope |
|---|---|---|
| REST Frappe | `/api/resource/{URL-encoded DocType}` | `{ "data": ... }` |
| Whitelisted custom method | `/api/method/cellphones_c360.api.{module}.{function}` | `{ "message": ... }` |

- Đọc dữ liệu: GET REST hoặc gọi phương thức đọc bằng client Frappe. Ghi dữ liệu: POST tạo bản ghi/thực hiện nghiệp vụ, PUT cập nhật REST. Phương thức HTTP thực tế của custom method cần được xác nhận; `frappe-ui.call()` xử lý gọi phương thức và trả payload, không đồng nhất với kiểm thử GET trực tiếp.
- Định danh khách hàng là chuỗi `C360 Customer.name`, không tự sinh ID từ frontend và không coi ID Lead là ID khách hàng. Dữ liệu hiện có ID chưa đồng nhất, cần chuẩn hóa có kế hoạch, giữ nguyên liên kết.
- Giá trị tiền dùng số VND; không dùng chuỗi định dạng tiền trong payload. Giá trị đơn hàng, giá trị Deal dự kiến và doanh thu thực tế là các khái niệm khác nhau.
- Ngày không có giờ: `YYYY-MM-DD`. Ngày giờ hiện có thể là chuỗi thời gian Frappe, không cam kết luôn có offset ISO 8601. Chuẩn hóa cách hiển thị và xác định timezone trước khi đổi contract.
- Phân trang Customer 360: `page` từ 1, `page_size` mặc định 20, tối đa 100 theo quy ước cần kiểm thử biên; payload gồm `items`, `page`, `page_size`, `total`.
- REST: URL-encode DocType, `fields`, `filters` và các tham số cần thiết; quyền đọc trường phụ thuộc cấu hình Frappe.

## 3. Xác thực, phân quyền và lỗi

Frontend chạy cùng origin với backend, tận dụng Frappe Session và frappe-ui. Không cần thiết kế lại CORS cho một frontend độc lập. Tuân thủ cơ chế CSRF của Frappe khi ghi dữ liệu. Không lưu mật khẩu, token, session cookie trong mã nguồn.

| Endpoint nền tảng | Mục đích | Trạng thái |
|---|---|---|
| `POST /api/method/login` | Đăng nhập Frappe (`usr`, `pwd`) | AVAILABLE / UNTESTED ở mức API riêng |
| `GET /api/method/frappe.auth.get_logged_user` | Người dùng của phiên hiện tại | AVAILABLE / UNTESTED |
| `POST /api/method/logout` | Đăng xuất | AVAILABLE / UNTESTED ở mức API riêng |

Không dùng Administrator làm tài khoản mặc định cho nhân viên. Module `registration.py`, `administration.py`, `employee_administration.py`, `access.py` và DocType `C360 Registration Request` đã có trong Custom App; cần đọc mã nguồn để xác nhận tên method, payload, quy trình duyệt và quyền. Không tiếp tục sử dụng tên `api.auth.*` đề xuất trong v1.0 nếu chưa xác nhận.

Mọi API truy cập hồ sơ khách hàng phải kiểm tra phiên, quyền DocType, quyền tài liệu và quyền trường trên server. Không dùng `ignore_permissions=True` để vượt quyền dữ liệu khách hàng. Ẩn nút ở frontend không thay thế phân quyền backend. Kiểm thử Guest và các role nghiệp vụ. Xử lý lỗi theo response thực tế của Frappe, không giả định mọi 403 là hết phiên hoặc mọi lỗi validation là 422.

### Ma trận quyền mục tiêu (chưa xác nhận cấu hình thực tế)

| Vai trò nghiệp vụ | Leads / Deals | Customer 360 | Orders / After-sales | Analytics |
|---|---|---|---|---|
| Administrator | Quản trị | Quản trị | Quản trị | Toàn bộ |
| Sales Manager | Phạm vi đội | Phạm vi đội | Theo quyền | Tổng hợp đội |
| Sales User | Được phân công | Theo quyền | Theo quyền | Dữ liệu được phép |
| CSKH | Theo nhu cầu và quyền | Khách được hỗ trợ | Xử lý hỗ trợ được phân công | Giới hạn |
| Guest | Không | Không | Không | Không |

Tên role nghiệp vụ và quyền cụ thể cần đối chiếu role/permission thực tế trước khi triển khai.

## 4. Mô hình dữ liệu Customer 360

| DocType | Vai trò / quan hệ xác định |
|---|---|
| `C360 Customer` | Hồ sơ tập trung; `crm_contact` Link tới `Contact`; `crm_lead` Link tới `CRM Lead` |
| `CRM Lead` | Khách hàng tiềm năng có sẵn của CRM |
| `CRM Deal` | Cơ hội bán hàng; liên kết Lead trong luồng tổng hợp hiện tại |
| `Contact` | Thông tin liên hệ |
| `Customer Order` | `customer` Link tới C360 Customer; `items` là bảng con Customer Order Item |
| `Customer Order Item` | Chi tiết sản phẩm, số lượng, đơn giá, thành tiền |
| `Customer Support Ticket` | `customer` Link tới C360 Customer; `related_order` Link tới Customer Order; `assigned_to` Link tới User |
| `C360 Registration Request` | Yêu cầu đăng ký; quy trình và quyền cần rà soát |

Mô hình hiện tại tổng hợp Deal thông qua Lead được liên kết trong hồ sơ. Không mặc nhiên bao phủ mọi Deal không có Lead hoặc nhiều Lead của cùng một khách hàng. Cần hoàn thiện quy tắc nhận diện, chống trùng, hợp nhất và bảo toàn lịch sử đa kênh.

## 5. API nền tảng Leads và Deals

Tận dụng màn hình và nghiệp vụ có sẵn của Frappe CRM. Các API REST sau là tham chiếu; không cần xây dựng lại CRUD riêng nếu chức năng gốc đáp ứng yêu cầu.

| Method | Endpoint | Trạng thái |
|---|---|---|
| GET | `/api/resource/CRM%20Lead` | VERIFIED-GET (lần kiểm tra trước) |
| GET | `/api/resource/CRM%20Lead/{name}` | AVAILABLE / UNTESTED |
| POST | `/api/resource/CRM%20Lead` | AVAILABLE / UNTESTED |
| PUT | `/api/resource/CRM%20Lead/{name}` | AVAILABLE / UNTESTED |
| GET | `/api/resource/CRM%20Deal` | VERIFIED-GET (lần kiểm tra trước) |
| GET | `/api/resource/CRM%20Deal/{name}` | AVAILABLE / UNTESTED |
| POST | `/api/resource/CRM%20Deal` | AVAILABLE / UNTESTED |
| PUT | `/api/resource/CRM%20Deal/{name}` | AVAILABLE / UNTESTED |

Trạng thái Lead đã ghi nhận trong tài liệu trước: New, Contacted, Nurture, Qualified, Converted, Unqualified, Junk. Trạng thái Deal: Qualification, Demo/Making, Proposal/Quotation, Negotiation, Ready to Close, Won, Lost. Đây là snapshot cấu hình trước, không hardcode thay cho trạng thái hiện có của site.

Chuyển Lead thành Deal cần bảo toàn liên kết và tránh tạo trùng; Deal Won không đồng nghĩa đơn hàng đã thanh toán. Module `leads.py` và `deals.py` có trong Custom App nhưng cần rà soát nếu muốn dùng thêm ngoài chức năng CRM gốc.

## 6. Customer 360 – API đang tích hợp

Module: `backend/cellphones_c360/cellphones_c360/api/customer360.py`.

| Method Python (tiền tố `cellphones_c360.api.customer360.`) | Input | Trạng thái |
|---|---|---|
| `list_customers` | `search`, `page`, `page_size` | VERIFIED-UI: danh sách hiển thị; cần kiểm thử tìm kiếm, phân trang và quyền |
| `get_customer_360` | `customer_id` | VERIFIED-UI: hồ sơ và các tab dữ liệu |
| `get_customer_timeline` | `customer_id`, `page`, `page_size` | VERIFIED-UI: lịch sử đơn hàng, hỗ trợ; cần kiểm thử thêm tương tác |

### 6.1. Danh sách khách hàng

Endpoint: `/api/method/cellphones_c360.api.customer360.list_customers`.

Tham số mặc định: `search=""`, `page=1`, `page_size=20`. Tìm kiếm theo dữ liệu nhận diện được backend hỗ trợ. Danh sách hiển thị tên và điện thoại đã che; các trường `lead_count` và `deal_count` hiện có thể là null, không tự diễn giải thành 0.

Ví dụ minh họa cấu trúc HTTP response (không phải bản ghi thật):

```json
{
  "message": {
    "items": [
      {
        "customer_id": "CUST-DEMO",
        "display_name": "Khách hàng mẫu",
        "phone_masked": "*******123",
        "lead_count": null,
        "deal_count": null,
        "updated_at": "2026-11-24 10:00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### 6.2. Hồ sơ chi tiết

Endpoint: `/api/method/cellphones_c360.api.customer360.get_customer_360`.

Input: `customer_id` (bắt buộc, sử dụng `C360 Customer.name`).

| Khóa payload | Dữ liệu |
|---|---|
| `customer` | `name`, `customer_name`, `phone_number`, `email`, `customer_type`, `customer_status`, `source_channel`, `crm_contact`, `crm_lead` |
| `contact` | Contact liên kết hoặc null; gồm `name`, `first_name`, `last_name`, `email_ids`, `phone_nos` |
| `lead` | Lead liên kết hoặc null; gồm `name`, `lead_name`, `email`, `mobile_no`, `status`, `lead_owner`, `converted` |
| `deals` | Danh sách Deal: `name`, `lead`, `status`, `deal_owner`, `probability`, `expected_deal_value`, `total`, `net_total`, `creation` |
| `orders` | Danh sách đơn: `name`, `order_date`, `sales_channel`, `order_status`, `total_amount`, `items` |
| `orders[].items` | `product_code`, `product_name`, `quantity`, `unit_price`, `amount` |
| `tickets` | Danh sách hỗ trợ: `name`, `subject`, `ticket_type`, `priority`, `ticket_status`, `created_date`, `related_order`, `description`, `assigned_to`, `resolution`, `resolved_date` |

Các trường có thể null hoặc bị giới hạn theo quyền; danh sách không có dữ liệu là mảng rỗng. Giao diện hiện dùng khóa customer, lead, deals, orders và tickets. Dữ liệu Contact cần kiểm thử hiển thị và quyền riêng; không khẳng định tất cả trường đã được hiển thị.

Ví dụ cấu trúc tối giản, minh họa hồ sơ không phát sinh giao dịch:

```json
{
  "message": {
    "customer": {"name": "CUST-DEMO", "customer_name": "Khách hàng mẫu"},
    "contact": null,
    "lead": null,
    "deals": [],
    "orders": [],
    "tickets": []
  }
}
```

Overview hiển thị thông tin hồ sơ. Orders hiển thị đơn hàng và sản phẩm. Leads & Deals hiển thị cơ hội liên quan. After-sales hiển thị ticket. Chỉ số Order Value hiện là tổng `total_amount` của các đơn được trả về, có thể gồm Draft; không gọi là doanh thu hoặc tổng tiền thực chi.

### 6.3. Timeline

Endpoint: `/api/method/cellphones_c360.api.customer360.get_customer_timeline`.

Input: `customer_id` bắt buộc, `page=1`, `page_size=20`.

Ví dụ minh họa:

```json
{
  "message": {
    "items": [
      {
        "id": "timeline-demo",
        "type": "order",
        "summary": "Đơn hàng mẫu",
        "occurred_at": "2026-11-24 10:00:00",
        "related_doctype": "Customer Order",
        "related_name": "ORD-DEMO"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

Nguồn dữ liệu hiện gồm đơn hàng, yêu cầu hỗ trợ và lịch sử liên kết được backend hỗ trợ. Kiểm thử thực tế hiện đã thấy sự kiện đơn hàng và ticket; cần kiểm thử cuộc gọi, email, công việc và lịch sử Lead/Deal. Không tự tạo sự kiện giả khi thiếu dữ liệu.

### 6.4. Tạo hồ sơ khách hàng

- `GET /api/method/cellphones_c360.api.customers.get_access` trả `canCreate` và `fields`. Mỗi trường có `fieldname`, `label`, `fieldtype`, `options`, `required` và `default` từ metadata theo quyền.
- `POST /api/method/frappe.client.insert` nhận `doc` với `doctype: "C360 Customer"` và các trường được phép ghi. Response `message.name` là mã hồ sơ do Frappe sinh.
- Giao diện dùng session và CSRF của Frappe UI. ORM kiểm tra quyền tạo, trường bắt buộc và Link. Controller chuẩn hóa các trường nhận diện và trả ValidationError khi có xung đột.
- `crm_contact` liên kết trực tiếp `Contact`, còn `crm_lead` liên kết `CRM Lead`. Khi tài khoản không đọc được Contact, hồ sơ Customer 360 vẫn tải được và không gửi phần chi tiết của Contact đó.

### 6.5. Sửa hồ sơ khách hàng

- `GET /api/method/cellphones_c360.api.customers.get_access?customer=CUST-00001` trả `canEdit` và metadata cho các trường được phép sửa. Phương thức kiểm tra quyền đọc hồ sơ trước.
- `POST /api/method/cellphones_c360.api.customers.update_customer` nhận `customer`, `modified` từ `customer.modified` của API hồ sơ và object `values`. Các trường được phép chỉnh sửa gồm tên, điện thoại, email, loại, trạng thái và nguồn, tùy metadata và quyền.
- Response `message.name` giữ nguyên mã hồ sơ. Gửi một phiên bản cũ trả `TimestampMismatchError`. Người dùng tải lại hồ sơ trước khi nhập lại thay đổi.
- Frappe ghi bản ghi `Version` khi nội dung thay đổi. API cập nhật thông tin khách hàng giữ liên kết CRM, đơn hàng và Ticket hiện có.

### 6.6. Đối chiếu hồ sơ khách hàng

`GET /api/method/cellphones_c360.api.customers.find_duplicates` nhận `customer` để đối chiếu với hồ sơ đã lưu hoặc `customer_name`, `phone_number`, `email` để tra theo dữ liệu nhập. Trả tối đa 20 hồ sơ trong quyền đọc, với các trường người gọi được phép xem và `matched_fields` để phân biệt trùng tên, số điện thoại, email hoặc nhiều dấu hiệu. Kết quả là danh sách ứng viên để nhân viên xác minh.

### 6.7. Tiếp nhận khách hàng đa kênh

- `POST /api/method/cellphones_c360.api.intake.process_csv` nhận `csv_text`. `POST /api/method/cellphones_c360.api.intake.process_records` nhận `rows` với cùng các trường được mô tả trong [mapping dữ liệu](../integration/customer-intake.md).
- Trả `items` theo số thứ tự dòng với `status`, `source_record_id`, `source_document`, `reason`, `customer`, `purchase_interest` và `replay` tùy kết quả. Hồ sơ chỉ được trả khi người gọi có quyền đọc.
- `POST /api/method/cellphones_c360.api.intake.resolve_record` nhận `source_document`, `customer`, `reason` để liên kết bản ghi đang Needs Review. Yêu cầu quyền ghi bản ghi nguồn và hồ sơ đích.

### 6.8. Hợp nhất khách hàng

- `GET /api/method/cellphones_c360.api.merge.preview` nhận `source` và `target`, trả dữ liệu đối chiếu được phép đọc, mốc phiên bản và `can_merge`.
- `POST /api/method/cellphones_c360.api.merge.merge_customers` nhận `source`, `target`, `source_modified`, `target_modified`, `selected` (mapping trường → `source` hoặc `target`), `reason` và `verified: true`. Yêu cầu Administrator hoặc System Manager có quyền ghi từng hồ sơ và bản ghi phụ thuộc.
- Response có `customer` là Golden Record, `archived_customer`, `moved` theo DocType và `crm_links_added`. Hồ sơ nguồn từ API chi tiết có `is_merged` và `merged_into` nếu người dùng có quyền đọc hồ sơ hiện hành.

### 6.9. Liên kết Lead, Deal và Contact

- `GET /api/method/cellphones_c360.api.customers.get_access?customer=...` có thêm `crmTypes`, `canCreateLead` và `canCreateDeal`.
- `POST /api/method/cellphones_c360.api.crm_links.link_record` nhận `customer`, `doctype`, `record`. Tạo liên kết một lần và trả `name` của thực thể CRM đã chọn.
- `POST /api/method/cellphones_c360.api.crm_links.create_linked_lead` và `create_linked_deal` nhận `customer`, `doc` từ form CRM chuẩn. Lead trả object có `name`, Deal trả mã Deal theo quy ước của modal gốc.
- `get_customer_360` trả thêm `leads` và `contacts`. `lead` và `contact` vẫn phục vụ các caller hiện có. `deals` gồm liên kết trực tiếp, Lead được liên kết và Contact qua child table CRM Contacts theo quyền đọc.

### 6.10. Hồ sơ và Timeline đầy đủ

`get_customer_360` trả `summary.recorded_order_value` và `summary.confirmed_spend`. Chỉ số chi tiêu yêu cầu đơn Completed, Paid và có `paid_at`. `customer.created_at` và `customer.modified_at` chứa timestamp ISO 8601 có offset của site.

`get_customer_timeline` giữ `items`, `page`, `page_size` và `total`. Mỗi sự kiện có `source`, `related_doctype`, `related_name` và `occurred_at` theo ISO 8601. Event types gồm tạo hồ sơ, tiếp nhận nguồn, hợp nhất, Version, Lead, Deal, Order, Payment, Handover, Ticket, Resolution, Task, Call, Note, Comment và Email.

## 7. Orders và After-sales

`GET /api/method/cellphones_c360.api.orders.get_access` trả quyền đọc, quyền tạo và options bộ lọc. `GET /api/method/cellphones_c360.api.orders.list_orders` nhận `search`, `status`, `channel`, `from_date`, `to_date` và `page`. Trả `items`, `has_more` và trang hiện tại. Tìm kiếm hỗ trợ mã đơn, mã hoặc tên khách hàng được phép đọc.

Form chuẩn Frappe Desk dùng ORM của `Customer Order` để lưu `items`, `crm_deal`, phương thức và trạng thái thanh toán/giao nhận. Controller tính `total_amount`, tự ghi `paid_at` và `completed_at` theo chuyển trạng thái. Tổng giá trị đơn được lưu riêng khỏi chỉ số tiền thực thu.

`GET /api/method/cellphones_c360.api.after_sales.get_capabilities` trả `canRead`, `canCreate` và metadata bộ lọc, hoặc `canEdit` nếu nhận mã `ticket`. `GET /api/method/cellphones_c360.api.after_sales.list_tickets` nhận `search`, `status`, `ticket_type`, `priority`, `customer`, `page`.

`POST /api/method/cellphones_c360.api.after_sales.record_demo_proposal` nhận `customer` và `proposal`. Trả mã Comment khi hồ sơ đang hoạt động, có consent và tài khoản đủ quyền. Lịch chăm sóc là CRM Task do scheduler tạo từ `Customer Order.completed_at`.

DocType đã có, dữ liệu đã hiển thị trong hồ sơ Customer 360. Màn hình quản lý riêng và thao tác ghi trong giao diện native mới chưa được kiểm thử.

| Nghiệp vụ | API / mã nguồn cần đối chiếu | Trạng thái |
|---|---|---|
| Quản lý đơn hàng | REST `/api/resource/Customer%20Order`, controller `customer_order.py`, bảng con `Customer Order Item` | REVIEW |
| Quản lý ticket | REST `/api/resource/Customer%20Support%20Ticket`, `api/after_sales.py`, controller `customer_support_ticket.py` | REVIEW |

Không sử dụng tên `C360 After Sales Request` hoặc các method `list_requests`, `get_request`, `create_request`, `update_request` từ đề xuất cũ nếu chưa đối chiếu. Tên method, input, output, enum trạng thái và phân quyền cụ thể cần trích từ mã nguồn hiện tại.

Quy tắc mục tiêu: đơn hàng phải thuộc đúng khách; sản phẩm lưu trong bảng con; ticket liên kết đúng khách và đơn hàng liên quan; xác minh trạng thái và người phụ trách trước khi cập nhật; bảo toàn lịch sử; không cho sửa trái quyền. Rà soát dữ liệu demo để tránh mâu thuẫn giữa trạng thái đơn hàng và yêu cầu bảo hành.

## 8. Dashboard và Analytics

`GET /api/method/cellphones_c360.api.analytics.get_access` cho biết quyền đọc nhóm KPI. `GET /api/method/cellphones_c360.api.analytics.get_analytics_overview` nhận `period` (`all`, `7d`, `30d`, `90d`) hoặc cặp `from_date`, `to_date` định dạng YYYY-MM-DD. `activities=1` yêu cầu danh sách hoạt động gần đây trong quyền đọc. Xem [công thức và kỳ đo KPI](../design/kpi-definition.md).

Ưu tiên Dashboard có sẵn của Frappe CRM. Module `api/analytics.py` đã có nhưng tên endpoint, tham số, phạm vi dữ liệu và kết quả cần đối chiếu trước khi tích hợp native. Không coi `api/dashboard.py` hoặc các API đề xuất trong v1.0 là đã triển khai.

Các KPI mục tiêu: tổng Lead, tổng Deal, Won Deal, tỷ lệ Won Deal, pipeline theo trạng thái, hoạt động gần đây, phân khúc khách hàng. Quy ước đề xuất: `deal_win_rate = won_deals / total_deals * 100`; `conversion_rate = converted_leads / total_leads * 100`; xử lý mẫu số 0; phải thống nhất kỳ lọc và phạm vi quyền. Giá trị Deal dự kiến không phải doanh thu. CLV/ABC cần nguồn giao dịch và định nghĩa riêng trước khi triển khai.

## 9. Tích hợp frontend native

Các trang hiện tại nằm trong repository CRM:

- `frontend/src/pages/Customer360.vue`
- `frontend/src/pages/Customer360Detail.vue`
- `frontend/src/router.js`
- `frontend/src/components/Layouts/AppSidebar.vue`

Route: `/crm/customer360` và `/crm/customer360/:customerId` trên trình duyệt. Dùng router của CRM để điều hướng sang Lead/Deal gốc.

Ví dụ gọi API đọc bằng frappe-ui:

```js
import { call } from 'frappe-ui'

const result = await call(
  'cellphones_c360.api.customer360.list_customers',
  { search: '', page: 1, page_size: 20 }
)
```

`result` là payload method theo cách sử dụng hiện tại, không phải đối tượng Axios `response.data.message`. Với API HTTP trực tiếp, giữ quy ước envelope mục 2. Hiển thị loading/error/empty state rõ ràng; giữ giá trị trạng thái từ backend, tách nhãn hiển thị khi cần. Không hiển thị dữ liệu giả như dữ liệu thật.

## 10. Tiêu chí chấp nhận và việc còn mở

- [x] Xác nhận Custom App và 5 DocType trên site hiện tại.
- [x] Hiển thị danh sách và mở hồ sơ Customer 360 bằng Administrator.
- [x] Hiển thị 5 tab hồ sơ với dữ liệu demo.
- [ ] Kiểm thử tìm kiếm, phân trang, ID không tồn tại, khách chưa có dữ liệu.
- [ ] Kiểm thử điều hướng Lead/Deal và nhiều khách khác nhau.
- [ ] Kiểm thử quyền Guest, Sales User, Sales Manager, CSKH và quyền tài liệu/trường.
- [ ] Rà soát dữ liệu Contact và lịch sử tương tác theo quyền.
- [ ] Đối chiếu module customers, after_sales, analytics, registration, administration, employee_administration và access.
- [ ] Hoàn thiện tạo/sửa khách hàng, chống trùng, hợp nhất đa kênh.
- [ ] Kiểm thử quản lý Orders và After-sales riêng, thao tác ghi và validation.
- [ ] Thống nhất định nghĩa doanh thu, KPI và nguồn dữ liệu phân tích.
- [ ] Kiểm thử bộ triển khai native trên môi trường bàn giao.
- [ ] Không lộ mật khẩu, token, dữ liệu cá nhân trong log, backup chia sẻ hoặc Git.

Các thay đổi endpoint và schema phải được cập nhật đồng bộ với frontend qua commit/PR. Chỉ nâng trạng thái kiểm thử khi có minh chứng tương ứng; không đánh dấu toàn bộ backend hay phân quyền đã hoàn thành dựa trên một lần kiểm thử Administrator.
