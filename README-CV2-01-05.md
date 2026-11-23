# BỔ SUNG MỚI – Phương án snapshot dữ liệu demo dùng chung qua GitHub

**Bản cập nhật 2026-11-23.** Đọc trước: `Web CellphoneS/Docs/CV2-01-05/CV2-00-KE-HOACH-SNAPSHOT.md` và `CV2-02-SNAPSHOT-GUIDE.md`. Bộ patch giữ lại toàn bộ code CV2-01 đến CV2-05 từ bản trước, chỉ **bổ sung** quy trình/manifest/CSV demo/validator offline. Các CSV mới **chưa phải bộ import Frappe tự động**. Không đưa database dump hay dữ liệu khách hàng thật lên GitHub.

Dữ liệu demo ở `snapshots/demo-v1` có 3 Customer, 3 Lead, 3 Deal, 2 Order, 2 Order Item, 2 Ticket, 4 lượt Intake; đã chuẩn hóa ID logic để tham chiếu, tách biệt với Frappe document name. Validator chạy offline:

```powershell
python '.\Web CellphoneS\Docs\CV2-01-05\validate_snapshot.py' '.\Web CellphoneS\Docs\CV2-01-05\snapshots\demo-v1'
```

**Hiện trạng máy Khải:** Code CV2 đã được giải nén trên `feature/khai-cv2-01-05`; chưa xác nhận migrate/nhập dữ liệu thật trên Docker. Có thể chỉ chép thêm các file tài liệu/dữ liệu từ gói này, không cần cài lại CRM hay tạo lại site.

---

# Giai đoạn 2 – CV2-01 đến CV2-05 (CellphoneS Customer 360)

**Nguồn:** bản ZIP `cellphones-customer360-latest.zip` do Khải cung cấp, tương ứng `origin/main` commit `51c5c54` ở thời điểm trích xuất. Chưa có quyền thực thi trên Docker/Frappe máy của người dùng.

## Những gì có trong bản bàn giao

| Task | Deliverable | Trạng thái thực tế |
| --- | --- | --- |
| CV2-01 | `Docs/CV2-01-05/CV2-01-Data-Dictionary.md`, ERD; `cv2_audit.py` kiểm tra metadata/tham chiếu trên site | Nguồn JSON được kiểm; metadata CRM trên site chưa chạy |
| CV2-02 | CSV 12 dòng, `api/intake.py` import API/CLI, khóa nguồn chống nhập lại | Dữ liệu mẫu được tạo; **chưa import vào DB** |
| CV2-03 | `cv2_utils.py` normalize/validate/match, Intake DocType + quy trình review, offline tests | 10 unit tests offline PASS; chưa test API với Frappe thật |
| CV2-04 | `CRM Lead.custom_c360_customer`, `CRM Deal.custom_c360_customer`, validator liên kết; kiểm thử quan hệ | Code đã làm; cần migrate, kiểm thử trên site |
| CV2-05 | Sửa `get_customer_360`, `get_customer_profile`, `get_customer_timeline` để có nhiều Lead/Deal và nguồn intake | Code đã làm; chưa kiểm thử HTTP thực tế |

**Quan trọng:** Kết quả thử nghiệm trên Frappe thật không được giả lập thành kết quả Pass. Các mốc chưa thực hiện được đánh dấu *chưa chạy*, cần máy Khải để xác nhận. Không tự đổi cấu hình React/Docker và không can thiệp database cho đến khi triển khai có backup.

## A. Áp dụng code vào repository trên Windows

1. Đảm bảo `git status` không có thay đổi chưa commit ở những file liên quan. Nên dùng branch riêng:

```powershell
cd 'C:\Users\TRUONG PHAN KHAI\Downloads\CRM\WEB\cellphones-customer360'
git status
git switch -c feature/khai-cv2-01-05
```

2. Giải nén file `CV2-01-05-CellphoneS-patch.zip` (tên file thực tế có thể là `CV2-01-05-CellphoneS-patch.zip`) vào root repository này, **sau khi kiểm tra không có file mới của người khác bị ghi đè**. Các đường dẫn trong ZIP giữ nguyên `Web CellphoneS/...`.

3. Xem thay đổi:

```powershell
git status
git diff -- 'Web CellphoneS/backend/cellphones_c360'
```

## B. Sao lưu database + mã nguồn trước khi migrate

Frappe khởi chạy trong container **hiện có** `crm-frappe-1`, site `crm.localhost`, không tạo lại container.

```powershell
docker exec -it crm-frappe-1 bash
```

Bên trong Docker:

```bash
cd /home/frappe/frappe-bench
bench --site crm.localhost backup --with-files
exit
```

Sau đó về PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\Downloads\frappe-backups"
docker cp 'crm-frappe-1:/home/frappe/frappe-bench/sites/crm.localhost/private/backups/.' "$HOME\Downloads\frappe-backups"
```

Sao lưu riêng ZIP/git branch source nếu cần. **Không chạy** `docker compose down -v`, `docker compose up --force-recreate`, `bench new-site`, `bench reinstall` hoặc `bench install-app` lại.

## C. Cập nhật app đã cài (KHÔNG `bench get-app` lại)

Từ root repository trên Windows:

```powershell
docker cp '.\Web CellphoneS\backend\cellphones_c360\cellphones_c360\.' 'crm-frappe-1:/home/frappe/frappe-bench/apps/cellphones_c360/cellphones_c360/'
docker exec -u root crm-frappe-1 chown -R frappe:frappe /home/frappe/frappe-bench/apps/cellphones_c360/cellphones_c360
docker exec -it crm-frappe-1 bash
```

Trong Docker:

```bash
cd /home/frappe/frappe-bench
bench --site crm.localhost migrate
bench --site crm.localhost clear-cache
bench --site crm.localhost execute cellphones_c360.cv2_audit.audit_schema
```

Nếu `migrate` báo lỗi, **dừng và lấy traceback**, không tự xoá DocType hay thêm patch SQL thủ công.

Thoát container (`exit`), rồi khởi động lại container cũ:

```powershell
docker restart crm-frappe-1
```

Đây là container `crm-frappe-1` đã có Bench và site. Không recreate.

## D. Chạy unit tests offline và test dữ liệu

Trên Windows tại thư mục backend:

```powershell
cd '.\Web CellphoneS\backend\cellphones_c360'
python -m unittest discover -s tests -p 'test_cv2_utils.py' -v
```

Trở về root repo bằng `cd ..\..\..` (hoặc mở PowerShell mới tại root repository), sao chép CSV rồi chạy preview/ingest theo `Docs/CV2-01-05/CV2-02-03-Import-Dedupe.md`.

**Quan trọng:** dữ liệu của các máy khác nhau, hãy test trước trên site riêng (`crm.localhost` của Khải) và database có backup. Không gửi trực tiếp database/Frappe chứa dữ liệu khách hàng thật cho người khác.

## E. Giao diện và xác nhận

- Docker web hiện có vẫn ở `http://localhost:8080`.
- CRM Lead từ UI có thể chưa tự điền `custom_c360_customer`; cần chọn link bằng Frappe Desk hoặc xây giao diện ở CV2-06.
- Trên Customer Profile, chọn một Customer được gắn với >=2 Lead rồi xác nhận các tab Lead/Deal, Order, Hậu mãi, Tương tác.
- Dùng `CV2-04-05-Testcases-API.md` ghi kết quả Pass/Fail; chỉ báo hoàn tất cuối cùng sau khi các bài test Frappe thật đạt.

## Cảnh báo version/GitHub

Bản bàn giao dựa trên commit `51c5c54`. Nếu trong lúc làm việc Giang/Hân/Linh đã push thêm, **so sánh `git diff` và merge thay đổi**, không ghi đè trực tiếp code mới của bạn bằng snapshot này. Tuỳ chọn tốt hơn là tạo branch riêng, commit rồi gửi PR để nhóm review.
