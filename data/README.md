
# Dữ liệu demo tiếp nhận khách hàng

Các bản ghi đều giả lập. Email dùng miền `example.test`. Số điện thoại trong CSV phục vụ kiểm tra định dạng và đối chiếu.

| File | Dữ liệu | Kết quả kỳ vọng khi chạy theo thứ tự |
| --- | --- | --- |
| [customers_online.csv](customers_online.csv) | Website, App, Facebook, Zalo và Hotline | 5 Created |
| [customers_offline.csv](customers_offline.csv) | Nhập tại cửa hàng, bản ghi POS giả lập, cùng một khách qua kênh khác | 2 Created, 1 Linked |
| [customers_duplicates.csv](customers_duplicates.csv) | Trùng cả định danh, dùng chung số, trùng tên và dữ liệu sai | 1 Linked, 1 Needs Review, 1 Created, 1 Invalid |

Gửi nội dung CSV UTF-8 dưới khóa `csv_text` đến `POST /api/method/cellphones_c360.api.intake.process_csv` từ phiên Frappe có quyền. Với từng nguồn, hãy giữ nguyên `source_record_id` qua các lần gửi lại. Kết quả ghi nhận theo từng dòng. Xem hướng dẫn và mapping trong [tiếp nhận đa kênh](../docs/integration/customer-intake.md).

Từ thư mục gốc repo, chạy bộ demo đầy đủ và kiểm tra replay trong giao dịch rollback:

```powershell
.\deployment\cellphones-c360\import-demo.ps1
```

Thêm `-Apply` khi quản trị viên muốn lưu bộ dữ liệu giả lập vào site demo. [demo-workflows.json](demo-workflows.json) định nghĩa Lead, Deal, đơn, Ticket và nhân viên demo. Tài khoản demo được để vô hiệu hóa và chỉ xuất hiện khi role tương ứng có trên site. Xem [kịch bản trình diễn](../docs/testing/demo-scenario.md).
