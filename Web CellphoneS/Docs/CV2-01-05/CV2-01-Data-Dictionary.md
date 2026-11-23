# CV2-01 – Data Dictionary và quan hệ dữ liệu

Nguồn kiểm tra: mã nguồn DocType JSON trong GitHub `main` mà nhóm cung cấp; các trường CRM chuẩn phải được **kiểm chứng trên Frappe site thật** bằng hàm `cellphones_c360.cv2_audit.audit_schema`.

## 1. DocType tuỳ chỉnh (được kiểm tra từ source)

### C360 Customer

- **Loại:** DocType chính; **autoname:** `CUST-.#####`.
- **Phân quyền mặc định trong source:** `System Manager`: read=1, create=1, write=1.

| Fieldname | Fieldtype | Bắt buộc | Link/Table / Ghi chú |
|---|---|:---:|---|
| `customer_information` | Section Break | Không |  |
| `customer_name` | Data | Có |  |
| `phone_number` | Data | Không |  |
| `email` | Data | Không |  |
| `customer_type` | Select | Có | Individual · Business |
| `customer_status` | Select | Có | Active · Inactive |
| `customer_source_section` | Section Break | Không |  |
| `source_channel` | Select | Không | Website · App · Facebook · Zalo · Hotline · Store · Other |
| `crm_references_section` | Section Break | Không |  |
| `crm_contact` | Link | Không | Contact |
| `crm_lead` | Link | Không | CRM Lead |

### C360 Customer Intake

- **Loại:** DocType chính; **autoname:** `INTAKE-.#####`.
- **Phân quyền mặc định trong source:** `System Manager`: read=1, create=1, write=1.

| Fieldname | Fieldtype | Bắt buộc | Link/Table / Ghi chú |
|---|---|:---:|---|
| `source_key` | Data | Có |  (unique) |
| `source_channel` | Select | Có | Website · App · Facebook · Zalo · Hotline · Store · Other |
| `source_reference` | Data | Có |  |
| `received_at` | Datetime | Có |  |
| `customer_name` | Data | Có |  |
| `phone_number` | Data | Không |  |
| `email` | Data | Không |  |
| `status` | Select | Có | Created · Linked · Needs Review · Rejected |
| `customer` | Link | Không | C360 Customer |
| `candidate_customer` | Link | Không | C360 Customer |
| `review_reason` | Small Text | Không |  |
| `reviewed_by` | Link | Không | User |
| `reviewed_at` | Datetime | Không |  |

### Customer Order

- **Loại:** DocType chính; **autoname:** `ORD-.#####`.
- **Phân quyền mặc định trong source:** `System Manager`: read=1, create=1, write=1.

| Fieldname | Fieldtype | Bắt buộc | Link/Table / Ghi chú |
|---|---|:---:|---|
| `order_information` | Section Break | Không |  |
| `customer` | Link | Có | C360 Customer |
| `order_date` | Date | Có |  |
| `sales_channel` | Select | Có | Website · App · Facebook · Zalo · Hotline · Store · Other |
| `order_status` | Select | Có | Draft · Confirmed · Processing · Completed · Cancelled |
| `order_items` | Section Break | Không |  |
| `items` | Table | Có | Customer Order Item |
| `order_summary` | Section Break | Không |  |
| `total_amount` | Currency | Không |  |

### Customer Order Item

- **Loại:** Child table; **autoname:** `(child managed by Frappe)`.
- **Phân quyền mặc định trong source:** Không khai báo; quyền phụ thuộc DocType cha/hệ thống.

| Fieldname | Fieldtype | Bắt buộc | Link/Table / Ghi chú |
|---|---|:---:|---|
| `product_information` | Section Break | Không |  |
| `product_code` | Data | Không |  |
| `product_name` | Data | Có |  |
| `quantity` | Int | Có |  |
| `unit_price` | Currency | Có |  |
| `amount` | Currency | Không |  |

### Customer Support Ticket

- **Loại:** DocType chính; **autoname:** `TICK-.#####`.
- **Phân quyền mặc định trong source:** `System Manager`: read=1, create=1, write=1.

| Fieldname | Fieldtype | Bắt buộc | Link/Table / Ghi chú |
|---|---|:---:|---|
| `ticket_information` | Section Break | Không |  |
| `subject` | Data | Có |  |
| `ticket_type` | Select | Có | Warranty · Return · Exchange · Complaint · Technical Support · Other |
| `priority` | Select | Có | Low · Medium · High · Urgent |
| `ticket_status` | Select | Có | Open · In Progress · Pending · Resolved · Closed |
| `created_date` | Datetime | Có |  |
| `customer_order_reference` | Section Break | Không |  |
| `customer` | Link | Có | C360 Customer |
| `related_order` | Link | Không | Customer Order |
| `support_details` | Section Break | Không |  |
| `description` | Small Text | Có |  |
| `assigned_to` | Link | Không | User |
| `resolution` | Small Text | Không |  |
| `resolved_date` | Datetime | Không |  |

### C360 Registration Request

- **Loại:** DocType chính; **autoname:** `hash`.
- **Phân quyền mặc định trong source:** Không khai báo; quyền phụ thuộc DocType cha/hệ thống.

| Fieldname | Fieldtype | Bắt buộc | Link/Table / Ghi chú |
|---|---|:---:|---|
| `full_name` | Data | Có |  |
| `email` | Data | Có |  (unique) |
| `phone` | Data | Có |  |
| `department` | Select | Có | Sales · Customer Service · Operations · Other |
| `status` | Select | Có | Pending · Approved · Rejected |
| `reason` | Small Text | Không |  |
| `reviewed_by` | Link | Không | User |
| `reviewed_at` | Datetime | Không |  |
| `provisioned_user` | Link | Không | User |
| `assigned_role` | Link | Không | Role |
| `invitation_status` | Select | Không | Not Queued · Queued · Failed |
| `invitation_queue` | Link | Không | Email Queue |

## 2. CRM Doctype nền: bắt buộc kiểm tra trên site

Các DocType `CRM Lead`, `CRM Deal`, `CRM Call Log`, `CRM Task` đến từ Frappe CRM **1.92.0** trên máy Khải. Không đưa fieldtype hay `reqd` của chúng thành kết quả đã xác nhận vì bản ZIP không chứa JSON chuẩn của ứng dụng `crm`.

| DocType | Trường đã được mã nguồn nhóm sử dụng | Việc đối chiếu |
|---|---|---|
| `CRM Lead` | `name`, `lead_name`, `mobile_no`, `email`, `status`, `lead_owner`, `custom_consultation_notes` | Kiểm tra tên/trạng thái/permission ở site |
| `CRM Deal` | `name`, `lead`, `status`, `deal_owner`, `expected_deal_value`, `creation` | Kiểm tra field và rule trong Frappe CRM thực tế |
| `CRM Call Log` | `reference_doctype`, `reference_docname`, `start_time`, `type`, `status` | Kiểm tra qua Meta/permission |
| `CRM Task` | `reference_doctype`, `reference_docname`, `title`, `status` | Kiểm tra qua Meta/permission |

### Custom Field CV2 bổ sung vào CRM chuẩn

| DocType | Fieldname | Kiểu | Link đích | Lý do |
|---|---|---|---|---|
| CRM Lead | `custom_c360_customer` | Link | C360 Customer | 1 Customer nhiều Lead |
| CRM Lead | `custom_consultation_notes` | Small Text | – | Tránh lỗi `DataError` trước đây ở Leads |
| CRM Deal | `custom_c360_customer` | Link | C360 Customer | Liên kết Deal trực tiếp với Customer và qua Lead |

Các field được tạo idempotent qua `after_install`/`after_migrate` trong `setup_cv2.py`. Không thêm trường dữ liệu bằng thao tác thủ công trên mỗi máy.

### 3. Kiểm tra trên Frappe thật

Chạy lệnh **sau khi triển khai code và `bench migrate`** (trong container Frappe, thư mục `/home/frappe/frappe-bench`):

```bash
bench --site crm.localhost execute cellphones_c360.cv2_audit.audit_schema
```

Kết quả trả về metadata **thực tế** cho 10 DocType, cùng `missing_fields`, `broken_links`, `cross_customer_deals`. Chỉ đánh dấu CV2-01 đạt khi các danh sách lỗi trống và kiểm tra thủ công quyền thành công.

## 4. Kết luận kiểm tra source

- `Customer Order.customer` và `Customer Support Ticket.customer` đã là Link tới `C360 Customer`.
- `Customer Support Ticket.related_order` là Link tới `Customer Order`; controller kiểm tra đơn hàng thuộc đúng khách.
- `Customer Order.items` là Table của `Customer Order Item`.
- `C360 Customer.crm_lead` là Link 1:1 kiểu cũ, vẫn giữ để tương thích.
- Link mới trên `CRM Lead` và `CRM Deal` hỗ trợ 1:N; validator trên Deal tránh liên kết sai Customer của Lead.
- `C360 Customer Intake` mới lưu nguồn và trạng thái xử lý cho từng lượt tiếp nhận; chỉ System Manager được truy cập theo phân quyền source.

**Chưa được xác nhận:** số bản ghi/thực tế các trường bắt buộc, dữ liệu mồ côi, quyền và hiệu quả trên Frappe của máy từng thành viên.
