# Task 09 · Chăm sóc sau bán

## 1. Mục tiêu

SP04 tiếp nhận, phân công và giải quyết yêu cầu hỗ trợ. Sau khi bàn giao, lịch chăm sóc được lập trước ngày hẹn.

## 2. Hiện trạng

Custom App có Customer Support Ticket và API xác định quyền. Frappe CRM có Task và cơ chế scheduler. Ticket đã kiểm tra khách hàng của đơn liên quan và nội dung xử lý khi đóng.

## 3. Phương án triển khai

After-sales dùng chung danh sách với Orders. Form, chi tiết và phân quyền theo Frappe Desk. Warranty, Return và Exchange yêu cầu đơn Completed của cùng khách hàng. Nhân viên phải được phân công trước In Progress, Resolved hoặc Closed. Frappe ghi Version và controller tự lưu thời điểm giải quyết.

Scheduler rà soát hàng giờ các đơn đã hoàn tất có `completed_at` và tạo một CRM Task với hạn sau ba ngày. Task tham chiếu đơn hàng, `care_task` giữ liên kết để lần chạy sau dùng lại. Đơn lịch sử chỉ tham gia khi có thời điểm hoàn tất được ghi nhận.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/after_sales.py`, `care.py`, `hooks.py` và `cellphones_customer_360/doctype/customer_support_ticket/` trong cùng package.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/CustomerAfterSales.vue`, `src/components/Customer360/CustomerWorklist.vue` và `src/pages/Customer360Detail.vue` trong repo CRM.

## 5. Các bước thực hiện

1. Sao lưu site và dùng `bench --site crm.localhost migrate --skip-search-index` để nạp metadata, Version và scheduler. Dùng `bench build --app crm` cập nhật Vue.
2. Chọn **After-sales**, lọc theo mã, chủ đề, loại, trạng thái hoặc ưu tiên. Chọn **New Ticket** để tạo bản ghi Open.
3. Chọn khách hàng và đơn đã hoàn tất đối với bảo hành hoặc đổi trả, phân công nhân viên, tiến hành xử lý và ghi Resolution trước khi giải quyết.
4. Mở Customer 360 để xem Ticket và kết quả. Kiểm tra Tasks và liên kết Care Task trong đơn sau kỳ scheduler.
5. Để trình diễn tiếp thị, ghi **Marketing Consent** trên hồ sơ chuẩn và gọi API đề xuất demo. Lần trình diễn ghi dấu vết Comment trên hồ sơ.

## 6. Luồng nghiệp vụ

Nhân viên CSKH → nhận yêu cầu → xác minh khách và đơn → tạo Ticket → phân công → xử lý → ghi giải pháp → Resolved → Closed. Hồ sơ khác khách, đơn chưa hoàn tất với yêu cầu bảo hành, thiếu người xử lý hoặc thiếu giải pháp đi vào nhánh lỗi validation. Sau bàn giao, scheduler → tìm đơn cập nhật → tạo một Task có hạn ba ngày → ghi liên kết lên đơn.

## 7. Kiểm thử

Đã chạy 3 kiểm thử hỗ trợ trên MariaDB. Các kịch bản gồm đơn chưa hoàn tất, khác khách hàng, thiếu phân công, thiếu giải pháp, đóng Ticket, một Task trong hai lần chạy, hạn ba ngày và kiểm tra opt-in. Năm kiểm thử hồi quy Orders và Merge tiếp tục đạt.

Chrome đã lọc Ticket giả lập theo khách hàng và mở cả chi tiết lẫn form tạo chuẩn. [Danh sách After-sales](../../screenshots/task09-ticket-list.png).

## 8. Output bàn giao

Danh sách và form Ticket, phân công, kiểm soát trạng thái, lưu lịch sử, lịch CRM Task và kiểm thử.

## 9. Tiêu chí hoàn thành

Ticket tham chiếu đúng khách và đơn, lưu được giải pháp, truy xuất được trong Customer 360. Lịch theo đơn được tạo một lần, tính theo thời điểm hoàn tất và nhánh tiếp thị kiểm tra consent trên hồ sơ.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: manage after-sales tickets and follow-up tasks`. Timeline sẽ tổng hợp Ticket và Task chăm sóc qua liên kết đơn hàng.
