# Task 06 · Hợp nhất hồ sơ khách hàng

## 1. Mục tiêu

Hoàn tất SP01 khi nhân viên đã xác minh hai hồ sơ hiện có thuộc cùng một khách hàng. Giữ mã Golden Record và lịch sử giao dịch.

## 2. Hiện trạng

Candidate API đối chiếu tên, số điện thoại và email theo quyền. C360 Customer có liên kết Contact và Lead chính. Đơn hàng, Ticket và nhật ký nguồn tham chiếu C360 Customer.

## 3. Phương án triển khai

Mở hồ sơ được chọn làm Golden Record và đối chiếu một hồ sơ nguồn. Mặc định giữ giá trị đầy đủ trên Golden Record, dùng giá trị nguồn khi đích trống. Người xác minh chọn theo thông tin đã kiểm chứng, thời điểm cập nhật và mức độ đầy đủ. Trùng tên chỉ gợi ý kiểm tra.

Custom App tái sử dụng bảng con `Dynamic Link` để lưu các liên kết Contact, CRM Lead và CRM Deal bổ sung. Hợp nhất khóa hồ sơ, kiểm tra phiên bản và quyền, chuyển đơn hàng trước Ticket tương ứng, rồi chuyển nhật ký nguồn. Hồ sơ nguồn giữ mã cũ và ghi hồ sơ đích, người thực hiện, ngày giờ, lý do. Savepoint rollback toàn bộ thay đổi khi một bản ghi phụ thuộc lỗi.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/merge.py` và `api/customer360.py` trong cùng package.
- Windows: `backend/cellphones_c360/cellphones_c360/cellphones_customer_360/doctype/` chứa metadata Customer, controller Customer/Order/Ticket và `c360_customer/test_merge.py`.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/components/Customer360/DuplicateReview.vue` và `frontend/src/pages/Customer360Detail.vue` trong cùng repo.

## 5. Các bước thực hiện

1. Sao lưu site. Nạp metadata C360 Customer bằng `bench --site crm.localhost reload-doc cellphones_customer_360 doctype c360_customer`. Bước này thêm các trường lưu trữ hợp nhất và bảng con liên kết.
2. Chạy `bench build --app crm` trong Bench để cập nhật giao diện.
3. Mở hồ sơ cần giữ, chọn **Review Duplicate** và chọn hồ sơ so sánh. Xác minh danh tính, chọn dữ liệu giữ lại, nhập lý do và chọn **Merge Customer**.
4. Kiểm tra đơn hàng, Ticket, bản ghi nguồn và liên kết CRM của hồ sơ đích. Mở hồ sơ cũ theo URL để xem liên kết đến hồ sơ hiện hành.

## 6. Luồng nghiệp vụ

Nhân viên → mở hồ sơ đích → đối chiếu ứng viên → xác minh → người có quyền chọn giá trị và xác nhận → khóa, kiểm tra và chuyển dữ liệu → lưu Golden Record và lưu trữ hồ sơ nguồn. Sự cố khi chuyển bản ghi làm rollback giao dịch. Hồ sơ thay đổi sau lúc đối chiếu yêu cầu tải lại dữ liệu.

## 7. Kiểm thử

| Test ID | Nghiệp vụ | Điều kiện đầu vào | Các bước | Kết quả mong đợi | Kết quả thực tế | Pass/Fail | Minh chứng |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MG-01 | Hợp nhất | Hai hồ sơ giả lập, Contact, đơn, Ticket, nguồn | Đối chiếu và hợp nhất | Chuyển các liên kết, giữ đơn gốc và lưu hồ sơ nguồn | Đã xác nhận các bản ghi và audit trên MariaDB | Pass | `test_moves_related_documents_and_retains_archived_source` |
| MG-02 | Rollback | Cố tình phát sinh lỗi khi chuyển Ticket sau khi đã chuyển đơn | Gọi hợp nhất và đọc lại từng bản ghi | Hồ sơ và đơn, Ticket giữ nguyên trạng thái ban đầu | Kiểm tra DB sau rollback đều khớp | Pass | `test_rolls_back_partially_moved_documents` |
| MG-03 | Quyền và xác minh | Guest hoặc chưa tích xác minh | Gọi hợp nhất | Từ chối | PermissionError hoặc ValidationError tương ứng | Pass | `test_requires_explicit_verification_and_merge_role` |
| MG-04 | Đối chiếu trên Vue | Hai hồ sơ giả lập có cùng tên, tài khoản System Manager thử nghiệm | Chọn ứng viên, xác minh, hợp nhất rồi mở route hồ sơ cũ | Hộp thoại đóng sau khi lưu. Hồ sơ cũ dẫn đến Golden Record | Đã xác nhận trên Chrome, đã thu hồi phiên và dọn hai hồ sơ kiểm thử | Pass | [Đối chiếu](../../screenshots/task06-review-duplicate.png), [Hồ sơ lưu trữ](../../screenshots/task06-customer-archived.png) |

## 8. Output bàn giao

Đối chiếu hai hồ sơ, hợp nhất theo quyền, lưu trữ nguồn và nhật ký truy vết, kiểm thử giao dịch.

## 9. Tiêu chí hoàn thành

Cả quyền đọc, quyền ghi và phiên bản của hai hồ sơ được kiểm tra. Các thực thể giao dịch đi theo Golden Record trong một giao dịch. Kiểm thử gồm luồng thành công, quyền và rollback sau ghi một phần.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: merge verified Customer 360 profiles transactionally`. Bước tiếp theo đưa các liên kết CRM bổ sung vào tab Leads & Deals.
