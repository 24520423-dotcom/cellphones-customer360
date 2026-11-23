# CV2-02 / CV2-03 – Dữ liệu đa kênh & xử lý trùng

## Bộ CSV mô phỏng

Tệp: `demo_customers_multichannel.csv` (12 dòng, Website/Facebook/Zalo/Hotline/Store). **Toàn bộ là dữ liệu giả lập**, email dùng miền `.test`. Không đưa danh sách khách hàng thật lên GitHub.

**Trường dữ liệu:** `source_channel`, `source_reference`, `customer_name`, `phone_number`, `email`, `received_at`.

`source_channel + source_reference` tạo khoá nguồn `SHA-256` duy nhất để import lại không nhân bản lượt tiếp nhận.

## Quy trình server

1. Xác thực quyền System Manager (API chỉ POST có session/CSRF từ Frappe).
2. Chuẩn hóa họ tên, số điện thoại Việt Nam (0 / +84 / 84), email viết thường; kiểm tra email, điện thoại, ít nhất một định danh.
3. Tìm các `C360 Customer` có cùng số điện thoại hoặc email. Không dò fuzzy rồi tự gộp.
4. **new:** tạo Customer mới, lưu Intake `Created`.
5. **linked:** đúng một hồ sơ có số điện thoại hoặc email khớp, họ tên tương đương và không có trường định danh xung đột → giữ Customer cũ, Intake `Linked`.
6. **review:** khác tên, xung đột email/điện thoại, hoặc nhiều ứng viên → không tạo Customer, Intake `Needs Review` và `candidate_customer`.
7. **rejected:** thiếu/không hợp lệ tên và định danh → Intake `Rejected`, có lý do.
8. Trường hợp nghi ngờ trùng cần người có quyền kiểm tra xác minh bằng `resolve_duplicate(intake_id, customer_id)` (POST), không tự động gộp hai hồ sơ đã có.

**Lưu ý:** số điện thoại chung trong gia đình, đổi số, email dùng chung có thể tạo dương tính giả. Quy tắc hiện là mức an toàn cho demo, chưa thay thế bài toán định danh thực tế hay chính sách xử lý dữ liệu cá nhân.

## Kết quả **dự kiến** trên site trống (không phải log chạy thật)

| Nguồn/mã | Hành động | Giải thích |
|---|---|---|
| Website / WEB-001 | new | Nguyễn Văn An đầu tiên |
| Store / STORE-001 | linked | Cùng An, cùng SĐT đã chuẩn hóa |
| Facebook / FB-001 | new | Trần Thị Bình |
| Hotline / HOT-001 | linked | Cùng An |
| Zalo / ZALO-001 | new | Lê Thanh Mai |
| Website / WEB-002 | new | Phạm Minh Khoa |
| Store / STORE-002 | linked | Cùng Bình |
| Facebook / FB-002 | review | SĐT An nhưng tên khác |
| Hotline / HOT-002 | review | SĐT An nhưng email xung đột |
| Website / WEB-003 | rejected | SĐT `012...` không được nhận diện là di động VN hợp lệ |
| Zalo / ZALO-002 | new | Nguyễn Thị Thảo theo email |
| Store / STORE-003 | linked | Cùng Thảo qua email, SĐT cũ để trống |

**Dự kiến:** 5 `new`, 4 `linked`, 2 `review`, 1 `rejected`. Tổng bản ghi Customer mới = 5, Intake = 12. Kết quả phụ thuộc dữ liệu đang có và phải đối chiếu bằng log trên Frappe site thật.

## Cách chạy sau khi cập nhật app trong Docker

Bên **Windows PowerShell tại root repository**, sao chép CSV vào container hiện tại:

```powershell
docker cp '.\Web CellphoneS\Docs\CV2-01-05\demo_customers_multichannel.csv' crm-frappe-1:/tmp/demo_customers_multichannel.csv
```

Bên **Docker terminal** (`docker exec -it crm-frappe-1 bash`, rồi `cd /home/frappe/frappe-bench`):

```bash
# Preview: không ghi dữ liệu, dự báo cả các dòng đứng trước trong CSV
bench --site crm.localhost execute cellphones_c360.api.intake.import_csv_from_bench --kwargs '{"path":"/tmp/demo_customers_multichannel.csv","dry_run":true}'

# Import thật: CHỈ chạy khi đã xem preview và backup
bench --site crm.localhost execute cellphones_c360.api.intake.import_csv_from_bench --kwargs '{"path":"/tmp/demo_customers_multichannel.csv","dry_run":false}'
```

Kết quả trả về gồm `rows` với `row`, `source_reference`, `action`, `intake_id`, `customer_id`, `reason` và `totals`. Lưu JSON của output làm **bảng đối chiếu**; `already_imported` thể hiện chạy lại không tạo bản ghi mới. Với dữ liệu có sẵn, dự kiến có thể khác.

**Lưu ý an toàn:** Đây là hàm import dành riêng cho Bench, có chủ đích sử dụng quyền Administrator trong môi trường tin cậy. API HTTP `ingest_customer` yêu cầu quyền `System Manager`; không public webhook hay sử dụng trên dữ liệu thật chưa được cấp phép.
