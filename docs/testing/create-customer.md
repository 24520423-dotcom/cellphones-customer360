# Task 02 · Tạo khách hàng

## 1. Mục tiêu

Tạo hồ sơ thống nhất trong SP01 khi nhân viên tiếp nhận khách hàng trực tiếp.

## 2. Hiện trạng

Danh sách Customer 360 đã có tìm kiếm, phân trang và điều hướng đến hồ sơ. Custom App có DocType và API quyền. Task 02 bổ sung thao tác tạo từ danh sách.

## 3. Phương án triển khai

Form dùng Frappe UI và Link chuẩn CRM. `customers.get_access` cung cấp metadata theo quyền. Form gọi `frappe.client.insert` và thực thi controller `C360 Customer`.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/customers.py` và `cellphones_customer_360/doctype/c360_customer/` trong cùng package.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/Customer360.vue` và `frontend/src/components/Customer360/CustomerForm.vue` trong cùng repo CRM.
- Windows: `frappe-crm-native/patches/cellphones-c360.patch`.

## 5. Các bước thực hiện

1. Trong Bench, build bằng `bench build --app crm`. Form tạo sử dụng metadata đã hiện diện trên site.
2. Mở `/crm/customer360` bằng tài khoản có quyền Create trên C360 Customer.
3. Chọn **Create Customer**, nhập thông tin khách hàng, chọn nguồn hoặc Link nếu cần, rồi chọn **Save**.
4. Kiểm tra hồ sơ vừa mở và tải lại trang để xác nhận dữ liệu lưu trong MariaDB.

## 6. Luồng nghiệp vụ

Nhân viên → Create Customer → nhập thông tin → Frappe kiểm tra quyền → controller chuẩn hóa và đối chiếu → lưu và mở hồ sơ mới. Thiếu trường bắt buộc, dữ liệu sai hoặc trùng định danh giữ người dùng trên form và hiển thị lỗi.

## 7. Kiểm thử

| Test ID | Nghiệp vụ | Điều kiện đầu vào | Các bước | Kết quả mong đợi | Kết quả thực tế | Pass/Fail | Minh chứng |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CC-01 | Tạo trên Vue | Tài khoản System Manager giả lập, email `example.test` | Nhập tên và email có khoảng trắng, lưu, refresh | Mở hồ sơ mới, dữ liệu chuẩn hóa và còn sau refresh | Đã xác nhận trên Chrome và site `crm.localhost` | Pass | [Form](../../screenshots/task02-create-customer.png), [Hồ sơ đã lưu](../../screenshots/task02-customer-persisted.png) |
| CC-02 | Metadata và chuẩn hóa | Administrator trong kiểm thử ORM | Lấy metadata, insert tên/email/nguồn cần chuẩn hóa | Metadata đúng, giá trị chuẩn hóa trong database | Giá trị đọc lại khớp kỳ vọng | Pass | `test_create_uses_live_metadata_and_normalizes` |
| CC-03 | Dữ liệu sai | Tên trắng, email sai, số điện thoại sai | Gọi native insert từng bộ dữ liệu | ValidationError | Ba trường hợp đều bị từ chối | Pass | `test_rejects_invalid_customer` |
| CC-04 | Email trùng | Email đã tồn tại | Insert cùng email ở dạng viết hoa | Từ chối và không lộ tên/mã hồ sơ | Lỗi không chứa tên/mã hồ sơ trùng | Pass | `test_detects_duplicate_without_disclosing_record` |
| CC-05 | Thiếu quyền | Guest | Kiểm tra quyền và gọi native insert trong bài kiểm thử | Từ chối | Quyền Create bằng false, insert trả PermissionError | Pass | `test_guest_has_no_create_permission` |

## 8. Output bàn giao

Nút Create Customer, form Vue, metadata API, kiểm tra controller, Git Patch và hai ảnh của dữ liệu giả lập.

## 9. Tiêu chí hoàn thành

Đã kiểm tra lưu và tải lại từ giao diện, validation bắt buộc, điều kiện trùng và từ chối phiên không có quyền ghi.

## 10. Commit và cập nhật tiến độ

CRM dùng commit `feat: add native Customer 360 creation form`. Repo Windows lưu Git Patch, kiểm thử và tài liệu theo tính năng. Tiếp theo tích hợp Edit Customer và Version.
