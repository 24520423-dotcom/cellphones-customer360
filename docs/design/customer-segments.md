# Task 11 · Phân khúc Customer 360

## 1. Mục tiêu

Hỗ trợ SP02 và SP04 theo dõi vòng đời khách hàng, nhu cầu mua lại và hồ sơ cần chăm sóc.

## 2. Hiện trạng

Hồ sơ có loại và trạng thái do nhân viên gán. Đơn hàng đã phân biệt trạng thái bàn giao và thanh toán.

## 3. Phương án triển khai

Phân khúc được tính theo tài liệu đọc được và có thể cùng xuất hiện trên một khách hàng.

| Phân khúc | Điều kiện |
| --- | --- |
| New | Tạo hồ sơ dưới 30 ngày trước ngày đo |
| Existing | Tạo hồ sơ từ 30 ngày trở lên |
| Returning | Có từ 2 đơn xác nhận chi tiêu |
| High Value | Chi tiêu xác nhận tích lũy từ 20.000.000 VND |
| Inactive | Từ 180 ngày kể từ giao dịch xác nhận gần nhất, hoặc từ lúc tạo hồ sơ nếu chưa mua |
| Online | Website, App, Facebook, Zalo, Hotline |
| Offline | Store |
| Open Support | Có Ticket Open, Pending hoặc In Progress trong quyền đọc |

RFM dùng đơn Completed, Paid và có ngày thanh toán. Recency là ngày từ lần thanh toán đủ điều kiện gần nhất. Frequency là số đơn đủ điều kiện. Monetary là tổng giá trị các đơn đó. Ngưỡng là quy tắc demo đã thống nhất trong mã. Sản phẩm đã mua được hiển thị trong Orders. Nhóm quan tâm cần sự kiện lựa chọn sản phẩm từ nguồn Lead/Deal đủ dữ liệu để tính.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/segments.py`, `api/customer360.py` và `cellphones_customer_360/doctype/c360_customer/test_segments.py`.
- Docker: hai trang Customer 360 trong `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/`.

## 5. Các bước thực hiện

Build CRM bằng `bench build --app crm`. Chọn phân khúc trên danh sách và tìm kiếm. Mở Overview để xem nhãn và RFM. Công thức chạy trên dữ liệu hiện có, dùng quyền đọc đơn và Ticket của người dùng.

## 6. Luồng nghiệp vụ

Nhân viên → mở danh sách hoặc hồ sơ → hệ thống truy xuất giao dịch trong quyền → tính nhãn và RFM → hiển thị kết quả hoặc trạng thái rỗng khi không có hồ sơ khớp.

## 7. Kiểm thử

Đã kiểm tra RFM với hai lần mua, một Draft, một đơn hủy/refund. Tần suất là 2, chi tiêu 21.000.000 VND, độ gần 6 ngày. Đã kiểm tra Offline qua API danh sách, không có Returning khi khách chưa mua, và dữ liệu đơn chưa đọc được trả RFM trống.

Chrome đã hiển thị nhãn và RFM trên hồ sơ mới, chọn Offline bằng bàn phím và lọc đúng khách hàng thử. [Nhãn và RFM trên hồ sơ](../../screenshots/task11-customer-segments.png).

## 8. Output bàn giao

Quy tắc phân khúc, bộ lọc, nhãn Overview, RFM và kiểm thử.

## 9. Tiêu chí hoàn thành

Hồ sơ hiển thị đúng phân khúc, danh sách lọc theo nhãn và các chỉ số trả theo quyền.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: calculate and filter customer segments`. Analytics dùng lại công thức này khi tổng hợp cấp quản lý.
