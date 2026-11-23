# CellphoneS Customer 360 – DEMO-V2: nhập dữ liệu và phát hành GitHub

**Phiên bản:** `demo-v2` (23/11/2026) · **Loại:** bộ dữ liệu **giả lập**, đóng gói CSV + manifest SHA256 + công cụ nhập. **Không phải** bản backup SQL/MariaDB. Dùng chung mã nguồn + snapshot qua Git, **không** tự đồng bộ dữ liệu khi người dùng sửa ở mỗi máy.

## 1. Danh sách dữ liệu

| File | Số dòng dữ liệu | Ý nghĩa |
|---|---:|---|
| `customers.csv` | 54 | 51 cá nhân, 3 tổ chức, nguồn từ 6 kênh |
| `intakes.csv` | 144 | 54 mới, 64 liên kết, 18 xem xét, 8 từ chối |
| `leads.csv` | 94 | 7 giai đoạn Lead, ghi chú tư vấn |
| `deals.csv` | 76 | 7 giai đoạn Deal, lý do Lost, giá VND |
| `orders.csv` | 62 | Draft, Confirmed, Processing, Completed, Cancelled |
| `order_items.csv` | 100 | Điện thoại, máy tính, tablet, phụ kiện (giá mô phỏng) |
| `tickets.csv` | 45 | 6 loại yêu cầu, 5 trạng thái và mức ưu tiên |
| `registration_requests.csv` | 12 | 8 Pending và 4 Rejected, **không** tạo User/nhắn email |

`offline_expected_kpis.json` dùng để đối chiếu tổng từ chính CSV: **44 đơn hợp lệ**, tổng **678.850.000 VND** (Confirmed + Processing + Completed), **7 khách mua lặp** trong bộ demo. Tổng trên website của site đã có dữ liệu cũ sẽ lớn hơn.

## 2. Đưa ZIP vào repository trên Windows

Mở PowerShell (nếu chưa vào thư mục Git):

```powershell
cd "C:\Users\TRUONG PHAN KHAI\Downloads\CRM\WEB\cellphones-customer360"
git branch --show-current
git status
```

Mong đợi branch `feature/khai-cv2-01-05`. **Nếu branch khác, dừng trước khi giải nén.** Tải ZIP về `Downloads`, sau đó:

```powershell
Expand-Archive -Path "$HOME\Downloads\CellphoneS-CV2-DEMO-V2-Snapshot-Git.zip" -DestinationPath "." -Force
git status
```

ZIP chỉ thêm thư mục `demo-v2`, tài liệu mới và file code importer `snapshot_seed.py`. Không thay thế `demo-v1`, không thay Docker Compose, không chỉnh sửa các file CV2 đang làm.

## 3. Kiểm tra snapshot trên Windows mà không cài Python

Từ thư mục repository:

```powershell
docker run --rm -v "${PWD}:/repo" -w /repo python:3.11-slim python "Web CellphoneS/Docs/CV2-01-05/validate_snapshot_v2.py" "Web CellphoneS/Docs/CV2-01-05/snapshots/demo-v2"
```

Kỳ vọng `PASS` về checksum/quan hệ/tổng tiền/trạng thái, **chưa phải nhập thành công lên Frappe**.

## 4. Sao lưu site trước khi nhập và copy ra ngoài Docker

**Ưu tiên site thử nghiệm riêng**. Trên máy Khải hiện site là `crm.localhost`. Các lệnh sau áp dụng vào site này nếu chấp nhận dữ liệu demo được **cộng thêm** vào dữ liệu CV2-01..05 đang có.

```powershell
docker exec crm-frappe-1 bash -lc "cd /home/frappe/frappe-bench && bench --site crm.localhost backup --with-files"
New-Item -ItemType Directory -Force "$HOME\Downloads\frappe-backups"
docker cp "crm-frappe-1:/home/frappe/frappe-bench/sites/crm.localhost/private/backups/." "$HOME\Downloads\frappe-backups"
```

**Không** upload `frappe-backups`, `site_config.json`, `.env`, token, mật khẩu hoặc database thật lên GitHub. Không `docker compose down -v` hay recreate container Frappe đang chứa Bench.

## 5. Cài file seed vào Frappe hiện tại

Các lệnh dưới đây **chạy ở PowerShell**, không phải trong Frappe Console `In [ ]:`:

```powershell
docker cp ".\Web CellphoneS\backend\cellphones_c360\cellphones_c360\snapshot_seed.py" "crm-frappe-1:/home/frappe/frappe-bench/apps/cellphones_c360/cellphones_c360/snapshot_seed.py"
docker cp ".\Web CellphoneS\Docs\CV2-01-05\snapshots\demo-v2" "crm-frappe-1:/tmp/"
docker exec -u root crm-frappe-1 chown frappe:frappe /home/frappe/frappe-bench/apps/cellphones_c360/cellphones_c360/snapshot_seed.py
docker exec -it crm-frappe-1 bash
```

Bên trong Docker:

```bash
cd /home/frappe/frappe-bench
```

File importer chỉ tương thích site đã cài `frappe`, `crm`, `cellphones_c360` cùng patch CV2, có `C360 Customer Intake`, `custom_c360_customer` trên Lead/Deal.

### 5a. Kiểm tra đồng tiền CRM (phải là VND)

Nếu setting CRM chưa là **VND**, importer sẽ báo rõ và không ghi dữ liệu. Kiểm tra trong Frappe Console:

```bash
bench --site crm.localhost console
```

```python
print(frappe.db.get_single_value("FCRM Settings", "currency"))
```

**Chỉ trên site DEMO đã backup và khi cả nhóm thống nhất dùng VND:**

```python
frappe.db.set_single_value("FCRM Settings", "currency", "VND")
frappe.db.commit()
```

Thoát Console bằng `exit()` để trở lại terminal `frappe@...$`. Việc này đổi cấu hình tiền tệ của cả site, **không làm trên môi trường thật**.

### 5b. Dry-run – không ghi dữ liệu

Lưu ý `bench execute --kwargs` dùng cú pháp Python, vì vậy `True` và `False` phải viết hoa:

```bash
bench --site crm.localhost execute cellphones_c360.snapshot_seed.import_demo_v2 --kwargs '{"folder":"/tmp/demo-v2","dry_run":True}'
```

Chỉ tiếp tục nếu trả về `"ok": true`, `"dry_run": true`, `"writes": 0`, không có danh tính trùng với khách hàng trước đó. Đây mới là preflight, không thay thế việc chạy thử trên site.

### 5c. Import thật (CHỈ SAU KHI BACKUP + DRY-RUN PASS)

```bash
bench --site crm.localhost execute cellphones_c360.snapshot_seed.import_demo_v2 --kwargs '{"folder":"/tmp/demo-v2","dry_run":False,"confirm":"IMPORT_SYNTHETIC_DEMO_V2"}'
```

Thao tác này **ghi vào MariaDB** và tạo Custom Field `custom_cv2_snapshot_key` (nếu chưa có) cho Lead, Deal, Order, Ticket, Registration Request để nhận diện lần nhập sau; có thể thêm các giá trị Source tương ứng 6 kênh trong `CRM Lead Source`. Với thay đổi schema, MariaDB có thể tự commit DDL; dù importer cố rollback khi lỗi, **bản sao lưu vẫn là điều bắt buộc**. Nếu lỗi, dừng lại, không chạy lại tùy tiện.

### 5d. Kiểm tra sau import

```bash
bench --site crm.localhost execute cellphones_c360.snapshot_seed.verify_demo_v2 --kwargs '{"folder":"/tmp/demo-v2"}'
bench --site crm.localhost execute cellphones_c360.cv2_audit.audit_schema
bench --site crm.localhost clear-cache
```

Kiểm tra `found` có 144 Intake / 94 Lead / 76 Deal / 62 Order / 45 Ticket / 12 Registration Request. `Customer` được ánh xạ qua 54 Intake đầu tiên, không so sánh ID Frappe với `snapshot_id` logic. Mở `http://localhost:8080` và refresh để xem Dashboard, Leads, Deals, Customers, After-sales, Analytics, Administration.

Rerun `dry_run=True` phải cho số `already_imported` tương ứng; chạy lại `dry_run=False` chỉ khi đã kiểm chứng cơ chế idempotent trên **site test**. Các chỉnh sửa sau khi import không tự đồng bộ giữa máy.

## 6. Đưa code + Snapshot lên GitHub

**Trở về PowerShell** (`exit()` khỏi Console; `exit` khỏi container nếu đang ở Docker). Thực hiện trên branch `feature/khai-cv2-01-05`, không push trực tiếp lên `main`:

```powershell
cd "C:\Users\TRUONG PHAN KHAI\Downloads\CRM\WEB\cellphones-customer360"
git branch --show-current
git status
```

Vì branch của Khải hiện **còn nhiều code CV2 chưa commit**, stage luôn code CV2 + Snapshot mới, nhưng **không** stage Docker kit hay file ZIP cục bộ:

```powershell
git add -- "CV2-MANIFEST.json" "README-CV2-01-05.md" "Web CellphoneS/Docs/CV2-01-05" "Web CellphoneS/backend/cellphones_c360/cellphones_c360" "Web CellphoneS/backend/cellphones_c360/tests"
git diff --cached --check
git diff --cached --stat
git status
```

**Đọc danh sách file đã stage trước khi commit**; chắc chắn không có backup/secret. Sau đó:

```powershell
git commit -m "feat(cv2): add validated demo-v2 seed snapshot and importer"
git push -u origin feature/khai-cv2-01-05
```

Mở repository GitHub của nhóm và tạo **Pull Request: `feature/khai-cv2-01-05` → `main`**. Nhờ Giang kiểm tra backend/schema; Linh kiểm tra Customer 360; Hân kiểm tra Leads/đăng ký. Chỉ merge sau khi ít nhất một máy **import thật và kiểm thử** thành công. Cách push branch rồi tạo PR phù hợp với hướng dẫn GitHub.

## 7. Mỗi thành viên khác dùng Snapshot như thế nào?

1. Sau khi PR được merge, cập nhật code từ `main` bằng Git (không dùng `reset --hard`).
2. Bảo đảm app CV2 và schema đã migrate trên Frappe của máy mình; backup site.
3. Chép `snapshot_seed.py` và `demo-v2/` vào Docker như mục 5; chạy dry-run rồi import.
4. Dùng ID Frappe **của máy mình**, không sao chép `CUST-00006` từ máy Khải vì naming series có thể khác.
5. Tất cả có cùng bộ dữ liệu demo **ban đầu**, nhưng người A sửa/xóa/tạo record trên máy A thì máy B **không tự nhận được**.

## 8. Giới hạn minh chứng

Đã kiểm chứng **offline**: checksum, FK logic, status, tổng Order/Item, trường lost_reason, synthetic email, quan hệ Ticket–Order. **Chưa chạy import trên Docker Frappe thật** trong môi trường tạo file; lệnh dry-run là bước bắt buộc trước khi báo cáo dữ liệu đã được triển khai. Dữ liệu demo không bao gồm User/mật khẩu thực, call log, task, file đính kèm hoặc email gửi ra ngoài. Giá sản phẩm chỉ minh họa, không phải bảng giá thương mại được xác minh.
