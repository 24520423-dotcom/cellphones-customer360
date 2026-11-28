# Task 07 · Liên kết bán hàng CRM

## 1. Mục tiêu

SP02 theo dõi mọi lần khách phát sinh nhu cầu trên cùng mã Customer 360.

## 2. Hiện trạng

CRM gốc có các form Lead, Deal, Contact, các pipeline và **Convert to Deal**. Hồ sơ trước đây chỉ truy vấn Deal theo một Lead chính.

## 3. Phương án triển khai

Giữ liên kết đơn trị cũ và dùng `crm_links` cho các thực thể bổ sung. Deal được tìm qua liên kết trực tiếp, `CRM Deal.lead` hoặc bảng con `CRM Contacts` nối với `Contact`. Customer 360 chỉ hiển thị các tài liệu CRM trong quyền đọc. Tạo từ modal gốc kiểm tra quyền và cập nhật liên kết trong cùng request.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/crm_links.py`, `api/customers.py`, `api/customer360.py` và `cellphones_customer_360/doctype/c360_customer/test_crm_links.py` trong cùng package.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/Customer360Detail.vue`, `frontend/src/components/Customer360/LinkCRMRecord.vue` và `frontend/src/components/Modals/{LeadModal,DealModal}.vue` trong repo CRM.

## 5. Các bước thực hiện

1. Sau metadata Task 06, chạy `bench build --app crm`.
2. Mở Customer 360 và tab **Leads & Deals**. Chọn **Create Lead**, **Create Deal** hoặc **Link CRM Record** nếu có quyền.
3. Trong Lead chuẩn, cập nhật tư vấn, trạng thái và dùng **Convert to Deal**. Quay lại Customer 360 để xem lịch sử.
4. Khi khách quay lại, mở mã khách hàng cũ và tạo thêm Lead hoặc Deal.

## 6. Luồng nghiệp vụ

Nhân viên → nhận nhu cầu trên hồ sơ có sẵn → tạo hoặc liên kết Lead, Deal hay Contact → kiểm tra quyền hai phía → lưu liên kết → theo dõi pipeline chuẩn. Khách mua lại có thể có nhiều Deal và một Deal có thể phát sinh trực tiếp. Xác nhận đơn và thanh toán thuộc luồng đơn hàng.

## 7. Kiểm thử

Kiểm thử trên site tạo hai Lead cho cùng khách hàng, chuyển đổi Lead bằng API chuẩn, kiểm tra replay của chuyển đổi, tạo Deal trực tiếp và tìm Deal theo Contact. Liên kết lặp giữ một quan hệ. Guest bị từ chối. Dữ liệu backend kiểm thử được rollback.

Chrome đã mở modal Lead chuẩn với dữ liệu điền sẵn, tạo Lead, điều hướng đến Lead và tìm lại liên kết trên Customer 360. Các hồ sơ UI giả lập đã được dọn sau kiểm thử. [Modal Lead từ hồ sơ khách hàng](../../screenshots/task07-create-linked-lead.png)

## 8. Output bàn giao

Tab Leads & Deals nhiều bản ghi, modal chuẩn, liên kết CRM, API và test cases.

## 9. Tiêu chí hoàn thành

Kết quả của lần mua đầu và lần mua lại xuất hiện theo cùng mã khách hàng. Tài liệu có thể mở trong các trang CRM gốc tương ứng.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: link Customer 360 to native CRM sales records`. Nghiệp vụ đơn hàng tiếp tục từ Deal đã liên kết.
