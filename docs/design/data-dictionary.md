# Từ điển dữ liệu Customer 360

| DocType / trường | Kiểu và yêu cầu | Ý nghĩa và kiểm tra |
| --- | --- | --- |
| C360 Customer · name | Naming series CUST-.#####, khóa chính | Mã chuẩn. Hồ sơ nguồn sau hợp nhất giữ mã và trỏ sang Golden Record |
| customer_name | Data, bắt buộc | Bỏ khoảng trắng thừa |
| phone_number, email | Data, tùy chọn, quyền cấp trường | Điện thoại Việt Nam và email chuẩn hóa. Trùng định danh yêu cầu xác minh |
| customer_type, customer_status | Select, bắt buộc | Individual/Business và Active/Inactive |
| source_channel, marketing_consent | Select, Check | Nguồn nhận diện và đồng ý tiếp thị. Consent chỉ cấp từ thông tin được ghi nhận |
| crm_contact, crm_lead | Link, tùy chọn | Liên kết chính đến Contact và CRM Lead |
| crm_links | Table Dynamic Link | Liên kết bổ sung Contact, CRM Lead hoặc CRM Deal |
| merged_into, merged_at, merged_by, merge_reason | Link, Datetime, Link, Small Text | Chỉ luồng hợp nhất ghi thông tin lưu trữ, người thực hiện và lý do |
| C360 Source Record · name | Hash kênh và mã nguồn, khóa chính | Chiến lược replay cho từng sự kiện tiếp nhận |
| source_channel, source_record_id, received_at | Data, Data, Datetime, bắt buộc | Kênh, mã nguồn và thời điểm tiếp nhận |
| processing_status, result_reason, customer | Select, Small Text, Link | Created, Linked, Needs Review hoặc Invalid. Khách hàng được gắn khi đã xác định |
| purchase_interest, reviewed_by, reviewed_at, review_reason | Check, Link, Datetime, Small Text | Nhu cầu và kết quả xác minh của nhân viên |
| Customer Order · name, customer | Naming series ORD-.#####, Link bắt buộc | Mã đơn và hồ sơ khách trong Customer 360 |
| order_date, sales_channel, order_status | Date, Select, Select, bắt buộc | Ngày đơn, kênh bán và vòng đời xử lý |
| crm_deal | Link, tùy chọn | Deal thuộc khách hàng đã chọn |
| payment_method, payment_status, paid_at | Select, Select, Datetime | Phương thức, trạng thái và thời điểm thanh toán |
| fulfillment_method, fulfillment_status, completed_at | Select, Select, Datetime | Nhận tại cửa hàng/giao tận nơi và thời điểm hoàn tất |
| fulfillment_owner | Link User | Phân công vận hành trong cấu hình Task 13 |
| care_task | Link CRM Task | Lịch chăm sóc phát sinh từ đơn |
| items, total_amount | Table bắt buộc, Currency | Danh sách sản phẩm và tổng do server tính |
| Customer Order Item · product_code, product_name | Data | Mã tùy chọn và tên sản phẩm bắt buộc |
| quantity, unit_price, amount | Int, Currency, Currency | Số lượng nguyên dương, giá không âm, thành tiền server tính |
| Customer Support Ticket · name, customer | Naming series theo metadata, Link bắt buộc | Mã yêu cầu gắn khách hàng |
| subject, ticket_type, description | Data, Select, Small Text, bắt buộc | Tóm tắt, loại và chi tiết hỗ trợ |
| related_order | Link | Đơn cùng khách. Bắt buộc với Warranty, Return hoặc Exchange |
| assigned_to, priority, ticket_status | Link User, Select, Select | Người xử lý, mức độ và trạng thái |
| created_date, resolution, resolved_date | Datetime, Small Text, Datetime | Mốc tạo, giải pháp và mốc xử lý do server đặt |
| C360 Registration Request | DocType riêng | Duyệt yêu cầu nhân viên và theo dõi thư mời trong phạm vi Admin |
| Contact, CRM Contacts | Hồ sơ gốc và bảng con | Contact là hồ sơ. CRM Contacts chứa Link đến Contact trên một Deal |
| CRM Lead, CRM Deal | DocType chuẩn CRM | Nhu cầu, pipeline và quan hệ Deal tạo từ Lead |
| CRM Task, CRM Call Log, FCRM Note, Communication, Version | DocType chuẩn | Dòng sự kiện theo quyền trên từng bản ghi |

[ERD](erd.md) · [API Contract](../api/api-contract.md) · [Quyền](permission-matrix.md)
