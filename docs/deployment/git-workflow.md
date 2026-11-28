# Task 17 · Quản lý mã nguồn

## 1. Mục tiêu

Giữ lịch sử thay đổi đủ để thành viên khác tái lập và review bản Customer 360.

## 2. Hiện trạng

Repo Windows chứa Custom App, dữ liệu, tài liệu, triển khai và Git Patch trên `feature/frappe-crm-native`. Repo Frappe CRM trong container chứa cập nhật frontend trên `feature/cellphones-c360`. Base CRM là `638bf3db23e7142870819a213368e028866b79b1`. Commit CRM đã kiểm chứng ở đợt này là `ed135bb`.

## 3. Phương án triển khai

Commit từng chức năng trong repo thích hợp và xuất mailbox patch từ base. Kiểm tra khả năng replay từ base trong worktree tạm. Patch truy cập vai trò phòng ban nằm trong gói bàn giao quyền để áp dụng cùng lần migration được duyệt.

## 4. Các file liên quan

- Windows: `frappe-crm-native/patches/cellphones-c360.patch` và `department-access.patch`.
- Docker: `/home/frappe/frappe-bench/apps/crm`.

## 5. Các bước thực hiện

1. Chạy `git status --short --branch` và xem diff ở cả hai repo.
2. Build CRM bằng `bench build --app crm`, kiểm thử rồi commit trong repo CRM.
3. Trong container, xuất bằng `git -C apps/crm format-patch --stdout 638bf3db23e7142870819a213368e028866b79b1..HEAD`. Sao chép patch về repo Windows bằng `docker cp`.
4. Kiểm tra Git Patch trên đúng commit nền. Commit patch, backend, test và tài liệu trong repo Windows.
5. Sau khi quyền gửi ra GitHub được xác nhận, đồng bộ nhánh `feature/frappe-crm-native` đến remote `24520423-dotcom/cellphones-customer360` và kiểm tra trạng thái PR.

## 6. Luồng nghiệp vụ

Người phát triển → sửa và kiểm thử → commit đúng repo → xuất patch → so sánh cây Git → commit bản bàn giao → xác nhận đồng bộ nhánh.

## 7. Kiểm thử

Git Patch dựng lại đúng cây nguồn CRM từ commit nền. Patch truy cập vai trò qua `git apply --check`. Push bị xét duyệt tự động chặn vì quyền gửi mã nguồn và ảnh ra remote đang chờ xác nhận.

## 8. Output bàn giao

Lịch sử commit cục bộ, patch tái lập CRM, patch vai trò chuẩn bị và hướng dẫn cho PR.

## 9. Tiêu chí hoàn thành

Đã kiểm tra nhánh cục bộ và bản vá có thể áp dụng. Đồng bộ remote còn chờ xác nhận.

## 10. Commit và cập nhật tiến độ

Bản bàn giao dùng từng commit theo tính năng. Không commit backup, cấu hình site, secrets, Bench Volume hoặc thư viện sinh tự động.
