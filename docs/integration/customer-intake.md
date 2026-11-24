# Task 05 · Tiếp nhận khách hàng đa kênh

## 1. Mục tiêu

SP01 tiếp nhận cùng một định dạng dữ liệu từ nguồn trực tuyến và tại cửa hàng, tạo hồ sơ hoặc chuyển xung đột định danh cho nhân viên xác minh.

## 2. Hiện trạng

Frappe có Data Import để nhập DocType và CRM Lead Source để ghi nguồn Lead. C360 Customer có Source Channel. Import trực tiếp Customer chưa lưu mã hồ sơ nguồn, tình trạng xử lý hoặc thông tin lần tiếp nhận tiếp theo.

## 3. Phương án triển khai

CSV và API JSON dùng chung controller tạo Customer. `C360 Source Record` giữ từng sự kiện nhận, kết quả và kiểm tra replay bằng khóa sinh từ kênh và mã nguồn. Nguồn website, ứng dụng, mạng xã hội và POS trong bộ demo đều giả lập.

| Cột | Mapping |
| --- | --- |
| `source_channel` | Giá trị chuẩn từ C360 Customer. Lưu trên sự kiện và trên khách hàng khi tạo mới |
| `source_record_id` | Mã bản ghi gốc bắt buộc. Dùng cùng source_channel để chống trùng khi gửi lại |
| `received_at` | Ngày giờ ISO 8601. Nếu có múi giờ, quy đổi sang giờ hệ thống. Nếu trống, dùng thời điểm server nhận |
| `customer_name`, `phone_number`, `email` | Chuẩn hóa theo [quy tắc dữ liệu](../design/customer-data-quality.md) |
| `customer_type` | Giá trị metadata C360 Customer. Mặc định Individual |
| `purchase_interest` | `0` hoặc `1`. Lưu trên sự kiện để nhân viên tiếp tục xử lý nhu cầu trong CRM |

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/intake.py` và `cellphones_customer_360/doctype/c360_source_record/` trong cùng package.
- Docker: `/home/frappe/frappe-bench/apps/cellphones_c360` sử dụng cùng Custom App.
- Windows: `data/customers_online.csv`, `data/customers_offline.csv`, `data/customers_duplicates.csv`.

## 5. Các bước thực hiện

1. Sao lưu site hiện tại. Nạp DocType bằng `bench --site crm.localhost reload-doc cellphones_customer_360 doctype c360_source_record` trong Bench. Lần cài mới nhận DocType qua cài Custom App.
2. Gửi object JSON `{"csv_text":"<nội dung CSV UTF-8>"}` đến `POST /api/method/cellphones_c360.api.intake.process_csv` qua phiên Frappe cùng site và header `X-Frappe-CSRF-Token`. Để nhận từ ứng dụng tích hợp, gửi `{"rows":[{...}]}` đến `process_records`. Một lần gửi tối đa 100 dòng.
3. Trong Desk, tìm **C360 Source Record** và kiểm tra kết quả từng mã nguồn. Với **Needs Review**, so khớp hồ sơ theo quyền và gửi `source_document`, `customer`, `reason` đến `POST /api/method/cellphones_c360.api.intake.resolve_record` sau khi xác minh.

## 6. Luồng nghiệp vụ

Nhân viên → gửi lô nguồn → xác thực quyền, mã nguồn và trường bắt buộc → chuẩn hóa → tạo mới hoặc liên kết khi bản ghi có duy nhất một hồ sơ đọc được và trùng cả tên, điện thoại, email → lưu kết quả. Xung đột một định danh được đưa vào **Needs Review**. Dòng lỗi có mã nguồn hợp lệ được lưu ở **Invalid**, các dòng còn lại vẫn xử lý. Gửi lại cùng kênh và mã trả kết quả đã lưu với `replay: true`. Một sự kiện sửa dữ liệu từ nguồn cần mã sự kiện mới của nguồn đó.

## 7. Kiểm thử

Ba bài kiểm thử trên MariaDB hiện có đi qua tạo, gửi lại, liên kết đa kênh, xác minh thủ công, CSV có BOM, sai header, thiếu khóa, điện thoại sai và từ chối Guest. Dữ liệu kiểm thử tự động được rollback.

Ba tệp CSV bàn giao cũng đã chạy theo thứ tự trong một giao dịch. Online trả 5 Created. Offline trả 2 Created và 1 Linked. Tệp đối chiếu trả 1 Linked, 1 Needs Review, 1 Created và 1 Invalid. Gửi lại từng tệp đều trả `replay: true`. Lô kiểm thử được rollback.

## 8. Output bàn giao

API JSON/CSV, DocType nhật ký nguồn, API xác minh, CSV giả lập và kiểm thử.

## 9. Tiêu chí hoàn thành

Nguồn có mã ổn định trả cùng kết quả khi gửi lại. Khi gặp xung đột, nhân viên có thể xác minh trước khi gắn nguồn vào hồ sơ. Kết quả và lý do được giữ để đối chiếu.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: import and reconcile multichannel customer intake`. Bước tiếp theo xử lý hai hồ sơ khách hàng đã tồn tại và cần hợp nhất.
