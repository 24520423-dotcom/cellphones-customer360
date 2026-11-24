# Task 16 · Bộ dữ liệu trình diễn

## 1. Mục tiêu

Chuẩn bị dữ liệu nhất quán cho SP01–SP04 và minh họa cả tình huống thành công lẫn ngoại lệ.

## 2. Hiện trạng

Ba CSV tạo khách hàng online, offline, xung đột định danh và dòng dữ liệu sai. Các kịch bản giao dịch, chăm sóc và nhân viên được khai báo thành gói demo.

## 3. Phương án triển khai

Site dùng intake và CRM chuẩn để tạo hồ sơ, chuyển Lead, lập đơn và giải quyết Ticket. Mã nguồn, email Lead liên kết, mã sản phẩm demo và chủ đề Ticket là khóa chạy lại. Tài khoản mẫu là System User vô hiệu hóa, dùng miền `example.test`.

## 4. Các file liên quan

- Windows: `data/demo-workflows.json`, `data/customers_*.csv`, `backend/cellphones_c360/cellphones_c360/demo.py`.
- Windows: `deployment/cellphones-c360/import-demo.ps1`.
- Docker: site `crm.localhost`, Custom App được bind mount vào Bench.

## 5. Các bước thực hiện

Từ repo gốc, chạy `.\deployment\cellphones-c360\import-demo.ps1` để thử, chạy lại và rollback. Trên site demo đã được chọn, `-Apply` ghi bộ demo. Dùng User trong Desk để kích hoạt tài khoản mẫu cần trình diễn và gán đúng phạm vi.

## 6. Luồng nghiệp vụ

Quản trị → nhập nguồn → xác nhận kết quả → tạo các thực thể của kịch bản → chạy lại để kiểm tra cùng mã → rollback trial hoặc lưu bộ demo theo tùy chọn.

| Dữ liệu | Cách trình diễn |
| --- | --- |
| WEB-DEMO-001 | Nguồn Website và Store, hai Deal Won, một lần Delivery, một lần Pickup trả góp, một bảo hành Closed, một yêu cầu mở và Care Task |
| POS-DEMO-001 | COD giao thất bại và hủy, một đơn Draft, một khiếu nại |
| ZALO-DEMO-001 | Ongoing, Lost có lý do và Lead chưa chuyển đổi |
| Dữ liệu trùng | Cùng định danh, dùng chung số, trùng tên và một dòng lỗi |

## 7. Kiểm thử

Đã chạy gói demo và lặp lại trên MariaDB trong một giao dịch. Kết quả nguồn lần đầu gồm 8 Created, 2 Linked, 1 Needs Review và 1 Invalid. Lần hai trả lại cùng mã kết quả nghiệp vụ. Ở quyền hiện hành, hai vai trò Sales User và Sales Manager đã có. Ba vai trò phòng ban đang chờ cấu hình mới.

## 8. Output bàn giao

CSV, JSON workflow, trình nhập có trial/commit theo lựa chọn, nhân viên mẫu và hướng dẫn trình diễn.

## 9. Tiêu chí hoàn thành

Dữ liệu demo có thể tái tạo, không trùng khi chạy lại và các yêu cầu bảo hành cần đơn đã bàn giao. Vai trò phòng ban được xác nhận khi Task 13 áp dụng.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `test: add replayable Customer 360 demo data`.
