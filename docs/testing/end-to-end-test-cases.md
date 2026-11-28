# Task 15 · Kiểm thử quy trình tổng thể

## 1. Mục tiêu

Đối chiếu các đường nghiệp vụ SP01–SP04 từ nhận diện đến giao dịch, giao nhận, hỗ trợ và mua lại.

## 2. Hiện trạng

Các bài kiểm thử đã chạy trên Bench và MariaDB của `crm.localhost`. Khi kiểm thử Chrome, phiên dùng tài khoản giả lập được thu hồi sau thao tác. Cấu hình vai trò phòng ban đang chờ migration được duyệt.

## 3. Phương án triển khai

Chạy bộ demo liên kết dữ liệu thật trong transaction kiểm thử, kiểm tra hành vi ORM và kiểm tra giao diện trên Chrome. Dùng savepoint để kiểm chứng nhánh lỗi giữa giao dịch hợp nhất.

## 4. Các file liên quan

- Windows: `data/demo-workflows.json`, ba CSV nguồn và `deployment/cellphones-c360/import-demo.ps1`.
- Windows: `backend/cellphones_c360/cellphones_c360/cellphones_customer_360/doctype/` có các bài kiểm thử tích hợp.
- Docker: site `crm.localhost` và source CRM dưới Bench hiện có.

## 5. Các bước thực hiện

Chạy trial import bằng PowerShell từ repo gốc. Kiểm tra mã và trạng thái trả về, rồi cho lệnh chạy lại trong cùng giao dịch. Khi kiểm thử bằng trình duyệt, dùng tài khoản thử được cấp quyền và thực hiện từng thao tác trong bảng. Chạy bộ test theo module áp dụng trong Bench.

## 6. Luồng nghiệp vụ

QA → chọn kịch bản và dữ liệu giả lập → chạy qua quyền và gateway tương ứng → so sánh kết quả API, UI và MariaDB → lưu minh chứng. Trường hợp vai trò chưa áp dụng được theo dõi trong bảng quyền.

## 7. Kiểm thử

| Test ID | Nghiệp vụ | Điều kiện đầu vào | Các bước | Kết quả mong đợi | Kết quả thực tế | Pass/Fail | Minh chứng |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E2E-01 | Online mới mua thành công | WEB-DEMO-001 từ Website | Import, tạo Lead, chuyển Deal Won, xác nhận đơn, thanh toán, giao tận nơi | Một hồ sơ, liên kết xuyên suốt và đơn Delivered/Completed/Paid | Kết quả được đọc lại qua Customer 360 và Timeline | Pass | [Bộ demo](demo-scenario.md), [màn hình đơn](../../screenshots/task08-order-detail.png) |
| E2E-02 | Khách offline đã tồn tại | Khách có dữ liệu Website và Store cùng định danh | Import offline, gửi lại, xử lý nguồn xung đột và đối chiếu | Liên kết bản ghi Store, ghi Needs Review với số dùng chung, không tạo lặp | CSV cho 1 Linked trong bộ offline. Đã chạy resolve và màn hình merge | Pass | [Kết quả CSV](../integration/customer-intake.md), [đối chiếu](../../screenshots/task06-review-duplicate.png) |
| E2E-03 | Mua lại trên hồ sơ cũ | WEB-DEMO-001 có đơn đầu đã giao | Tạo Lead và Deal tiếp, thêm đơn Pickup, đánh dấu Paid/Completed | Cùng khách có 2 cơ hội và 2 giao dịch xác nhận | RFM Frequency 2 và Monetary 23.000.000 VND, hồ sơ có hai Deal | Pass | [Luồng CRM](../integration/crm-sales-links.md), [bộ demo](demo-scenario.md) |
| E2E-04 | Cân nhắc hoặc từ chối | ZALO-DEMO-001 | Tạo hai cơ hội, giữ Ongoing hoặc chuyển Lost với lý do | Kết quả vẫn thuộc cùng khách, giữ trạng thái pipeline gốc | Seed kiểm tra Deal Ongoing/Lost và một Lead chưa chuyển đổi | Pass | [Dữ liệu luồng](../../data/demo-workflows.json) |
| E2E-05 | Giao thất bại hoặc hủy | POS-DEMO-001 COD giao tận nơi | Confirmed → Processing → In Transit → Cancelled/Failed | Đơn giữ kết quả lỗi, không tăng tiền thu | MariaDB lưu Failed, Cancelled, Unpaid. KPI loại khỏi doanh số xác nhận | Pass | [Kiểm thử Orders](../integration/customer-orders.md), [KPI](../design/kpi-definition.md) |
| E2E-06 | Bảo hành | Đơn Completed có hoạt động bàn giao | Tạo Ticket Warranty, phân công, ghi giải pháp, đóng, kiểm tra Task chăm sóc | Đúng đơn, có giải pháp, lịch tạo một lần | Ticket Closed. DB xác nhận từ chối đơn sai/chưa hoàn tất và một Care Task sau ba ngày | Pass | [Kiểm thử hậu mãi](../integration/after-sales.md) |
| E2E-07 | Nhân viên ngoài phạm vi | Sales User thử nghiệm theo cấu hình quyền hiện hành | Mở URL hồ sơ trực tiếp, gọi API đọc và tạo | Từ chối trên UI và API | Chrome báo không tải được hồ sơ, API đọc và ghi trả HTTP 403. Ma trận vai trò mới chờ Task 13 | Pass theo quyền hiện hành | [Ảnh từ chối](../../screenshots/task15-direct-access-denied.png), [ma trận](../design/permission-matrix.md) |
| E2E-08 | Khách có nhiều thực thể | Hồ sơ WEB-DEMO-001 | Đọc 5 tab và Timeline sau tạo nhiều Lead/Deal/Order/Ticket | Các quan hệ và chỉ số cùng mã khách | Hai Deal, hai đơn, hai Ticket và các sự kiện từ đúng tài liệu đã được kiểm tra | Pass | [Timeline](../../screenshots/task10-customer-timeline.png), [bộ demo](demo-scenario.md) |
| E2E-09 | Hợp nhất thất bại | Hai hồ sơ giả lập, đơn và Ticket | Chèn lỗi khi chuyển Ticket sau ghi đơn, đọc lại DB | Hoàn tác hồ sơ, đơn và quan hệ | Bản ghi sau rollback khớp trạng thái trước hợp nhất | Pass | [Bảng kiểm thử merge](../design/customer-merge.md) |

## 8. Output bàn giao

Bảng liên kết BPMN, chín ca E2E và minh chứng môi trường.

## 9. Tiêu chí hoàn thành

Các nhánh nghiệp vụ được kiểm tra trên site hiện tại. Kiểm thử vai trò mới và áp dụng phân quyền cuối cùng được theo dõi tại Task 13.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `test: record end-to-end CRM workflow evidence`.
