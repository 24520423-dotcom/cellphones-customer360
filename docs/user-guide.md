# Hướng dẫn sử dụng Customer 360

Mở CRM rồi đăng nhập bằng tài khoản đã cấp. Với site phát triển, địa chỉ là [crm.localhost](http://crm.localhost:8000/crm).

| Công việc | Thao tác |
| --- | --- |
| Tìm khách hàng | Chọn **Customer 360**, nhập tên, điện thoại, email hoặc mã. Có thể chọn phân khúc rồi tìm |
| Tạo hoặc sửa hồ sơ | Chọn **Create Customer** ở danh sách hoặc **Edit Customer** trong hồ sơ. Nếu báo trùng, đối chiếu trước khi lưu |
| Xác minh và hợp nhất | Mở hồ sơ cần giữ, chọn **Review Duplicate**, xem hai hồ sơ, chọn giá trị và nhập lý do. **Merge Customer** xuất hiện khi đủ quyền |
| Tiếp nhận nguồn | Chạy trial import CSV hoặc gửi API phiên Frappe. Mở **C360 Source Record** trong Desk để xem Created, Linked, Needs Review hoặc Invalid |
| Bán hàng và mua lại | Từ tab **Leads & Deals**, tạo hoặc liên kết bản ghi CRM. Khi khách quay lại, tạo thêm Lead hoặc Deal trên hồ sơ đã có |
| Xử lý đơn | Chọn **Orders**, lọc hoặc mở đơn. Form chuẩn có sản phẩm, trạng thái đơn, thanh toán và giao nhận. Dùng Open Customer 360 để quay về hồ sơ |
| Hậu mãi | Chọn **After-sales**, lập Ticket và giao người xử lý. Với bảo hành/đổi trả, chọn đơn Completed đúng khách. Ghi giải pháp trước Resolved/Closed |
| Phân tích | Chọn **Customer Analytics**, chọn kỳ và áp dụng. Quyền đọc dữ liệu quyết định KPI và biểu đồ hiện ra |
| Lịch sử | Mở Timeline trong hồ sơ, xem sự kiện và chọn **Open record** khi có liên kết |

Trong nhóm tab, dùng phím mũi tên hoặc Home/End. Quản trị viên cấp vai trò và phạm vi qua User, Role Profile và User Permission của Frappe. [Quyền và giới hạn theo vai trò](design/permission-matrix.md)
