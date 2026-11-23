# Ma trận kịch bản demo – Snapshot `demo-v2`

**Nguồn:** dữ liệu tổng hợp giả lập, không phải dữ liệu khách hàng CellphoneS thật. `snapshot_id` là ID logic trong CSV, **không phải** `name` Frappe. Sau khi import, tìm ID Frappe bằng `custom_cv2_snapshot_key` hoặc dòng `example_customer_ids` từ importer.

| ID | Module / tình huống | Minh chứng có trong bộ dữ liệu | Kiểm tra thực tế sau import |
|---|---|---|---|
| V2-01 | Customers đa nguồn | 54 Customer, mỗi nguồn Website/App/Facebook/Zalo/Store/Hotline có 9 khách | Danh sách Customer, lọc theo nguồn và loại Individual/Business |
| V2-02 | Một khách nhiều lần tiếp nhận | `V2-CUS-001`: 3 Intake từ nhiều kênh | Timeline có 3 sự kiện Intake cho khách này |
| V2-03 | Khách trùng chắc chắn | 64 Intake `expected_action=linked` | Không tạo Customer mới; `status=Linked` |
| V2-04 | Khách nghi trùng | 18 Intake `expected_action=review` | `Needs Review`, có `candidate_customer`, chưa tự hợp nhất |
| V2-05 | Dữ liệu sai | 8 Intake `expected_action=rejected` | `Rejected`, không sinh Customer |
| V2-06 | Nhập lại Snapshot | 144 Intake có source reference cố định và các bản ghi có marker | Chạy lại dry-run, số `already_imported` tương ứng; không ghi đè |
| V2-07 | Một Customer – nhiều Lead/Deal | `V2-CUS-001`: 3 Lead + 3 Deal | Profile trả nhiều Lead và Deal |
| V2-08 | Deal pipeline | 7 trạng thái, có 18 `Won`, 16 `Lost` | Board/Deal List và biểu đồ theo trạng thái |
| V2-09 | Lead lifecycle | New/Contacted/Qualified/Nurture/Converted/Unqualified/Junk | Lead List, tìm kiếm, tình trạng và ghi chú tư vấn |
| V2-10 | Đơn hàng nhiều sản phẩm | 62 Order, tổng cộng 100 Order Item | API Order tính đúng `total_amount`, bảng lịch sử mua |
| V2-11 | Mua hàng lặp | `V2-CUS-002`: hai Order `V2-ORD-017`, `V2-ORD-061` | Profile có hai Order, Analytics có khách mua lặp |
| V2-12 | Đơn hàng hủy/chưa hoàn tất | Draft, Confirmed, Processing, Completed, Cancelled | Analytics chỉ tính Confirmed/Processing/Completed vào giá trị đơn hợp lệ |
| V2-13 | Ticket nhiều loại và ưu tiên | 45 Ticket; Warranty/Return/Exchange/Complaint/Technical Support/Other | After-sales danh sách và bộ lọc trạng thái/loại/ưu tiên |
| V2-14 | Ticket theo đơn hàng đúng Customer | Các Ticket có `order_snapshot_id` | Profile và Timeline trả Ticket và Order liên kết |
| V2-15 | Ticket không gắn Order | Cứ mỗi Ticket thứ 6 có `order_snapshot_id` rỗng | Ticket vẫn tạo được với Customer |
| V2-16 | Hoàn tất hỗ trợ | Ticket Resolved và Closed có nội dung giải quyết | Controller chấp nhận Resolution hợp lệ |
| V2-17 | Dashboard/Analytics | `offline_expected_kpis.json` | Đối chiếu số lượng, giá trị đơn hợp lệ, funnel và trạng thái |
| V2-18 | Administration – đăng ký | 8 Pending + 4 Rejected (email `example.test`) | Danh sách yêu cầu xét duyệt; không tạo tài khoản Frappe |

## Những phần không tự động seed

- **Phê duyệt nhân viên và phân quyền:** cần chạy bằng người dùng test riêng và kiểm thử UI/permission; không phát hành User, mật khẩu, token hoặc email mời trong Git.
- **Call Log/CRM Task:** dữ liệu liên hệ của phiên bản này minh họa qua Intake, Order, Ticket. Không tự tạo Call Log/Task vì cần kiểm tra schema/quan hệ chi tiết của CRM v1.92.0 tại site triển khai.
- **Ảnh, file đính kèm, giao dịch thanh toán thật:** không có trong CSV; không dùng để minh chứng nghiệp vụ thanh toán thực tế.
- **Doanh thu thật:** giá và SKU minh họa (VND), không đại diện giá bán hiện hành của CellphoneS.
- **Timestamps cho Lead/Deal:** Frappe `creation` là thời điểm import; không backdate dấu vết audit. Bộ lọc 7d/30d/90d có thể thay đổi theo ngày nhập.

## Gợi ý demo end-to-end

1. Tìm `V2-CUS-002` (tra cứu qua Intake đầu tiên `DEMO-V2-V2-CUS-002-FIRST`).
2. Mở hồ sơ Customer 360, xem các Lead, Deal, hai Order và Ticket.
3. Sang Deals xem các giai đoạn `Won`, `Lost`, `Proposal/Quotation`.
4. Sang After-sales kiểm tra Ticket đang mở và đã giải quyết.
5. Vào Dashboard/Analytics so sánh số liệu với snapshot (lưu ý database có thể có dữ liệu cũ).
6. Với Administration, xem danh sách `Pending` và `Rejected`, kiểm thử `Approved` bằng tài khoản test thủ công thay vì tạo sẵn tài khoản không an toàn.
