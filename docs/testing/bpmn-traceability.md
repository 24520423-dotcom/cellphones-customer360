# Dấu vết kiểm thử BPMN

| Quy trình | Actor và điểm bắt đầu | Gateway và kết thúc | Tính năng | Test ID |
| --- | --- | --- | --- | --- |
| SP01 Nhận diện khách hàng | Nhân viên tiếp nhận CSV hoặc tạo hồ sơ | Hợp lệ → tạo/liên kết, xung đột → xác minh/hợp nhất, lỗi → ghi nguyên nhân | Intake, Data Quality, Create/Edit, Duplicate Review | E2E-01, 02, 08, 09 |
| SP02 Tư vấn và giao dịch | Sales nhận nhu cầu trên hồ sơ | Mua → Deal và đơn; cân nhắc → tiếp tục pipeline; từ chối → Lost; đơn thất bại → không tính tiền thu | Lead/Deal chuẩn, Orders, thanh toán, mua lại | E2E-01, 03, 04, 05, 08 |
| SP03 Bàn giao | Vận hành xử lý đơn Confirmed | Pickup hoặc Delivery → bàn giao và Completed; Failed → giữ nguyên kết quả và hủy khi phù hợp | Phương thức giao nhận, kiểm tra cặp trạng thái, ngày bàn giao | E2E-01, 03, 05 |
| SP04 Hậu mãi | CSKH nhận yêu cầu hoặc scheduler phát hiện đơn Completed | Đơn đủ điều kiện → Ticket, phân công và xử lý; hạn chăm sóc sau ba ngày; đề xuất demo cần consent; nhu cầu mới → SP02 | Ticket, CRM Task, Comment demo, Timeline và CRM links | E2E-03, 06, 07, 08 |

Xem [sơ đồ BPMN](../design/bpmn.md), [kịch bản thực thi](end-to-end-test-cases.md) và [bộ demo](demo-scenario.md).
