# CV2-04 / CV2-05 – Liên kết thực thể, API và test case

## 1. Luồng dữ liệu đã bổ sung

- `CRM Lead.custom_c360_customer` (Link Customer) cho phép nhiều Lead thuộc cùng C360 Customer.
- `CRM Deal.custom_c360_customer` (Link Customer) cho phép Deal thuộc Customer trực tiếp, đồng thời được truy vấn thông qua `CRM Deal.lead`.
- `CRM Deal` có Lead liên kết Customer mà trường Customer trên Deal lại khác → controller `validate` sẽ từ chối khi lưu.
- `Customer Order.customer` giữ nguyên Link, `Customer Order.items` giữ Table con, Ticket giữ Customer + Order và kiểm tra Order đúng Customer.
- `C360 Customer.crm_lead` giữ cho hồ sơ cũ. API mới dùng cả link cũ và link mới, loại trùng tên bản ghi.
- Intake lưu lịch sử tiếp nhận đa kênh; timeline chỉ hiển thị các Intake đã được xác nhận nếu người dùng có quyền đọc Intake.

## 2. API Customer 360 đã sửa (không đổi đường dẫn)

`GET /api/method/cellphones_c360.api.customer360.get_customer_360?customer_id=CUST-00001`

Trả:

```json
{
  "message": {
    "customer": {"name":"CUST-00001","customer_name":"Nguyễn Văn An","phone_number":"0901234567"},
    "contact": null,
    "lead": {"name":"..."},
    "leads": [{"name":"..."}],
    "deals": [{"name":"...","lead":"..."}],
    "orders": [{"name":"...","items":[]}],
    "tickets": [{"name":"...","customer":"..."}]
  }
}
```

**Ví dụ minh họa cấu trúc, không phải response thật.** `lead` đơn giữ lại để các consumer cũ không lỗi. `get_customer_profile` nay trả toàn bộ `leads`, `deals`, `orders`, `after_sales_requests`. `get_customer_timeline` tổng hợp Order, Ticket, CRM Call Log, CRM Task theo tất cả Lead/Deal liên quan và Intake đã xác minh.

API giữ kiểm tra quyền `C360 Customer.read` và giới hạn dữ liệu liên quan bằng `frappe.get_list`/kiểm tra quyền từng document. Nếu người dùng không có quyền một DocType, phần đó là mảng rỗng/giá trị null, không tuỳ tiện vượt quyền.

## 3. Kịch bản kiểm thử cần chạy trên site thật

| ID | Kịch bản | Kỳ vọng | Trạng thái |
|---|---|---|---|
| R01 | Customer C1 có hai CRM Lead L1, L2; mỗi Lead có Deal | Profile C1 có 2 Lead và Deal đúng của chúng | Chưa chạy Frappe |
| R02 | CRM Deal D có Lead L1 thuộc C1 nhưng `custom_c360_customer=C2` | Save bị từ chối, không có dữ liệu liên kết sai | Chưa chạy Frappe |
| R03 | Tạo Order O1 có `customer=C1`, hai Order Item | Tổng tiền tính từ item; profile trả Order+items | Chưa chạy Frappe |
| R04 | Ticket T1 thuộc C1, `related_order=O1` | Lưu và thấy trên profile/timeline | Chưa chạy Frappe |
| R05 | Ticket T2 thuộc C2, `related_order=O1` | Controller từ chối | Chưa chạy Frappe |
| R06 | C1 không có Lead, Order, Ticket | API trả mảng rỗng, không lỗi | Chưa chạy Frappe |
| R07 | Người không có quyền Customer | API từ chối đọc hồ sơ | Chưa chạy Frappe |
| R08 | Người có quyền Customer nhưng không có quyền Ticket | Không tiết lộ Ticket | Chưa chạy Frappe |
| R09 | Cùng số điện thoại/tên từ Web + Hotline | Một Customer, hai Intake; timeline có nguồn nếu có quyền | Chưa chạy Frappe |
| R10 | Intake mơ hồ → `resolve_duplicate` sau khi xác minh | Liên kết Customer cũ, không sinh Customer mới | Chưa chạy Frappe |
| R11 | Import CSV lần 2 | Source key trùng → `already_imported`, Customer không tăng | Chưa chạy Frappe |
| R12 | C360 Customer cũ chỉ có `crm_lead` | API vẫn đọc được Lead/Deal cũ | Chưa chạy Frappe |

### Đối chiếu dữ liệu thực

Chạy trong Bench:

```bash
bench --site crm.localhost execute cellphones_c360.cv2_audit.audit_schema
```

Kỳ vọng `missing_fields=[]`, `broken_links=[]`, `cross_customer_deals=[]`. Kiểm tra `get_customer_profile` và `get_customer_timeline` bằng tài khoản có quyền thực tế. Không đánh dấu Pass nếu chỉ dựa vào source hoặc unit tests offline.

## 4. Những thứ **chưa thực hiện** trong phạm vi CV2-01 đến CV2-05

- Chưa chỉnh frontend tạo Lead/Deal để chọn Customer trực tiếp (CV2-06).
- Chưa kiểm thử UI/API với quyền của nhiều nhân viên trên site thật (CV2-06, CV2-08).
- Chưa nhập thật CSV vào database của Khải hay bạn khác.
- Chưa giải quyết mô hình danh tính phức tạp: khách đổi số, nhiều người chung số, email dùng chung, gộp hai Customer đã tồn tại.
- Chưa bổ sung bảo vệ chống tranh chấp đồng thời hai request tạo cùng số ngay trong cùng mili-giây; cần khoá giao dịch/unique constraint phù hợp nếu dùng production.
