# Quy ước snapshot dùng chung qua GitHub (CV2-01 đến CV2-05)

## 1. Mô hình đã chọn

Snapshot ở đây là **dataset seed/fixture DEMO theo phiên bản**, không phải sao chép nguyên database SQL. Các máy có cùng dữ liệu mẫu ban đầu; các thay đổi cục bộ không tự cập nhật trở lại GitHub.

> Trong Frappe, `bench backup --with-files` tạo bản sao lưu site (database và file) để khôi phục thảm họa. `bench restore` khôi phục trạng thái site, có thể thay thế dữ liệu đích: không dùng trực tiếp trên database đang có việc làm chưa sao lưu. Những file này **không được commit lên GitHub**.

## 2. Cấu trúc thư mục đề xuất

```text
Web CellphoneS/Docs/CV2-01-05/snapshots/
└── demo-v1/
    ├── manifest.json
    ├── customers.csv
    ├── leads.csv
    ├── deals.csv
    ├── orders.csv
    ├── order_items.csv
    ├── tickets.csv
    └── intakes.csv
```

Các CSV trong `demo-v1` là **dataset logic minh họa, chưa phải file import thẳng vào Frappe**. Một bước mapping/importer phải chuyển `snapshot_id` thành tên `name` của bản ghi Frappe, xử lý trường bắt buộc theo phiên bản CRM và quan hệ Link/Table.

## 3. Trường và quy tắc

- `snapshot_id`: mã ID ổn định trong gói, không phải tên chứng từ Frappe.
- `*_snapshot_id`: tham chiếu đến ID trong các CSV khác, phải tồn tại và đúng Customer.
- `manifest.json`: tên gói, phiên bản, `data_type=synthetic_demo`, version app dùng để kiểm thử, thứ tự import, checksum + số dòng.
- `source_channel + source_reference`: chống nhập lại cùng một sự kiện intake.
- `customers.csv`: họ tên/điện thoại/email đều giả lập. Mẫu `example.test` không gửi email được.
- Chỉ commit bản demo sau khi có review dữ liệu nhạy cảm, kiểm tra schema và kiểm thử an toàn.

## 4. Quy trình trên máy chủ tạo snapshot

1. Hoàn thiện app schema + migration theo CV2-01, chạy `bench --site crm.localhost execute cellphones_c360.cv2_audit.audit_schema`.
2. Dùng dữ liệu giả lập; nếu xuất từ máy bạn đang có khách hàng, phải **ẩn danh và loại tài khoản/mật khẩu/token/đính kèm trước**.
3. Xuất theo từng DocType hoặc tạo dataset CSV trong format logic; tạo manifest/checksum và chạy validator offline.
4. Thử import vào **site test mới hoặc máy test đã backup**; không đè site đang làm việc. Importer dùng Frappe ORM và bảng ánh xạ logical ID→document name.
5. Xác thực counts, lookup từ Customer, lần import lại, dedupe review, quyền API. Lưu report kết quả.
6. Commit `demo-v1` + hướng dẫn + test result qua Pull Request, các thành viên review trước khi merge.

## 5. Quy trình trên máy nhận snapshot

1. `git pull`/`git fetch` lấy code + `demo-v1` từ GitHub, nhưng **không tự có database**.
2. Xác nhận `frappe`, `crm`, `cellphones_c360` tương thích manifest; chạy migration/app patch đầy đủ và audit metadata.
3. Sao lưu database site đích (`bench --site crm.localhost backup --with-files`), copy backup ra Windows, ưu tiên dùng site test riêng.
4. Chạy `python validate_snapshot.py <đường dẫn demo-v1>` trên Windows để kiểm tra file/quan hệ/checksum.
5. Chạy **dry-run của importer khi đã phát triển/kiểm thử**, xem dữ liệu mới/trùng/nghi trùng/mồ côi; chỉ import khi đã duyệt.
6. Lưu file mapping `snapshot_id→name` riêng trên máy, không đẩy dữ liệu cá nhân lên GitHub.
7. Test `get_customer_360`, hồ sơ timeline và React UI. Kết quả không PASS thì không coi đã đồng bộ snapshot thành công.

**Chưa có trong gói này:** importer tự động tất cả DocType trên Frappe, bản sao database thật hoặc script ghi đè site. Không thực hiện `bench restore` trên site đang làm việc chỉ để xem dữ liệu demo.

## 6. Quy trình phát hành và thay đổi

- `demo-v1`: bất biến sau khi công bố (freeze). Muốn sửa dữ liệu -> `demo-v2` và PR mới.
- Cả nhóm thống nhất dùng cùng bản snapshot trong kịch bản nghiệm thu.
- Nếu một bạn thêm khách hàng trên site cá nhân, các máy khác **không thấy** thay đổi đó; muốn chia sẻ phải xuất và nhập bản demo mới hoặc dùng backend chung.
- Người quản lý snapshot giữ changelog, schema version, mã dữ liệu demo/nguồn, tổng số bản ghi và biên bản kiểm thử.

## 7. Lệnh mẫu an toàn

Trong PowerShell, tại thư mục `Web CellphoneS/Docs/CV2-01-05`:

```powershell
python .\validate_snapshot.py .\snapshots\demo-v1
```

Kiểm tra container/app trên máy Khải:

```powershell
docker exec crm-frappe-1 bash -lc "cd /home/frappe/frappe-bench && bench --site crm.localhost list-apps"
```

**Không** đưa nguyên site backup của bạn lên repository: backup có thể chứa dữ liệu cá nhân, tài khoản, config và secret. Nếu cần chuyển site riêng phục vụ demo, trao đổi backup qua kênh riêng an toàn, kiểm soát quyền và thử restore trên site mới.
