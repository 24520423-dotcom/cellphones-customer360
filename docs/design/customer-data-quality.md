# Chất lượng và nhận diện dữ liệu khách hàng

## 1. Mục tiêu

Chuẩn hóa dữ liệu định danh ngay khi ghi hồ sơ trong bước nhận diện của SP01. Hướng nhân viên xác minh khi nhiều hồ sơ dùng chung thông tin liên hệ.

## 2. Hiện trạng

DocType dùng mã `CUST-.#####` và lưu số điện thoại, email, tên, nguồn tiếp nhận. Ba hồ sơ có mặt khi rà soát site. Kiểm tra tổng hợp không phát hiện số điện thoại lưu với tiền tố `+84` hoặc khoảng trắng đầu. Khóa chính đã sinh của hồ sơ cũ được giữ trong mọi thao tác cập nhật.

## 3. Phương án triển khai

| Dữ liệu | Quy tắc |
| --- | --- |
| Tên | Bỏ khoảng trắng đầu và cuối, gộp nhiều khoảng trắng thành một, bắt buộc theo metadata |
| Điện thoại | Bỏ dấu phân tách trình bày, chuyển `+84` hoặc `84` sang `0`. Chấp nhận di động 10 chữ số có đầu 03, 05, 07, 08 hoặc 09 và số cố định 11 chữ số có đầu 02 |
| Email | Bỏ khoảng trắng đầu và cuối, viết thường, kiểm tra một địa chỉ email |
| Nguồn | Gộp khoảng trắng và khớp tên lựa chọn trong metadata, không phân biệt hoa thường |
| Trống | Điện thoại, email và nguồn có thể để trống. Chuỗi chỉ chứa khoảng trắng được chuẩn hóa thành giá trị rỗng |
| Số điện thoại hoặc email đã được sử dụng | Chặn thao tác lưu và yêu cầu xác minh. Lỗi không chứa tên hoặc mã hồ sơ ngoài quyền đọc |
| Tên giống nhau | Có thể tra cứu bằng danh sách, danh tính vẫn cần thông tin xác minh bổ sung |

Tạo và sửa hồ sơ qua ORM chia sẻ khóa giao dịch trên hàng DocType. Truy vấn đối chiếu đọc dữ liệu mới nhất theo khóa, gồm dữ liệu vừa được giao dịch trước đó commit. Khi sửa, controller kiểm tra các trường định danh thay đổi. Giá trị cũ còn nguyên có thể được xem và sửa từng phần.

`customers.find_duplicates` chỉ trả hồ sơ trong quyền đọc, kèm `matched_fields`. Dùng cả số điện thoại và email để phân biệt mức độ tương đồng. Chỉ trùng tên là tín hiệu tra cứu và có thể tồn tại nhiều hồ sơ khác nhau.

## 4. Các file liên quan

Windows và Custom App được bind mount vào Docker dùng cùng mã trong `backend/cellphones_c360/cellphones_c360/cellphones_customer_360/doctype/c360_customer/c360_customer.py`. Các kiểm thử đặt cạnh controller trong `test_c360_customer.py`.

## 5. Các bước thực hiện

1. Mở Customer 360 và nhập tên, điện thoại, email hoặc nguồn trên form.
2. Gửi dữ liệu qua API Frappe hoặc Data Import. Controller chuẩn hóa trước khi ghi.
3. Khi có cảnh báo trùng, tra hồ sơ bằng dữ liệu được phép đọc và tiến hành xác minh.

## 6. Luồng nghiệp vụ

Nhân viên → gửi dữ liệu từ form hoặc import → chuẩn hóa → kiểm tra định dạng và đối chiếu → ghi hồ sơ nếu hợp lệ hoặc yêu cầu xác minh khi trùng. Người xử lý dùng thêm bằng chứng để phân biệt khách dùng chung số điện thoại hoặc email.

## 7. Kiểm thử

Đã chạy tạo hồ sơ với tên nhiều khoảng trắng, email hoa và nguồn khác kiểu chữ. Đã kiểm tra từ chối email sai, số điện thoại sai, tên trống và email trùng. Kiểm thử hai kết nối MariaDB tạo cùng email xác nhận giao dịch thứ hai bị từ chối ngay cả khi đã đọc dữ liệu trước lúc giao dịch đầu commit. Chỉ có một bản ghi được lưu và bản ghi giả lập đó được dọn sau kiểm thử.

## 8. Output bàn giao

Quy tắc dữ liệu, controller dùng chung, API trả ứng viên theo quyền, test cases backend và dữ liệu [đối chiếu trùng](../../data/customers_duplicates.csv).

## 9. Tiêu chí hoàn thành

Đã kiểm chứng chuẩn hóa, đối chiếu tên/điện thoại/email, chỉnh sửa hồ sơ hiện tại và hai luồng tạo đồng thời. Đối chiếu từ CSV và hợp nhất được kiểm thử tại Task 05–06.

## 10. Commit và cập nhật tiến độ

Quy tắc chuẩn hóa dùng chung đã được commit ở Task 02. Task 04 bổ sung API đối chiếu, dữ liệu mẫu và kiểm thử định danh.
