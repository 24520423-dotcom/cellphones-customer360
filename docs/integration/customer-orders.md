# Task 08 · Quản lý đơn hàng

## 1. Mục tiêu

SP02 xác nhận nhu cầu, đơn hàng và trạng thái thanh toán. SP03 theo dõi bàn giao trực tiếp hoặc giao tận nơi.

## 2. Hiện trạng

`Customer Order` và bảng con `Customer Order Item` đã có tổng tiền và các trạng thái Draft, Confirmed, Processing, Completed, Cancelled. Cần ghi phương thức và trạng thái thanh toán, giao nhận và đường dẫn từ CRM.

## 3. Phương án triển khai

Orders trong sidebar CRM hiển thị danh sách, lọc theo đơn, khách hàng, trạng thái, kênh và ngày. Chi tiết, tạo và sửa sử dụng form chuẩn Frappe Desk với hàng sản phẩm và quyền DocType. Controller tính lại tổng từ số lượng và đơn giá. Nhân viên có thể liên kết Deal đã thuộc khách hàng.

| Nhóm | Giá trị nghiệp vụ |
| --- | --- |
| Trạng thái đơn | Draft → Confirmed → Processing → Completed. Draft, Confirmed và Processing có thể chuyển Cancelled |
| Phương thức thanh toán | Direct, COD, Installment |
| Trạng thái thanh toán | Unpaid, Pending, Paid, Refunded. Ghi thời điểm khi chuyển Paid |
| Nhận tại cửa hàng | Pickup, Ready for Pickup, Picked Up |
| Giao tận nơi | Delivery, In Transit, Delivered hoặc Failed |

Đơn kết thúc Completed cần trạng thái bàn giao tương ứng. Các đơn cũ giữ thông tin thanh toán và giao nhận chưa xác định nếu trước đó chưa thu thập. Deal Won và trạng thái đơn, trạng thái thanh toán được lưu riêng.

## 4. Các file liên quan

- Windows: `backend/cellphones_c360/cellphones_c360/api/orders.py` và `cellphones_customer_360/doctype/customer_order/` trong cùng package.
- Docker: `/home/frappe/frappe-bench/apps/crm/frontend/src/pages/CustomerOrders.vue`, `src/pages/Customer360Detail.vue`, `src/router.js` và `src/components/Layouts/AppSidebar.vue` trong repo CRM.

## 5. Các bước thực hiện

1. Sao lưu trước khi nạp các trường. Trong Bench, chạy `bench --site crm.localhost reload-doc cellphones_customer_360 doctype customer_order` và `bench build --app crm`.
2. Mở **Orders** trong sidebar, dùng bộ lọc hoặc chọn **New Order**.
3. Trong form chuẩn, chọn khách hàng, kênh, sản phẩm, số lượng và đơn giá. Lưu Draft rồi xác nhận cùng phương thức thanh toán và giao nhận.
4. Tiến hành xử lý, cập nhật thanh toán và bàn giao. Chọn Completed sau khi bàn giao, hoặc Cancelled khi kết thúc theo nhánh hủy.
5. Mở tab Orders của khách hàng để kiểm tra đơn, sản phẩm và trạng thái.

## 6. Luồng nghiệp vụ

Nhân viên → xác nhận nhu cầu → tạo Draft và sản phẩm → kiểm tra quyền, thuộc khách hàng, số lượng và giá → xác nhận → thanh toán và bàn giao theo phương thức đã chọn → hoàn tất hoặc hủy → đồng bộ Customer 360. Trường hợp giao thất bại giữ thông tin Failed. Đơn đã thanh toán cần ghi hoàn tiền trước khi hủy.

## 7. Kiểm thử

Bài kiểm thử MariaDB xác nhận nhận tại cửa hàng, tính đúng tổng 240.000 VND từ hai sản phẩm đơn giá 120.000 VND, thời điểm thanh toán và hoàn tất, tìm theo khách hàng và kỳ, từ chối giá hoặc số lượng sai, chuyển hoàn tất trước bàn giao, giá thay đổi sau xác nhận và Guest. Đã kiểm tra nhánh COD giao thất bại và hủy. Ba kiểm thử hợp nhất và rollback tiếp tục đạt.

Chrome đã lọc một đơn giả lập theo khách hàng, mở chi tiết có sản phẩm và trường thanh toán, rồi mở form tạo đơn chuẩn. [Danh sách đã lọc](../../screenshots/task08-order-list.png) và [chi tiết đơn](../../screenshots/task08-order-detail.png).

## 8. Output bàn giao

Orders list, bộ lọc, form và chi tiết Frappe Desk, liên kết hồ sơ và Deal, metadata, validation và kiểm thử.

## 9. Tiêu chí hoàn thành

Đơn và sản phẩm được lưu từ form, tổng tiền được tính phía server và chỉ trạng thái hợp lệ có thể ghi. Hồ sơ Customer 360 hiển thị lịch sử đơn theo quyền.

## 10. Commit và cập nhật tiến độ

Commit dự kiến `feat: manage customer orders and fulfillment in native CRM`. Bước kế tiếp dùng đơn đã hoàn tất để chăm sóc sau bán.
