# Báo cáo kiểm thử

Kiểm thử thực hiện trên `crm.localhost`, Frappe 15.126.1, CRM 1.92.0 và MariaDB trong Docker phát triển hiện có. Chrome headless dùng tài khoản thử với dữ liệu `example.test`.

| Hạng mục | Kết quả |
| --- | --- |
| Suite Python/MariaDB | 26 kiểm thử đạt cho hồ sơ, intake, merge, CRM links, Orders, Ticket, Timeline, phân khúc và KPI |
| Ghi đồng thời | Hai giao dịch độc lập tạo cùng email. Một hồ sơ được ghi và yêu cầu còn lại bị từ chối |
| Trình duyệt | Tạo/sửa và tải lại, hợp nhất, Lead chuẩn, Orders, After-sales, 5 tab và Timeline, lọc phân khúc và KPI |
| Quyền hiện hành | Guest bị từ chối. Sales User thử nghiệm gọi URL trực tiếp và API đọc/ghi trả 403 |
| Bàn phím và di động | Tab list vào Timeline bằng End, focus đúng. Viewport 390 × 844 không cuộn ngang ở mức document |
| Dữ liệu đa kênh | 8 Created, 2 Linked, 1 Needs Review, 1 Invalid. Lần phát lại giữ nguyên kết quả |
| Demo nghiệp vụ | Hai giao dịch thanh toán và bàn giao, mua lại, Ongoing/Lost, đơn giao thất bại, Ticket và lịch. Seed thử và replay được rollback |
| Bàn giao mã nguồn | Kiểm tra replay Git Patch, Compose config, cú pháp PowerShell/Bash và Verify trên site hiện có |
| Mục chờ | Migration vai trò bộ phận và E2E theo quyền mới, cài New/Snapshot trên project được phép, push GitHub |

[Bảng E2E](end-to-end-test-cases.md) · [BPMN](bpmn-traceability.md) · [Ảnh minh chứng](../../screenshots/) · [Mục còn chờ](../known-issues.md)
