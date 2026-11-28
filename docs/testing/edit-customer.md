# Task 03 · Cập nhật khách hàng

## 1. Mục tiêu

Cho phép nhân viên chỉnh sửa thông tin đã xác minh trong SP01. Những giao dịch SP02–SP04 tiếp tục tham chiếu cùng một mã khách hàng.

## 2. Hiện trạng

Hồ sơ được đọc theo quyền bằng `get_customer_360`. Form tạo dùng metadata từ `customers.get_access`. Trước thay đổi, DocType chưa bật Track Changes.

## 3. Phương án triển khai

Dùng lại CustomerForm với dữ liệu của hồ sơ. API kiểm tra quyền đọc, quyền ghi từng hồ sơ, quyền trường và phiên bản hiện tại. Controller áp dụng cùng validation định danh như tạo mới. Bật Track Changes trên DocType để Frappe ghi Version.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/customers.py` và `api/customer360.py` trong cùng package.
- Windows: `backend/cellphones_c360/cellphones_c360/cellphones_customer_360/doctype/c360_customer/c360_customer.json` và `test_c360_customer.py`.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/components/Customer360/CustomerForm.vue` và `frontend/src/pages/Customer360Detail.vue` trong cùng repo CRM.

## 5. Các bước thực hiện

1. Chạy `bench --site crm.localhost backup` trong Bench hiện có. Bản sao trước thay đổi mang tiền tố `20261124_123306-crm_localhost` trong `sites/crm.localhost/private/backups/`.
2. Chạy `bench --site crm.localhost reload-doc cellphones_customer_360 doctype c360_customer` để nạp cấu hình Version. Chạy `bench build --app crm` để cập nhật giao diện.
3. Mở hồ sơ, chọn **Edit Customer**, sửa dữ liệu và chọn **Save**. Kiểm tra tên và mã hồ sơ sau khi tải lại.

## 6. Luồng nghiệp vụ

Nhân viên → Edit Customer → điền sẵn hồ sơ → nhập thay đổi → kiểm tra quyền, phiên bản, định dạng và xung đột → lưu → tải lại hồ sơ và ghi Version. Khi phiên bản đã thay đổi, đóng form và tải lại hồ sơ trước khi thử tiếp.

## 7. Kiểm thử

| Test ID | Nghiệp vụ | Điều kiện đầu vào | Các bước | Kết quả mong đợi | Kết quả thực tế | Pass/Fail | Minh chứng |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EC-01 | Sửa tên và ghi Version | Hồ sơ có Contact | Cập nhật tên, đọc lại hồ sơ và Version | Tên thay đổi, giữ Contact và mã khách hàng, ghi Version | Đã xác nhận trên MariaDB | Pass | `test_edit_preserves_contact_and_records_version` |
| EC-02 | Dữ liệu đồng thời và trường hệ thống | Hai yêu cầu dùng cùng phiên bản | Thử thay ID, lưu yêu cầu hợp lệ, tiếp tục lưu bằng phiên bản cũ | Từ chối đổi ID và yêu cầu cũ | PermissionError và TimestampMismatchError, dữ liệu lần lưu đầu được giữ | Pass | `test_edit_rejects_unchanged_revision_and_protected_fields` |
| EC-03 | Cập nhật email | Hai hồ sơ | Lưu email cũ bằng chữ hoa, sau đó lưu cùng email vào hồ sơ thứ hai | Chấp nhận hồ sơ hiện tại, từ chối hồ sơ khác | Đã xác nhận cả hai nhánh | Pass | `test_edit_checks_duplicate_excluding_current_customer` |
| EC-04 | Sửa hồ sơ trên Vue | Hồ sơ giả lập và tài khoản System Manager thử nghiệm | Mở form đã điền, sửa tên, lưu và tải lại | Dữ liệu cập nhật, giữ nguyên route theo mã khách hàng | Đã xác nhận trên Chrome và site `crm.localhost` | Pass | [Hồ sơ đã sửa](../../screenshots/task03-customer-updated.png) |

## 8. Output bàn giao

Form Edit Customer, API cập nhật trường cho phép, cấu hình Version và kiểm thử hồi quy.

## 9. Tiêu chí hoàn thành

Đã kiểm chứng thao tác sửa qua Vue, tải lại hồ sơ, giữ liên kết Contact và ghi Version. Các vai trò bổ sung được kiểm tra tại Task 13.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: edit Customer 360 profiles with version history`. Xuất lại Git Patch từ nhánh CRM sau khi kiểm thử.
