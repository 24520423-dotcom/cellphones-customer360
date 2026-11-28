# Task 13 · Quyền nhân viên Customer 360

## 1. Mục tiêu

Áp dụng quyền DocType, hồ sơ và cấp trường xuyên suốt SP01–SP04. Dùng User, Role Profile và User Permission của Frappe cho cấp quyền.

## 2. Hiện trạng

Site hiện tại đã xác nhận các DocType Customer, Order và Ticket dùng quyền System Manager trước migration vai trò mới. Quản trị nhân viên và duyệt đăng ký dùng API dành cho Administrator. Ma trận dưới đây mô tả cấu hình đã chuẩn bị trong mã nguồn. Áp dụng và kiểm thử các vai trò mới trên `crm.localhost` đang chờ xác nhận thay đổi quyền.

## 3. Phương án triển khai

| Chức năng | Administrator / System Manager | Sales Manager | Sales User | C360 Customer Service | C360 Operations | C360 Marketing |
| --- | --- | --- | --- | --- | --- | --- |
| Customer 360 | Toàn bộ theo quyền Frappe | Quản lý theo User Permission | Tạo, đọc và sửa theo owner và chia sẻ hợp lệ | Đọc khách có Ticket được giao hoặc được cấp User Permission | Đọc khách của đơn được giao hoặc có User Permission, ẩn điện thoại/email và liên kết CRM | Đọc khách active có consent, ẩn điện thoại/email và liên kết CRM |
| Lead, Deal và Contact | Quyền chuẩn CRM | Quyền chuẩn CRM | Quyền chuẩn CRM | Quyền chuẩn nếu có cấp quyền riêng | Truy cập theo cấp quyền riêng | Truy cập theo cấp quyền riêng |
| Orders | Toàn bộ | Quản lý theo User Permission | Theo chủ đơn | Đọc các đơn liên quan hồ sơ hỗ trợ | Đọc đơn được giao, cập nhật giao nhận và trạng thái đơn | Không có quyền DocType |
| Ticket | Toàn bộ | Quản lý theo User Permission | Đọc Ticket mình sở hữu | Tạo và xử lý Ticket được giao hoặc mình tạo khi chưa phân công | Đọc Ticket của khách liên quan vận hành | Không có quyền DocType |
| Analytics | Theo dữ liệu đọc được | Theo dữ liệu đọc được | Theo dữ liệu đọc được | Dữ liệu trong phạm vi hỗ trợ | Dữ liệu trong phạm vi vận hành | Theo hồ sơ có consent |
| Merge | Administrator hoặc System Manager có đủ quyền | Cần thêm C360 Merge Approver và đủ quyền trên bản ghi | Đối chiếu theo quyền đọc | Đối chiếu theo quyền đọc | Đối chiếu trường được đọc | Đối chiếu trường được đọc |
| Quản trị nhân viên C360 | Administrator | Cấp quyền qua công cụ Frappe khi được ủy quyền | Không có API quản trị | Không có API quản trị | Không có API quản trị | Không có API quản trị |

Role Profile dự kiến gồm C360 Customer Service, C360 Operations và C360 Marketing. Vai trò phòng ban chạy độc lập với Sales User. UI CRM nạp quyền vào startup khi áp dụng patch truy cập vai trò. Trường Fulfillment Owner trên đơn là căn cứ cho hàng đợi vận hành.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/permissions.py`, `hooks.py`, DocType metadata và `cellphones_customer_360/doctype/c360_customer/test_permissions.py`.
- Windows: `frappe-crm-native/patches/department-access.patch`.
- Docker: `/home/frappe/frappe-bench/apps/crm/crm/api/__init__.py` là đích kiểm tra của patch truy cập.

## 5. Các bước thực hiện

Sau khi quyền thay đổi được xác nhận, dùng quyền quản trị để sao lưu site, áp dụng patch truy cập và migrate. Trong Desk, mở **Role Profile**, **User** và **User Permission** để cấp phạm vi cho tài khoản tương ứng. Vai trò phòng ban độc lập giúp duy trì giới hạn field-level. Áp dụng quy tắc cấp riêng khi cần cấp quyền CRM chuẩn.

## 6. Luồng nghiệp vụ

Quản trị → tạo hoặc cập nhật User → gán Role Profile và User Permission → đăng nhập → truy vấn theo role, phạm vi bản ghi và quyền trường → cho phép thao tác hoặc trả PermissionError. API tạo/sửa/hợp nhất kiểm tra quyền khi được gọi trực tiếp.

## 7. Kiểm thử

Kiểm thử nghiệp vụ trước đó đã xác nhận Guest bị từ chối trực tiếp ở API. Chrome đã dùng System Manager thử nghiệm với phiên thực. Patch mở quyền truy cập giao diện cho role phòng ban đã qua `git apply --check`. Bộ kiểm thử hai Sales User, Sales Manager, CSKH, Vận hành và Marketing đã được chuẩn bị cho lần chạy sau migration. Xét duyệt tự động chặn lần migrate cấu hình quyền trên site hiện tại, nên ma trận vai trò mới chưa được xác nhận trên site.

## 8. Output bàn giao

Ma trận, Role/Role Profile khai báo, điều kiện theo quyền khách hàng và phân công, giới hạn trường, kiểm thử và patch truy cập.

## 9. Tiêu chí hoàn thành

Cần áp dụng migration được duyệt, chạy bộ kiểm thử từng vai trò và xác minh đường dẫn/API trực tiếp bằng tài khoản thử.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: prepare scoped Customer 360 staff permissions`. Trạng thái Task 13 là chờ xác nhận migration và kiểm thử quyền mới.
