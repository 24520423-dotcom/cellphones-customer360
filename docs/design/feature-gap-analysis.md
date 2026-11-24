# Rà soát chức năng Customer 360

## 1. Mục tiêu

Xác định phần Frappe CRM và Custom App có thể dùng lại cho SP01–SP04 trên site hiện tại.

## 2. Hiện trạng

Máy Windows đang ở nhánh `feature/frappe-crm-native`, tại commit `3853504` khi bắt đầu rà soát. Docker Desktop đang chạy `crm-frappe-1`, `crm-mariadb-1` và `crm-redis-1`. Bench tại `/home/frappe/frappe-bench` báo Frappe 15.126.1 và CRM 1.92.0. Site `crm.localhost` đã cài `cellphones_c360`. CRM trong Docker ở nhánh `feature/cellphones-c360`, commit `261dc53`, trên base `638bf3db23e7142870819a213368e028866b79b1`.

| Chức năng | Frappe CRM có sẵn | Custom App có sẵn | Cần bổ sung | Hướng xử lý | Trạng thái kiểm thử |
| --- | --- | --- | --- | --- | --- |
| Danh sách và hồ sơ | Điều hướng, session và Frappe UI | `customer360.py`, danh sách, năm tab | Form và quyền thao tác | Mở rộng trang trong Git Patch | Site và phiên bản đã xác nhận. Kiểm thử CRUD theo từng task |
| Thêm và sửa hồ sơ | ORM, DocType Form, `frappe.client.insert`, Version | `customers.get_access` và DocType `C360 Customer` | Form trên SPA, metadata, kiểm tra lưu đồng thời, theo dõi thay đổi | Dùng Frappe UI và kiểm tra trong controller | Đã đọc mã nguồn, quyền site cần kiểm chứng theo vai trò |
| Chuẩn hóa và đối chiếu | Validation kiểu dữ liệu, naming series | Chuẩn hóa cơ bản điện thoại/email, kiểm tra trùng chính xác | Chuẩn hóa tên và nguồn, kiểm tra định dạng, bảo mật lỗi trùng, đồng thời | Bổ sung controller dùng chung cho ORM và Data Import | Chưa chạy kịch bản |
| Tiếp nhận đa kênh | Data Import, CRM Lead Source | Source Channel trong hồ sơ | Mã bản ghi nguồn, idempotency, nhật ký tiếp nhận | Thiết kế mapping CSV và bước xác minh | Chưa chạy kịch bản |
| Hợp nhất | Transaction, Link và Version | Liên kết đơn và Ticket đến khách hàng | Đối chiếu, phân quyền hợp nhất, bảo toàn hồ sơ nguồn | Áp dụng giao dịch giữ ID nguồn và audit | Chưa chạy kịch bản |
| Bán hàng | Lead, Convert to Deal, Deal, Contact, Organization | `leads.get_options`, `deals.get_options`; hồ sơ có một Lead và một Contact | Nhiều lần phát sinh cơ hội, Deal qua Contact, liên kết hai chiều | Dùng các trang CRM gốc | Đã đọc các điểm tích hợp |
| Đơn hàng | Frappe Desk, DocType Form và bảng con | Customer Order và Customer Order Item, tính tổng backend | Giao diện nghiệp vụ, thanh toán và bàn giao | Mở rộng DocType hiện có | Chưa chạy kịch bản |
| Chăm sóc sau bán | Task, Note, Call Log | Customer Support Ticket, `after_sales.get_capabilities` | Luồng xử lý, kiểm tra thời điểm, lịch chăm sóc | Mở rộng controller và dùng CRM Task | Chưa chạy kịch bản |
| Timeline | Hoạt động trên hồ sơ Lead và Deal | Tổng hợp đơn, Ticket và một phần hoạt động CRM | Nguồn tiếp nhận, Version, quan hệ nhiều Lead/Deal | Mở rộng API và giữ phân trang | Đã đọc mã nguồn |
| Phân khúc và dashboard | Dashboard và biểu đồ CRM | `analytics.get_analytics_overview` tổng hợp theo quyền | Phân khúc, KPI giao dịch thực tế, giao diện và khoảng thời gian | Kế thừa truy vấn hiện có | Chưa chạy kịch bản |
| Nhân viên và quyền | User, Role, Role Profile, User Permission | `access.py`, API quản trị và đăng ký nhân viên | Ma trận quyền theo phạm vi, kiểm thử từng vai trò | Cấu hình quyền Frappe và kiểm tra trên từng bản ghi | Metadata trong Git cấp quyền các DocType chính cho System Manager. Cần đối chiếu tùy chỉnh trên site |

## 3. Phương án triển khai

Giữ Customer 360 trên hai route hiện tại, dùng component của Frappe CRM và gọi API theo session. Dùng DocType hiện có cho khách hàng, đơn hàng và Ticket. Tách `Contact` là hồ sơ liên hệ khỏi `CRM Contacts` là bảng con nối Contact với Deal. Mối liên kết đơn trị `crm_lead` phục vụ tương thích hồ sơ cũ và cần cơ chế bổ sung để hỗ trợ mua lại.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/` và `backend/cellphones_c360/cellphones_c360/cellphones_customer_360/doctype/`.
- Windows: `frappe-crm-native/patches/cellphones-c360.patch`.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/Customer360.vue`, `Customer360Detail.vue`, `src/router.js` và `src/components/Layouts/AppSidebar.vue`.
- Docker: `/home/frappe/frappe-bench/apps/cellphones_c360` được cấu hình bind mount từ backend của repo Windows.

## 5. Các bước thực hiện

1. Trong PowerShell tại repo Windows, chạy `git status --short --branch` và xem lịch sử hai repository.
2. Kiểm tra container bằng `docker ps`. Trong Bench hiện có, chạy `bench version`, `bench --site crm.localhost list-apps` và kiểm tra Git của `apps/crm`.
3. Đối chiếu các API đã whitelist, quyền theo metadata và cách hai trang Vue sử dụng `call` từ Frappe UI. Rà soát này chỉ đọc mã và trạng thái môi trường.

## 6. Luồng nghiệp vụ

Nhân viên → mở Customer 360 → Frappe xác thực session và kiểm tra quyền → khách hàng được phép đọc xuất hiện trong danh sách → mở hồ sơ và tải các thực thể liên quan theo quyền. Yêu cầu sai quyền bị từ chối ở backend. Công việc tiếp nhận, chỉnh sửa hoặc chuyển tiếp sang luồng bán hàng được kiểm thử riêng theo từng task.

## 7. Kiểm thử

Git ở nhánh dự kiến và không có thay đổi khi bắt đầu. Ba container chính đang chạy, Bench xác nhận đúng phiên bản và site xác nhận đủ ba app. Các tiêu chí ghi dữ liệu, phân quyền theo tài khoản và kiểm thử giao diện được ghi lại theo từng tính năng.

## 8. Output bàn giao

Bảng phân tích khoảng trống, vị trí hai repository, kiểm kê API và quan hệ dữ liệu ưu tiên.

## 9. Tiêu chí hoàn thành

Mỗi chức năng trong phạm vi rà soát có quyết định về tái sử dụng tính năng chuẩn, mở rộng chức năng hiện có hoặc bổ sung chức năng mới.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `docs: audit native CRM and Customer 360 feature gaps`. Tiếp theo áp dụng quy tắc nhận diện và thêm form tạo khách hàng vào danh sách.
