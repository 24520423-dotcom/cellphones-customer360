# API Contract – CellphoneS Customer 360

> **Phiên bản:** 1.0 – Đề xuất để nhóm triển khai (chưa phê duyệt kỹ thuật)  
> **Ngày:** 17/11/2026  
> **Điều phối tài liệu:** Giang  
> **Hệ thống:** Frappe Framework 15.126.1, Frappe CRM 1.92.0, React + Vite  
> **Backend local:** `http://crm.localhost:8000`

## 1. Mục đích và phạm vi

Đây là giao ước dữ liệu giữa Frontend React và Backend Frappe cho demo **Customer 360 – CellphoneS**. Giang xây dựng bản đề xuất; Hân triển khai Auth/Lead, Linh triển khai Customer 360/After-sales, Khải triển khai Deal/Analytics; Giang triển khai Dashboard và tích hợp.

**Phân biệt trạng thái:**
- **VERIFIED-GET:** Đã thực sự đọc dữ liệu thành công từ site hiện tại.
- **FRAPPE-AVAILABLE / UNTESTED:** REST/method có sẵn theo giao diện Frappe nhưng chưa kiểm thử thao tác này trong site/role cụ thể.
- **PROPOSED:** API hoặc mô hình dữ liệu nhóm cần tự triển khai; JSON bên dưới là hợp đồng đề xuất, **không phải response đã quan sát**.
- **BLOCKED:** Chưa thể triển khai chính xác khi chưa chốt DocType/quan hệ hoặc quy tắc nghiệp vụ.

Không coi tài liệu này là bằng chứng đã hoàn thành backend, kiểm thử quyền hay tích hợp.

## 2. Quy ước chung

### 2.1. Đường dẫn và HTTP

| Loại | Đường dẫn | Response |
|---|---|---|
| REST Frappe | `/api/resource/{URL-encoded DocType}` | `{ "data": ... }` |
| Whitelisted custom method | `/api/method/cellphones_c360.api.{module}.{function}` | `{ "message": ... }` |

`cellphones_c360` là **tên custom app đề xuất, chưa xác nhận đã tạo**. Nếu app được đặt tên khác, phải sửa contract và services đồng bộ trước khi code.

- `GET`: đọc dữ liệu; `POST`: tạo hoặc thực hiện nghiệp vụ; `PUT`: cập nhật bản ghi REST.
- Dữ liệu ngày giờ dùng ISO 8601 có múi giờ trong custom response, ví dụ `2026-11-17T10:00:00+07:00`. Ngày không có giờ: `YYYY-MM-DD`.
- Số tiền dùng JSON number, đơn vị VND; không định dạng dấu phân cách hàng nghìn trong API.
- Phân trang custom: `page` bắt đầu từ 1, `page_size` mặc định 20, tối đa 100; response trả `items`, `page`, `page_size`, `total`.
- ID (`name`, `customer_id`, `request_id`) là chuỗi, không tự sinh ở Frontend.
- Với Frappe REST, tham số `fields`, `filters`, `limit_page_length`, `limit_start` cần được URL-encode. Trường được phép đọc tùy quyền của người dùng.

### 2.2. Xác thực, CORS và lỗi

**Định hướng:** Frappe Session Authentication; Frontend gửi cookie phiên (`withCredentials: true`) khi cần. Khi frontend và backend khác origin, phải cấu hình CORS/cookie phù hợp và xác thực cơ chế CSRF cho thao tác ghi; **không** giả định có thể POST cross-origin ngay.

- Không hardcode mật khẩu, API key, secret hoặc session cookie trong repo.
- Không dùng tài khoản Administrator làm tài khoản mặc định cho Frontend.
- Mọi custom method truy cập dữ liệu phải xác thực và kiểm tra quyền trên server; **không dùng `ignore_permissions=True`** cho dữ liệu khách hàng.
- `401`: chưa đăng nhập/phiên hết hạn (tùy endpoint Frappe có thể trả `403`); `403`: thiếu quyền; `404`: không có bản ghi hoặc không được phép xem; `409`: xung đột nghiệp vụ; `422`: dữ liệu đầu vào không hợp lệ (mã thực tế Frappe có thể khác, adapter frontend phải chuẩn hóa).

**Mẫu lỗi chuẩn hóa ở frontend (không phải nguyên dạng lỗi Frappe):**

```json
{ "code": "VALIDATION_ERROR", "message": "Thiếu số điện thoại", "details": { "phone": "required" } }
```

### 2.3. Quyền dự kiến

| Vai trò nghiệp vụ | Auth | Lead | Deal | Customer 360 | After-sales | Analytics/Dashboard |
|---|---|---|---|---|---|---|
| Administrator | Quản trị | Toàn bộ | Toàn bộ | Toàn bộ | Toàn bộ | Toàn bộ |
| Sales Manager | Đăng nhập | Xem/quản lý phạm vi đội | Xem/quản lý phạm vi đội | Xem khách thuộc phạm vi | Xem theo phạm vi | Tổng hợp đội |
| Sales User | Đăng nhập | Lead được phân công | Deal được phân công | Khách được phân công | Xem/tạo theo phạm vi | Chỉ dữ liệu được phép |
| CSKH | Đăng nhập | Xem theo nhu cầu | Xem theo nhu cầu | Xem khách được hỗ trợ | Xem/tạo/cập nhật được phân công | Giới hạn |
| Guest | Đăng nhập/đăng ký nếu bật | Không | Không | Không | Không | Không |

**Lưu ý:** Đây là **ma trận mục tiêu**, chưa chứng minh role/permission thực tế trên Frappe. Các thành viên phải kiểm thử từng vai trò trước khi đánh dấu hoàn tất.

## 3. Authentication – Hân

| Method | Endpoint | Trạng thái | Mục đích |
|---|---|---|---|
| POST | `/api/method/login` | FRAPPE-AVAILABLE / UNTESTED | Đăng nhập |
| GET | `/api/method/frappe.auth.get_logged_user` | FRAPPE-AVAILABLE / UNTESTED | Lấy người dùng phiên hiện tại |
| POST | `/api/method/logout` | FRAPPE-AVAILABLE / UNTESTED | Đăng xuất |
| POST | `/api/method/cellphones_c360.api.auth.register` | PROPOSED | Đăng ký nhân viên demo |
| GET | `/api/method/cellphones_c360.api.auth.pending_users` | PROPOSED | Danh sách chờ duyệt |
| POST | `/api/method/cellphones_c360.api.auth.review_user` | PROPOSED | Duyệt/từ chối tài khoản |

**Đăng nhập Frappe – request form:** `usr`, `pwd`. **Không tự giả định** `/api/method/login` nhận JSON ở mọi cấu hình; Hân kiểm thử thực tế với client đang dùng.

**Đăng ký (PROPOSED):**

```http
POST /api/method/cellphones_c360.api.auth.register
Content-Type: application/json
```
```json
{ "full_name": "Nhân viên Demo", "email": "sales.demo@example.com", "password": "<do-not-commit-real-password>", "requested_role": "Sales User" }
```
```json
{ "message": { "user_id": "sales.demo@example.com", "approval_status": "Pending" } }
```

**Duyệt (PROPOSED; chỉ Administrator):**
```json
{ "user_id": "sales.demo@example.com", "decision": "approve", "assigned_role": "Sales User", "reason": null }
```
```json
{ "message": { "user_id": "sales.demo@example.com", "approval_status": "Approved" } }
```

**Quy tắc:** người chưa được duyệt không được truy cập dữ liệu CRM; server phải chống tự nâng quyền và kiểm tra trùng email. Cần chốt cơ chế lưu trạng thái Pending/Approved/Rejected và chính sách gửi email trước khi implement.

## 4. Lead – Hân

**DocType xác nhận:** `CRM Lead`. **Đã kiểm thử:** GET danh sách với các trường `name`, `lead_name`, `status`, trả về 5 Lead trên dữ liệu demo lúc kiểm tra. **Các thao tác ghi chưa kiểm thử.**

| Method | Endpoint | Trạng thái |
|---|---|---|
| GET | `/api/resource/CRM%20Lead?fields=["name","lead_name","status"]` (URL-encode query) | VERIFIED-GET |
| GET | `/api/resource/CRM%20Lead/{name}` | FRAPPE-AVAILABLE / UNTESTED |
| POST | `/api/resource/CRM%20Lead` | FRAPPE-AVAILABLE / UNTESTED |
| PUT | `/api/resource/CRM%20Lead/{name}` | FRAPPE-AVAILABLE / UNTESTED |

**Các trường đã xác nhận:** `name`, `lead_name`, `status`, `source`, `lead_owner`, `converted`, `creation` (không khẳng định tất cả bắt buộc/ghi được).

**Ví dụ tạo Lead – chỉ là payload đề xuất, cần đối chiếu field bắt buộc trên site:**
```json
{ "lead_name": "Nguyễn Minh Anh", "status": "New", "source": "Website" }
```

**Ví dụ cập nhật:**
```json
{ "status": "Contacted" }
```

**Trạng thái thực tế đã ghi nhận:** `New`, `Contacted`, `Nurture`, `Qualified`, `Converted`, `Unqualified`, `Junk`.

**Quy tắc:** chỉ cho phép cập nhật Lead trong phạm vi quyền; chuyển Lead → Deal phải có cơ chế tránh tạo trùng và bảo toàn liên kết. Endpoint chuyển đổi riêng chỉ bổ sung nếu nghiệp vụ cần và Hân/Khải chốt.

## 5. Deal – Khải

**DocType xác nhận:** `CRM Deal`. **Đã kiểm thử:** GET danh sách trả về 2 Deal; `CRM-DEAL-2026-00001` trạng thái `Demo/Making`, `deal_value = 0`, liên kết Lead `CRM-LEAD-2026-00001`; `CRM-DEAL-2026-00002` trạng thái `Lost`, `deal_value = 0`, `lead = null`.

| Method | Endpoint | Trạng thái |
|---|---|---|
| GET | `/api/resource/CRM%20Deal` | VERIFIED-GET |
| GET | `/api/resource/CRM%20Deal/{name}` | FRAPPE-AVAILABLE / UNTESTED |
| POST | `/api/resource/CRM%20Deal` | FRAPPE-AVAILABLE / UNTESTED |
| PUT | `/api/resource/CRM%20Deal/{name}` | FRAPPE-AVAILABLE / UNTESTED |

**Các trường đã xác nhận:** `name`, `status`, `deal_value`, `expected_deal_value`, `lead`, `closed_date`, `creation`.

**Trạng thái thực tế:** `Qualification`, `Demo/Making`, `Proposal/Quotation`, `Negotiation`, `Ready to Close`, `Won`, `Lost`.

**Ví dụ cập nhật Deal (PROPOSED payload REST, chưa kiểm thử):**
```json
{ "status": "Negotiation", "expected_deal_value": 19990000 }
```

**Quy tắc:** Deal Won không tự đồng nghĩa đã có đơn hàng/đã thanh toán; không tính doanh thu thật từ `deal_value` khi dữ liệu demo chưa có quy ước. Khải phải xác định liên kết Deal không có `lead` trước khi Linh tổng hợp Customer 360.

## 6. Dashboard – Giang

**Tất cả API dưới đây: PROPOSED; chưa tạo custom app.**

| Method | Endpoint | Input | Output |
|---|---|---|---|
| GET | `/api/method/cellphones_c360.api.dashboard.get_kpis` | `period` | `total_leads`, `total_deals`, `won_deals`, `deal_win_rate` |
| GET | `/api/method/cellphones_c360.api.dashboard.get_lead_stats` | `period` | `[{status,count}]` |
| GET | `/api/method/cellphones_c360.api.dashboard.get_deal_stats` | `period` | `[{status,count}]` |
| GET | `/api/method/cellphones_c360.api.dashboard.get_recent_activities` | `period`, `limit` | `[{id,type,subject,related_doctype,related_name,created_at}]` |

`period`: `7d|30d|90d|all`, mặc định `30d`. Lọc Lead/Deal theo `creation`. `deal_win_rate = won_deals / total_deals * 100`, bằng `0` nếu không có Deal; không gọi tỷ lệ này là tỷ lệ chốt theo cohort nếu chưa có định nghĩa khác.

**Ví dụ GET `get_kpis?period=all` – JSON thiết kế minh họa từ snapshot kiểm tra, không phải API trả về:**
```json
{ "message": { "total_leads": 5, "total_deals": 2, "won_deals": 0, "deal_win_rate": 0.0 } }
```

**Ví dụ `get_lead_stats`:**
```json
{ "message": [ { "status": "New", "count": 1 }, { "status": "Contacted", "count": 1 }, { "status": "Nurture", "count": 1 }, { "status": "Qualified", "count": 2 }, { "status": "Converted", "count": 0 }, { "status": "Unqualified", "count": 0 }, { "status": "Junk", "count": 0 } ] }
```

**Ví dụ `get_deal_stats`:**
```json
{ "message": [ { "status": "Qualification", "count": 0 }, { "status": "Demo/Making", "count": 1 }, { "status": "Proposal/Quotation", "count": 0 }, { "status": "Negotiation", "count": 0 }, { "status": "Ready to Close", "count": 0 }, { "status": "Won", "count": 0 }, { "status": "Lost", "count": 1 } ] }
```

**Ví dụ `get_recent_activities` (giả lập):**
```json
{ "message": [ { "id": "activity-demo-1", "type": "call", "subject": "Cuộc gọi tư vấn", "related_doctype": "CRM Lead", "related_name": "CRM-LEAD-2026-00001", "created_at": "2026-11-17T10:00:00+07:00" } ] }
```

Nguồn activity ưu tiên `CRM Call Log`, `CRM Task` và các bản ghi tương tác mà người dùng được phép xem. Nếu chưa thống nhất mapping, trả `[]`, **không tự tạo hoạt động giả**.

## 7. Customer 360 – Linh

**Trạng thái: PROPOSED / BLOCKED về mô hình dữ liệu.** Frappe CRM hiện đã xác nhận `CRM Lead`, `CRM Deal`, `CRM Contacts`, `CRM Organization`, `CRM Task`, `CRM Call Log`; **chưa xác nhận DocType `CRM Customer`**. Không mặc định `customer_id` trùng Lead ID.

**Đề xuất:** Linh thiết kế khóa định danh khách hàng thống nhất (`customer_id`) và bảng/DocType mapping để liên kết Lead, Deal, Contact, lịch sử tương tác và dữ liệu mua hàng demo. Cần chốt cách hợp nhất trùng email/số điện thoại và bảo vệ thông tin cá nhân.

| Method | Endpoint custom đề xuất | Mục đích |
|---|---|---|
| GET | `/api/method/cellphones_c360.api.customers.list_customers` | Danh sách hồ sơ hợp nhất |
| GET | `/api/method/cellphones_c360.api.customers.get_customer_profile` | Hồ sơ 360 theo `customer_id` |
| GET | `/api/method/cellphones_c360.api.customers.get_customer_timeline` | Lịch sử tương tác theo khách |

**`list_customers` query:** `search` (tùy chọn), `page=1`, `page_size=20`.
```json
{ "message": { "items": [ { "customer_id": "C360-DEMO-001", "display_name": "Nguyễn Minh Anh", "phone_masked": "*******123", "lead_count": 1, "deal_count": 1 } ], "page": 1, "page_size": 20, "total": 1 } }
```

**`get_customer_profile?customer_id=C360-DEMO-001` – mẫu giả lập:**
```json
{ "message": { "customer_id": "C360-DEMO-001", "display_name": "Nguyễn Minh Anh", "email": null, "phone": null, "segments": [], "leads": [ { "name": "CRM-LEAD-2026-00001", "status": "Qualified" } ], "deals": [ { "name": "CRM-DEAL-2026-00001", "status": "Demo/Making", "deal_value": 0 } ], "interactions": [], "after_sales_requests": [] } }
```

**`get_customer_timeline?customer_id=C360-DEMO-001&page=1&page_size=20`:**
```json
{ "message": { "items": [ { "id": "timeline-demo-1", "type": "call", "summary": "Đã tư vấn sản phẩm", "occurred_at": "2026-11-17T10:00:00+07:00", "related_doctype": "CRM Lead", "related_name": "CRM-LEAD-2026-00001" } ], "page": 1, "page_size": 20, "total": 1 } }
```

**Quy tắc:** `customer_id` phải có bản ghi ánh xạ thực; không truy xuất bằng tên khách vì có thể trùng. Chỉ hiển thị dữ liệu trong phạm vi quyền. Linh phải xác nhận cấu trúc trong `docs/data/customer360-data-model.md` trước khi code các endpoint này.

## 8. After-sales – Linh

**Trạng thái: PROPOSED / BLOCKED về DocType.** Đề xuất DocType tùy chỉnh `C360 After Sales Request` (tên tạm; Linh có thể đổi trước khi triển khai). Không coi đây là DocType có sẵn.

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | `/api/method/cellphones_c360.api.after_sales.list_requests` | Lọc yêu cầu theo `customer_id`, `status`, `page`, `page_size` |
| GET | `/api/method/cellphones_c360.api.after_sales.get_request` | Chi tiết theo `request_id` |
| POST | `/api/method/cellphones_c360.api.after_sales.create_request` | Tạo yêu cầu |
| POST | `/api/method/cellphones_c360.api.after_sales.update_request` | Cập nhật trạng thái/nhân viên/ghi chú |

**Tạo yêu cầu (PROPOSED):**
```json
{ "customer_id": "C360-DEMO-001", "category": "Warranty", "subject": "Hỏi về bảo hành điện thoại", "description": "Khách cần kiểm tra điều kiện bảo hành", "related_deal": "CRM-DEAL-2026-00001" }
```
```json
{ "message": { "request_id": "AS-DEMO-001", "status": "Open", "customer_id": "C360-DEMO-001" } }
```

**Cập nhật (PROPOSED):**
```json
{ "request_id": "AS-DEMO-001", "status": "In Progress", "assigned_to": "support@example.com", "note": "Đang xác minh thông tin" }
```
```json
{ "message": { "request_id": "AS-DEMO-001", "status": "In Progress", "updated_at": "2026-11-17T11:00:00+07:00" } }
```

**Danh sách:**
```json
{ "message": { "items": [ { "request_id": "AS-DEMO-001", "customer_id": "C360-DEMO-001", "category": "Warranty", "subject": "Hỏi về bảo hành điện thoại", "status": "Open", "assigned_to": null, "created_at": "2026-11-17T10:00:00+07:00" } ], "page": 1, "page_size": 20, "total": 1 } }
```

**Trạng thái đề xuất:** `Open`, `In Progress`, `Resolved`, `Closed`; chỉ người được phân công/CSKH có quyền được sửa. Mọi thay đổi phải ghi lịch sử; không cho tự ý đổi `customer_id` sau khi tạo.

## 9. Analytics – Khải

**Trạng thái: PROPOSED.** Báo cáo chỉ dùng dữ liệu CRM demo; không gọi giá trị Deal là doanh thu giao dịch thực tế.

| Method | Endpoint | Input | Output |
|---|---|---|---|
| GET | `/api/method/cellphones_c360.api.analytics.get_pipeline_summary` | `period` | Số Deal theo từng trạng thái, tổng giá trị dự kiến |
| GET | `/api/method/cellphones_c360.api.analytics.get_lead_conversion` | `period` | Lead tạo mới, Lead converted, tỷ lệ chuyển đổi |
| GET | `/api/method/cellphones_c360.api.analytics.get_customer_segments` | `period` | Phân khúc từ mô hình Customer 360 |

**`get_pipeline_summary?period=all` – mẫu giả lập dựa trên snapshot 2 Deal:**
```json
{ "message": { "total_deals": 2, "total_expected_value": 0, "by_status": [ { "status": "Demo/Making", "count": 1 }, { "status": "Lost", "count": 1 } ] } }
```

**`get_lead_conversion?period=all` – mẫu giả lập:**
```json
{ "message": { "total_leads": 5, "converted_leads": 0, "conversion_rate": 0.0 } }
```

**`get_customer_segments?period=all` – chỉ dùng khi Linh đã tạo segment:**
```json
{ "message": { "segments": [], "method": "not_configured" } }
```

`conversion_rate = converted_leads / total_leads * 100`, dùng `creation` để lọc Lead theo kỳ. `total_expected_value` là tổng `expected_deal_value` hợp lệ, không phải doanh thu. Chỉ phân tích phân khúc/CLV/ABC sau khi Linh cung cấp dữ liệu giao dịch và quy tắc tính; **không tự sinh chỉ số CLV** từ hai Deal demo.

## 10. Quy tắc tích hợp Frontend

- Tạo Axios instance dùng `baseURL`, `withCredentials` phù hợp; xử lý lỗi Frappe tập trung.
- REST Frappe: đọc `response.data.data`; custom method: đọc `response.data.message`.
- Frontend không tự đổi tên trạng thái Lead/Deal; dùng đúng giá trị Backend hoặc mapping hiển thị riêng.
- `403`/phiên hết hạn: hiển thị thông báo và điều hướng phù hợp, không tự giả định mọi `403` đều là chưa đăng nhập.
- Chưa có API custom: dùng mock **có nhãn rõ ràng**, không trình diễn là dữ liệu Backend thật.
- Không gọi API trực tiếp từ component nếu đã có `src/services/*Service.js`.

**Định hướng service:**

| Người phụ trách | Frontend service | Backend module |
|---|---|---|
| Hân | `authService.js`, `leadService.js` | Frappe Auth, REST Lead, `api/auth.py` |
| Khải | `dealService.js`, `analyticsService.js` | REST Deal, `api/analytics.py` |
| Linh | `customerService.js`, `afterSalesService.js` | `api/customers.py`, `api/after_sales.py` |
| Giang | `dashboardService.js` | `api/dashboard.py` |

Đường dẫn service là quy ước đề xuất; đối chiếu cấu trúc thực tế của repo trước khi tạo file.

## 11. Bàn giao và tiêu chí chấp nhận

### Hân
- Kiểm thử login, logout, session, đăng ký và phê duyệt nếu nghiệp vụ yêu cầu.
- Kiểm thử GET/POST/PUT Lead với role hợp lệ và role không có quyền.
- Xác nhận trường bắt buộc và quy tắc chuyển Lead → Deal.

### Linh
- Chốt mô hình `customer_id` và mapping Lead/Deal/Contact trước khi viết API Customer 360.
- Chốt DocType After-sales, các trạng thái và lịch sử cập nhật.
- Kiểm thử một khách có nhiều tương tác; ngăn lẫn hồ sơ giữa hai khách.

### Khải
- Kiểm thử CRUD Deal, trạng thái pipeline và liên kết Lead.
- Triển khai analytics dựa trên dữ liệu thực tế của site, không hardcode demo.
- Phối hợp với Linh về Deal không có Lead và dữ liệu giao dịch.

### Giang
- Triển khai custom Dashboard API; thống nhất response và quyền.
- Kết nối Axios/service; kiểm tra dữ liệu và thông báo lỗi trên React.
- Cập nhật tài liệu khi nhóm đổi DocType, tên app hoặc cấu trúc response.

### Checklist API trước khi đánh dấu DONE

- [ ] Endpoint tồn tại và trả response đúng contract.
- [ ] Test thành công với user được phép.
- [ ] Test bị chặn với user không được phép.
- [ ] Test trường hợp thiếu tham số, không có bản ghi và dữ liệu rỗng.
- [ ] Không lộ mật khẩu, token, dữ liệu cá nhân nhạy cảm trong log/Git.
- [ ] Cập nhật trạng thái từ PROPOSED sang VERIFIED sau khi có minh chứng.

## 12. Các quyết định cần chốt trước khi triển khai

| Mã | Quyết định | Người xác nhận |
|---|---|---|
| D01 | Tên custom app có dùng `cellphones_c360` không? | Giang + Khải |
| D02 | Frontend/backend chạy cùng origin hay khác origin? Cấu hình session/CSRF thế nào? | Giang + Hân |
| D03 | Đăng ký nhân viên có cần duyệt? Lưu trạng thái duyệt ở đâu? | Hân |
| D04 | Lead chuyển thành Deal theo workflow nào, chống trùng ra sao? | Hân + Khải |
| D05 | Khóa `customer_id`, quan hệ Lead/Deal/Contact và dữ liệu offline/online? | Linh + Khải |
| D06 | DocType After-sales và quyền CSKH? | Linh |
| D07 | Quy tắc tính doanh thu/CLV/ABC, nguồn giao dịch thật hay demo? | Linh + Khải |
| D08 | Dashboard hiển thị KPI theo ngày tạo hay ngày đóng Deal? | Giang + Khải |

**Nguyên tắc:** Giang phát hành contract để nhóm follow; các thành viên chỉ phản hồi điểm không khả thi hoặc không khớp mô hình. Chỉ đổi contract qua commit/PR có thông báo, không tự thay endpoint một phía.
