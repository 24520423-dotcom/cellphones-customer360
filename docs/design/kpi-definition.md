# Task 12 · Customer Analytics

## 1. Mục tiêu

Theo dõi kết quả SP01–SP04 theo kỳ bằng dữ liệu MariaDB và quyền của tài khoản quản lý.

## 2. Hiện trạng

Dashboard chuẩn CRM và API Analytics có truy vấn Lead, Deal, giao dịch và hậu mãi. Trang Customer Analytics nối các nhóm KPI xuyên suốt Customer 360 và dùng lại thư viện biểu đồ của Dashboard.

## 3. Phương án triển khai

| KPI | Kỳ và công thức |
| --- | --- |
| Tổng khách hàng | Hồ sơ chưa hợp nhất có ngày tạo trước hoặc trong ngày kết thúc |
| Khách hàng mới, nguồn và kênh | Hồ sơ tạo trong kỳ. Kênh Online gồm Website/App/Facebook/Zalo/Hotline, cửa hàng là Offline |
| Khách quay lại và phân khúc | RFM tích lũy tới ngày kết thúc, dựa trên đơn đủ điều kiện trong quyền đọc |
| Ứng viên trùng | Số hồ sơ active có trùng điện thoại hoặc email đã lưu trong phạm vi nhìn thấy |
| Chờ xác minh | Số bản ghi nguồn Needs Review tiếp nhận trong kỳ và đọc được |
| Lead, Deal và pipeline | Lead/Deal tạo trong kỳ. Pipeline dự kiến cộng các Deal ở trạng thái mở có giá trị VND xác định |
| Lead Conversion Rate | Số Lead tạo trong kỳ có ít nhất một Deal tạo trong cùng kỳ chia số Lead tạo trong kỳ |
| Deal Win Rate | Deal Won chia tổng Won + Lost, theo cohort Deal tạo trong kỳ |
| Tổng đơn, hoàn tất, hủy | Đếm theo order_date trong kỳ và trạng thái hiện tại |
| Giá trị đơn hợp lệ | Tổng đơn Confirmed, Processing hoặc Completed theo order_date trong kỳ |
| Tiền thu xác nhận | Tổng đơn Completed, Paid có paid_at trong kỳ. Đây là chỉ số theo dõi nghiệp vụ trong phạm vi đồ án |
| Ticket và tồn đọng | Ticket lập trong kỳ. Backlog gồm Open/Pending/In Progress tại lúc đọc |
| Tỷ lệ xử lý | Ticket Resolved hoặc Closed trong cohort chia tổng Ticket tạo trong kỳ |
| Thời gian xử lý trung bình | Trung bình resolved_date trừ created_date của Ticket Resolved/Closed có đủ hai mốc hợp lệ |

Đếm trả 0 khi phạm vi có quyền chỉ gồm tập rỗng. Tỷ lệ có mẫu số 0 và chỉ số không đủ quyền hoặc dữ liệu trả giá trị trống. Tiền dự kiến từ Deal và số tiền đã thu có thẻ riêng.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/analytics.py`, `api/segments.py` và `cellphones_customer_360/doctype/c360_customer/test_analytics.py`.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/CustomerAnalytics.vue` và sidebar/router trong repo CRM.

## 5. Các bước thực hiện

Chạy `bench build --app crm`. Mở **Customer Analytics**, chọn kỳ mặc định hoặc nhập ngày đầu và cuối. Ngày cuối là bao gồm toàn bộ ngày đó trong múi giờ site.

## 6. Luồng nghiệp vụ

Quản lý → chọn kỳ → API xác định ranh giới thời gian và quyền → tổng hợp KPI, không có đủ dữ liệu thì để trống → giao diện hiển thị thẻ và biểu đồ.

## 7. Kiểm thử

MariaDB xác nhận kỳ rỗng, giá trị 0, mẫu số 0, thứ tự ngày sai, quyền Guest và cách chỉ cộng khoản thu từ đơn hoàn tất đã thanh toán. Đơn nháp còn lại vẫn xuất hiện trong tổng số đơn và không tăng tiền thu.

Chrome đã hiển thị các thẻ KPI và biểu đồ Frappe từ dữ liệu site và tải lại khi áp dụng kỳ. [Customer Analytics trên CRM](../../screenshots/task12-customer-analytics.png).

## 8. Output bàn giao

Trang Customer Analytics, bộ lọc tùy chọn kỳ, KPI và biểu đồ Frappe, tài liệu công thức và kiểm thử.

## 9. Tiêu chí hoàn thành

Chỉ số phản ánh dữ liệu thực trong quyền đọc, áp dụng đúng ngày đo, có hành vi rõ cho tập rỗng và mẫu số 0.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: add permission-aware Customer Analytics dashboard`. Kiểm thử vai trò tiếp theo đối chiếu giới hạn theo hồ sơ và trường.
