# CellphoneS Customer 360 · Snapshot `demo-v2`

**Đây là bản cập nhật của giai đoạn CV2-01 đến CV2-05**, đóng gói cùng repo (không phải database dump). Dùng được cho cả nhóm sau khi pull code và import vào từng Frappe site.

- Snapshot data: `Web CellphoneS/Docs/CV2-01-05/snapshots/demo-v2/` (54 Customer, 144 Intake, 94 Lead, 76 Deal, 62 Order, 100 Item, 45 Ticket, 12 Registration Request).
- Mã importer có idempotency: `Web CellphoneS/backend/cellphones_c360/cellphones_c360/snapshot_seed.py`.
- Validate offline: `Web CellphoneS/Docs/CV2-01-05/validate_snapshot_v2.py`.
- Hướng dẫn từng lệnh PowerShell/Docker/Git: `Web CellphoneS/Docs/CV2-01-05/DEMO-V2-IMPORT-GIT.md`.
- Kịch bản demo website: `Web CellphoneS/Docs/CV2-01-05/DEMO-V2-SCENARIOS.md`.

**Không ghi đè `demo-v1` hoặc mã nguồn CV2 hiện có.** Bộ này chỉ bổ sung `demo-v2`, một importer mới và tài liệu kiểm chứng.

**Đã kiểm thử:** kiểm tra offline checksum, ID, quan hệ dữ liệu, status, số tiền đơn hàng và giả lập kết quả phân loại trùng bằng đúng hàm `cv2_utils.py` của patch CV2. **Chưa kiểm thử import trên site Frappe đang chạy của Khải**; phải backup, dry-run và test thật trước khi merge lên main.

**Không được đưa lên GitHub:** file backup `*.sql.gz`, `*.tar`, `site_config.json`, API token, `.env`, dữ liệu khách hàng thật. GitHub chỉ lưu CSV demo và code.
