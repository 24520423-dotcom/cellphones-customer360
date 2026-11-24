# Task 18 · Triển khai và bàn giao

## 1. Mục tiêu

Tái lập bản CRM của dự án từ mã nguồn, giữ công việc cập nhật site hiện có tách khỏi tạo site mới.

## 2. Hiện trạng

Môi trường phát triển đang chạy `crm.localhost` trong `crm-frappe-1`. Script Snapshot dựa trên bộ sao lưu ngày 22/11/2026. Release nguồn mới dùng bản mã đã khóa, Git Patch và dữ liệu giả lập.

## 3. Phương án triển khai

| Thành phần | Nguồn |
| --- | --- |
| Frappe Framework | `v15.126.1`, commit `2e9ecdc03fa5b5b8d1ba05224a1aff7dad832bd0` |
| Frappe CRM | 1.92.0, commit nền `638bf3db23e7142870819a213368e028866b79b1` |
| Custom App | `backend/cellphones_c360` bind mount song song với Bench hiện có |
| Git Patch | `cellphones-c360.patch` tái lập giao diện, `department-access.patch` mở quyền vào CRM sau cấu hình được duyệt |
| Dockerfile | Bench image khóa digest trong Dockerfile. Python 3.12.15 |
| Thương hiệu | Logo/favicon đóng gói trong public assets và FCRM Settings trên site mới |
| Demo | Ba CSV, workflow JSON và seed có thử lại |

## 4. Các file liên quan

- Windows: `deployment/cellphones-c360/{Dockerfile,docker-compose.yml,.env.example,setup.ps1,setup-source.ps1,release.sh,import-demo.ps1}`.
- Windows: `frappe-crm-native/patches/`, `backend/cellphones_c360/cellphones_c360/branding.py`, `data/`.
- Docker: `/home/frappe/frappe-bench`, `apps/crm` và `sites/<site>`.

## 5. Các bước thực hiện

1. Kiểm tra hiện hành bằng `setup.ps1 -Mode Verify`. Đối chiếu nhánh CRM, commit và trạng thái Git theo [Git workflow](git-workflow.md).
2. Với site đang có, sau phê duyệt thay đổi Role/DocPerm, dùng `setup.ps1 -Mode Update -ApplyDepartmentRoles -Container crm-frappe-1 -Site crm.localhost`. Update sao lưu database và tệp đính kèm trước khi áp dụng, kiểm tra cây Git, chuẩn bị bản vá trong worktree rồi fast-forward khi hợp lệ. Tiếp tục cài app thiếu, migrate, build và clear-cache.
3. Với máy hoặc project mới được cấp quyền, dùng [Installation Guide](installation-guide.md). New tạo Bench và site mới, áp dụng patch đúng base, cấu hình FCRM Settings và hỗ trợ import demo.
4. Kiểm tra `bench version`, `bench --site <site> list-apps`, đăng nhập CRM, truy cập Customer 360, Orders, After-sales, Analytics và kiểm thử quyền trước khi bàn giao tài khoản.
5. Snapshot cũ dành cho bản sao đúng bộ tệp đã được chuẩn bị sẵn. Dùng `-Mode Snapshot` trên môi trường riêng của bản backup.

## 6. Luồng nghiệp vụ

Người triển khai → chọn Verify, Update hoặc New → kiểm tra Bench và site → kiểm tra patch → sao lưu nếu Update → cài/migrate/build → kiểm chứng API và UI → bàn giao. Lỗi patch được xử lý trong worktree trước khi cập nhật nhánh đang dùng.

## 7. Kiểm thử

Kiểm tra cú pháp script, cấu hình Compose, bản Git Patch ở commit nền, phần Verify trên Frappe hiện có và trial demo. Khởi tạo New và áp dụng quyền phòng ban trên site hiện có cần kiểm chứng ở môi trường được duyệt.

### Xử lý lỗi và rollback

- Nếu patch lỗi, giữ lại thông báo Git và đối chiếu commit nền cùng thay đổi cục bộ. Release chỉ fast-forward sau khi áp dụng được trong worktree.
- Nếu migrate hoặc build lỗi, ghi lại commit đã dùng và lỗi từ Bench. Với lỗi asset, áp dụng lại mã nguồn phiên bản đã kiểm chứng và build lại trong thời gian bảo trì.
- Nếu cần rollback dữ liệu, dùng bộ database/public/private files và cấu hình được tạo trước cập nhật trong `sites/<site>/private/backups`. Thử khôi phục trên site đã được phê duyệt và dùng quy trình Bench được nhóm xác nhận trước khi thay site hiện hành. Mật khẩu và file backup được quản lý ngoài Git.

## 8. Output bàn giao

Cấu hình Compose, pin nền tảng, script Verify/New/Update, cơ chế áp dụng patch, thiết lập thương hiệu, hướng dẫn rollback và dữ liệu demo.

## 9. Tiêu chí hoàn thành

Cần xác nhận cài mới trên máy được cấp phép, smoke test bằng tài khoản quản trị và nghiệp vụ, đối chiếu quyền thực tế và xác nhận dữ liệu demo sau import.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `chore: package pinned Customer 360 source deployment`. Các bước còn chưa chạy được ghi trong [Known Issues](../known-issues.md).
