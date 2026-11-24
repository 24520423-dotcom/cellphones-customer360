# Task 10 · Hồ sơ Customer 360 và Timeline

## 1. Mục tiêu

Tra cứu SP01–SP04 trên cùng hồ sơ, theo quyền từng loại dữ liệu.

## 2. Hiện trạng

Hồ sơ có năm tab và Timeline phân trang. Các phần bán hàng, đơn hàng và hậu mãi đã có liên kết trực tiếp.

## 3. Phương án triển khai

Overview hiển thị thông tin nhận diện, nguồn, ngày tạo/cập nhật và các chỉ số. Orders đưa sản phẩm, thanh toán và bàn giao vào lịch sử. Leads & Deals và After-sales dùng liên kết tới tài liệu gốc. Timeline hợp nhất sự kiện theo thời gian, gắn loại, nguồn và liên kết tới hồ sơ đọc được.

Giá trị đơn ghi nhận là tổng giá trị các đơn nhìn thấy. Chi tiêu xác nhận chỉ cộng Completed, Paid và có thời điểm thanh toán. Quyền cấp trường quyết định các giá trị có thể tổng hợp.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/customer360.py`, `timeline.py`, `orders.py` và `cellphones_customer_360/doctype/c360_customer/test_timeline.py` trong cùng package.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/Customer360Detail.vue` và `src/components/Customer360/format.js` trong repo CRM.

## 5. Các bước thực hiện

1. Dùng metadata đã triển khai ở các task trước.
2. Chạy `bench build --app crm`. Mở hồ sơ và lần lượt chọn Overview, Orders, Leads & Deals, After-sales và Timeline.
3. Kiểm tra loại, nguồn, ngày giờ và liên kết từng sự kiện. Dùng Previous/Next khi nhiều hơn 20 sự kiện.

## 6. Luồng nghiệp vụ

Nhân viên → mở hồ sơ → kiểm tra quyền khách hàng → lấy các bản ghi và trường được phép đọc → tổng hợp theo thời gian → hiển thị trang yêu cầu. Task, Call Log, Note, Communication, Comment và Version phụ thuộc dữ liệu thực tế và quyền trên tài liệu tương ứng.

## 7. Kiểm thử

MariaDB xác nhận sáu loại sự kiện, thứ tự nhất quán qua phân trang, quyền Guest bị từ chối và đơn Draft không tăng chi tiêu xác nhận.

Chrome đã mở cả năm tab và xác nhận sự kiện tạo hồ sơ trên Timeline có dữ liệu từ site. [Timeline trên CRM](../../screenshots/task10-customer-timeline.png).

## 8. Output bàn giao

Hồ sơ năm tab, Timeline có phân trang, định dạng VND/ngày giờ Việt Nam và kiểm thử hồi quy.

## 9. Tiêu chí hoàn thành

Hồ sơ và Timeline chỉ tổng hợp sự kiện từ tài liệu được phép xem, chỉ số chi tiêu theo căn cứ thanh toán rõ ràng.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: complete Customer 360 profile and activity timeline`. Phân khúc và Analytics dùng lại các dữ liệu giao dịch đã xác nhận.
