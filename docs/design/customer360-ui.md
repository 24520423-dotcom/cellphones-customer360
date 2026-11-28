# Task 14 · Giao diện CellphoneS

## 1. Mục tiêu

Giúp nhân viên hoàn tất SP01–SP04 trên màn hình máy tính, di động hoặc khi dùng bàn phím.

## 2. Hiện trạng

CRM đã dùng logo, favicon và sắc đỏ CellphoneS. Các màn hình Customer 360, Orders, After-sales và Analytics dùng Frappe UI. Hồ sơ trước đây có ít chỉ dẫn focus và tab ở chiều rộng nhỏ.

## 3. Phương án triển khai

Giữ màu chủ đạo `#D70018` và dùng token Frappe cho bề mặt, đường viền và chữ. Phạm vi CSS mới áp dụng trong trang Customer 360. Trạng thái có badge theo màu và nhãn văn bản. Ngày giờ hiển thị theo Việt Nam, tiền theo VND. Chuỗi giao diện đi qua cơ chế dịch CRM.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/translations/vi.csv` và `api/customer360.py` trong cùng package.
- Docker: `apps/crm/frontend/src/cellphones-theme.css`, các trang Customer 360/Analytics và `src/components/Customer360` trong Bench.

## 5. Các bước thực hiện

Chạy `bench build --app crm`. Trong hồ sơ, dùng Tab để đến nhóm tab rồi dùng Arrow Left/Right, Home hoặc End để chọn nội dung. Form, bảng, badge và timeline dùng cùng bộ định dạng. Tài khoản có thể chọn ngôn ngữ trong thiết lập người dùng Frappe.

## 6. Luồng nghiệp vụ

Nhân viên → mở hồ sơ → chọn tab bằng chuột hoặc bàn phím → vùng nội dung hiển thị theo tab đang chọn. Bảng dài có vùng cuộn cục bộ và bố cục hồ sơ co theo màn hình.

## 7. Kiểm thử

Chrome đã chuyển đến Timeline bằng phím End và xác nhận focus ở tab mới. Ở viewport 390 × 844, document không cuộn ngang. [Trước](../../screenshots/task10-customer-timeline.png), [sau trên máy tính](../../screenshots/task14-profile-desktop.png), [sau trên di động](../../screenshots/task14-profile-mobile.png).

Frappe đã đọc chuỗi tiếng Việt từ Custom App trên site hiện có.

## 8. Output bàn giao

CSS trong phạm vi Customer 360, bố cục responsive, hỗ trợ bàn phím, badge, dịch tiếng Việt và ảnh minh chứng.

## 9. Tiêu chí hoàn thành

Năm tab truy cập được, focus theo lựa chọn, các trang nội bộ dùng cùng định dạng tiền/ngày và màu nhận diện.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `style: refine and localize the CellphoneS CRM workspace`.
