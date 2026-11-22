# Báo cáo triển khai Customer 360 CellphoneS

Ngày kiểm tra 22/11/2026. Các tuyến nghiệp vụ dùng Frappe trên site `crm.localhost`. Chrome headless đã đăng nhập qua giao diện, mở Dashboard, After-sales, Analytics, Deals, Leads, Customer 360 và Administration, rồi đăng xuất. Các ca ghi dữ liệu được chạy qua bộ xử lý REST Frappe trong giao dịch có rollback.

## Giai đoạn 1. Giao diện hậu mãi

| Mã | Công việc và tệp | API sử dụng | Kiểm thử và cách kiểm tra | Bước kế tiếp |
| --- | --- | --- | --- | --- |
| AS-01 | Trang `/after-sales`, KPI, bảng và trạng thái tải, rỗng, lỗi. [AfterSales.jsx](frontend/src/pages/AfterSales/AfterSales.jsx) | GET danh sách Ticket sau API-03. KPI tính trên tập Ticket người dùng được xem. | Chrome đạt ở 1.440, 820 và 390 px. Mở After-sales từ sidebar. | AS-02 |
| AS-02 | Bảng, tìm kiếm không dấu, lọc trạng thái và ngày, sắp xếp, phân trang. [AfterSalesList.jsx](frontend/src/pages/AfterSales/AfterSalesList.jsx), [ticketFilters.js](frontend/src/pages/AfterSales/ticketFilters.js) | GET Ticket và nhãn khách hàng theo lô sau API-03. | Kiểm tra logic tìm kiếm và lọc ngày đạt. Chrome kiểm tra chuyển trang, lọc Pending và mở mã Ticket. | AS-03 |
| AS-03 | Form tạo yêu cầu, chọn khách hàng và đơn thuộc khách hàng đó. [AfterSalesForm.jsx](frontend/src/pages/AfterSales/AfterSalesForm.jsx) | GET C360 Customer, GET Customer Order theo `customer`, POST Ticket. | Chrome kiểm tra trường bắt buộc, lỗi lưu giữ form và tải lại danh sách sau khi lưu. Frappe từ chối đơn thuộc khách khác. | AS-04 |
| AS-04 | Tuyến chi tiết, liên kết hồ sơ khách hàng, trạng thái, phân công, ngày tạo, cập nhật và giải quyết. [AfterSalesTicketPage.jsx](frontend/src/pages/AfterSales/AfterSalesTicketPage.jsx), [AfterSalesDetail.jsx](frontend/src/pages/AfterSales/AfterSalesDetail.jsx) | GET Ticket, GET quyền theo Ticket, PUT trạng thái và nội dung xử lý. | Mở mã Ticket thật. Kiểm thử Frappe xác nhận chuyển Resolved đòi hỏi nội dung xử lý. Lịch sử hiện có gồm các mốc lưu trên Ticket. | AS-05 |
| AS-05 | Badge trạng thái, thông báo kết quả, lỗi trong form và phục hồi khi tải lại. [TicketStatus.jsx](frontend/src/pages/AfterSales/TicketStatus.jsx), [AfterSales.jsx](frontend/src/pages/AfterSales/AfterSales.jsx) | GET lại sau POST hoặc PUT thành công. | Chrome kiểm tra lỗi form, bản ghi xuất hiện sau khi lưu và điều hướng về danh sách. | AN-01 |

## Giai đoạn 2. Giao diện Analytics

Các mục AN-01 đến AN-06 dùng [Analytics.jsx](frontend/src/pages/Analytics/Analytics.jsx), [useAnalytics.js](frontend/src/hooks/useAnalytics.js) và GET `cellphones_c360.api.analytics.get_analytics_overview` sau API-06.

| Mã | Công việc | Kiểm thử và cách kiểm tra | Bước kế tiếp |
| --- | --- | --- | --- |
| AN-01 | Trang `/analytics`, thẻ KPI, biểu đồ và bảng với trạng thái tải, lỗi và thiếu dữ liệu. | Mở Analytics trên Chrome và kiểm tra biểu đồ, bảng cùng thông báo khi mô phỏng mất kết nối. | AN-02 |
| AN-02 | Tổng hồ sơ đến cuối kỳ, hồ sơ mới, kênh nguồn, loại khách, khách có một hoặc nhiều đơn hợp lệ trong kỳ. | Xem mục Khách hàng. Tổng hồ sơ khớp truy vấn Frappe độc lập. | AN-03 |
| AN-03 | Lead theo trạng thái và nguồn, Deal theo giai đoạn, Won/Lost, pipeline, tỷ lệ thắng và tỷ lệ chuyển đổi Lead. | Xem mục Lead và Deal. Đối chiếu tổng Lead và Deal theo toàn kỳ và 7 ngày. | AN-04 |
| AN-04 | Tổng đơn, phân bố trạng thái, xu hướng, giá trị đơn hợp lệ và giá trị trung bình. | Xem mục Đơn hàng. Kiểm tra tổng khớp Customer Order theo toàn kỳ và 7 ngày. | AN-05 |
| AN-05 | Ticket theo trạng thái, loại, ngày tạo, tỷ lệ giải quyết và thời gian xử lý trung bình có đủ mốc. | Xem mục Hậu mãi. Đối chiếu tổng Ticket và kiểm tra số đếm tăng sau một lần tạo trong giao dịch thử. | AN-06 |
| AN-06 | Bộ lọc 7, 30, 90 ngày và toàn bộ, tải lại, chú giải, tooltip và định dạng số. | Đổi sang 7 ngày trên Chrome và kiểm tra request đổi kỳ. Mô phỏng lỗi mạng và dùng nút tải lại. | API-01 |

## Giai đoạn 3 và 4. API hậu mãi và Analytics

Hậu mãi sử dụng [afterSalesService.js](frontend/src/services/afterSalesService.js) và [after_sales.py](backend/cellphones_c360/cellphones_c360/api/after_sales.py). Analytics sử dụng [analytics.py](backend/cellphones_c360/cellphones_c360/api/analytics.py) và [analyticsService.js](frontend/src/services/analyticsService.js).

| Mã | Công việc và API | Kiểm thử và cách kiểm tra | Bước kế tiếp |
| --- | --- | --- | --- |
| API-01 | Xác minh metadata và các quy tắc của Customer Support Ticket, C360 Customer và Customer Order. | Kiểm tra controller, field và quyền trên site. Sales User và Sales Manager tiêu chuẩn bị từ chối tạo Ticket. | API-02 |
| API-02 | GET `/api/resource/Customer%20Support%20Ticket` trả danh sách theo lô. GET theo mã trả chi tiết. POST nhận `customer`, `related_order`, `subject`, `description`, `ticket_type`, `ticket_status` và `priority`. PUT nhận `ticket_status` và `resolution`. | Chạy GET, POST, PUT bằng Frappe. Kiểm tra payload sai, Ticket không tồn tại và CSRF. | API-03 |
| API-03 | Nối màn hình danh sách, chi tiết, tạo và cập nhật vào REST và GET `cellphones_c360.api.after_sales.get_capabilities`. | Mở danh sách và chi tiết thật trên Chrome. Mô phỏng lỗi và thành công ở form tạo, đồng thời kiểm tra bản ghi qua bộ xử lý REST Frappe. | API-04 |
| API-04 | GET `cellphones_c360.api.customer360.get_customer_profile` trả Ticket từ cùng DocType. [customer360.py](backend/cellphones_c360/cellphones_c360/api/customer360.py), [CustomerSupport.jsx](frontend/src/components/customers/CustomerSupport.jsx) | Mở tab Sau bán trong hồ sơ và chọn mã Ticket. Kiểm thử rollback xác nhận Ticket xuất hiện đúng khách hàng. | API-05 |
| API-05 | GET `cellphones_c360.api.analytics.get_analytics_overview` nhận `period` và `activities`, trả chỉ số tổng hợp theo quyền đọc. | Đối chiếu trực tiếp trên site. Kết quả thiếu quyền hoặc thiếu cơ sở tính được trả về dạng chưa xác định. | API-06 |
| API-06 | Service và hook dùng cùng kỳ cho các chỉ số, biểu đồ, bảng, cập nhật khi đổi kỳ và bỏ qua phản hồi cũ. | Chrome kiểm tra đổi kỳ, tải lại và lỗi mạng. | API-07 |
| API-07 | Đối chiếu năm DocType bằng truy vấn Frappe độc lập. | Toàn kỳ có 3 khách hàng, 7 Lead, 3 Deal, 1 đơn hàng và 1 Ticket. Kỳ 7 ngày có 3 hồ sơ đến cuối kỳ, 2 Lead, 1 Deal, 1 đơn và 1 Ticket. Các số này là ảnh chụp khi kiểm thử. | DB-01 |

Đơn hợp lệ có trạng thái Confirmed, Processing hoặc Completed. Giá trị đơn là tổng giá trị theo dữ liệu đặt hàng. Tỷ lệ thắng Deal là Won chia cho Won + Lost trong nhóm Deal tạo trong kỳ. Tỷ lệ chuyển đổi Lead là số Lead tạo trong kỳ có ít nhất một Deal thắng cũng tạo trong kỳ, chia cho tổng Lead tạo trong kỳ. Một Lead chỉ đóng góp một lần vào tử số. Tổng pipeline bằng VND chỉ hiện khi có đủ dữ liệu giá trị và đơn vị tiền. Thời gian giải quyết dùng ngày tạo và ngày giải quyết đã lưu.

## Giai đoạn 5. Dashboard

Tất cả mục DB dùng API Analytics với cùng tham số kỳ. Dashboard gửi thêm `activities=1` để nhận tối đa 10 hoạt động gần nhất trong phạm vi quyền và kỳ đã chọn.

| Mã | Công việc và tệp | Kiểm thử và cách kiểm tra | Bước kế tiếp |
| --- | --- | --- | --- |
| DB-01 | Bỏ dữ liệu minh họa khỏi [Dashboard.jsx](frontend/src/pages/Dashboard/Dashboard.jsx). | Đăng nhập và mở Dashboard bằng Frappe thật. | DB-02 |
| DB-02 | Lead, Deal, Won và Conversion Rate từ kết quả API. [Dashboard.jsx](frontend/src/pages/Dashboard/Dashboard.jsx) | Đối chiếu tổng trên site. Đọc định nghĩa tỷ lệ ngay dưới thẻ. | DB-03 |
| DB-03 | Biểu đồ lấy trạng thái và giai đoạn có số liệu trong kỳ. [LeadChart.jsx](frontend/src/pages/Dashboard/LeadChart.jsx), [DealChart.jsx](frontend/src/pages/Dashboard/DealChart.jsx) | Mở Dashboard thật và đối chiếu phân bố với Analytics cùng kỳ. | DB-04 |
| DB-04 | Chuẩn hóa hoạt động từ CRM Call Log, CRM Task, CRM Deal, Customer Order và Customer Support Ticket. [RecentActivities.jsx](frontend/src/pages/Dashboard/RecentActivities.jsx) | Backend trả 7 hoạt động toàn kỳ và 3 hoạt động trong kỳ 7 ngày tại thời điểm thử. Cột khách hàng hoặc nhân viên hiển thị trống khi bản ghi thiếu liên kết tương ứng. | DB-05 |
| DB-05 | Bộ lọc kỳ thống nhất cho KPI, biểu đồ và hoạt động. [Dashboard.jsx](frontend/src/pages/Dashboard/Dashboard.jsx) | Kiểm tra phản hồi 7 ngày với `activities=1` qua HTTP đã đăng nhập. | CRM-01 |

## Giai đoạn 6. CRM và quản trị

| Mã | Công việc và tệp | API sử dụng | Kiểm thử và cách kiểm tra | Bước kế tiếp |
| --- | --- | --- | --- | --- |
| CRM-01 | Gỡ debug log, tải Lead theo lô, đọc trạng thái và quyền, bổ sung lịch sử cuộc gọi và công việc liên kết. [LeadList.jsx](frontend/src/pages/Leads/LeadList.jsx), [LeadDetail.jsx](frontend/src/pages/Leads/LeadDetail.jsx), [LeadForm.jsx](frontend/src/pages/Leads/LeadForm.jsx), [leadService.js](frontend/src/services/leadService.js), [leads.py](backend/cellphones_c360/cellphones_c360/api/leads.py) | REST `CRM Lead` và GET `cellphones_c360.api.leads.get_options`. | Chrome mở Leads. REST xác nhận tạo, sửa, đọc lại ghi chú. | CRM-02 |
| CRM-02 | Persist Deal, dùng các giai đoạn thực từ Frappe, chia sẻ dữ liệu giữa bảng và pipeline, liên kết qua Lead. [DealList.jsx](frontend/src/pages/Deals/DealList.jsx), [DealForm.jsx](frontend/src/pages/Deals/DealForm.jsx), [DealBoard.jsx](frontend/src/pages/Deals/DealBoard.jsx), [DealDetail.jsx](frontend/src/pages/Deals/DealDetail.jsx), [dealService.js](frontend/src/services/dealService.js), [deals.py](backend/cellphones_c360/cellphones_c360/api/deals.py) | REST `CRM Deal`, GET `cellphones_c360.api.deals.get_options`. | Browser mở Deals. REST xác nhận tạo Deal, đọc lại Lead liên kết và cập nhật trạng thái. | CRM-03 |
| CRM-03 | Thêm form quản lý hồ sơ, liên kết Ticket và timeline. [CustomerList.jsx](frontend/src/pages/Customers/CustomerList.jsx), [CustomerProfile.jsx](frontend/src/pages/Customers/CustomerProfile.jsx), [CustomerEditor.jsx](frontend/src/pages/Customers/CustomerEditor.jsx), [customerService.js](frontend/src/services/customerService.js), [customers.py](backend/cellphones_c360/cellphones_c360/api/customers.py) | REST `C360 Customer`, GET `cellphones_c360.api.customers.get_access`, GET danh sách, hồ sơ và timeline Customer 360. | Browser mở Customer 360. REST xác nhận tạo và sửa hồ sơ. Kiểm tra liên kết Ticket trong hồ sơ và timeline. | CRM-04 |
| CRM-04 | Kiểm tra quyền quản trị theo phiên, dùng Frappe Desk cho User, Role và Role Permission Manager. [Administration.jsx](frontend/src/pages/Administration/Administration.jsx), [administration.py](backend/cellphones_c360/cellphones_c360/api/administration.py), [auth.js](frontend/src/services/auth.js) | GET `cellphones_c360.api.administration.get_access`, POST login/logout và GET phiên Frappe. | Chrome mở Administration bằng Administrator. Sales User và Sales Manager thử nghiệm không có quyền quản trị. Quản lý tài khoản trong Frappe Desk. | TEST-01 |

## Giai đoạn 7. Kiểm thử tổng thể

| Mã | Phạm vi và kết quả | Cách đối chiếu | Bước kế tiếp |
| --- | --- | --- | --- |
| TEST-01 | HTTP thật xác nhận đăng nhập, cookie phiên, GET Analytics, GET danh sách Ticket, từ chối CSRF sai và 404 với CSRF hợp lệ. Giao dịch thử xác nhận POST, PUT, payload sai và bản ghi thiếu. Chrome mô phỏng lỗi mạng và phản hồi lỗi API ở form. | Đăng nhập, mở Dashboard và After-sales, sau đó đăng xuất. API ghi chỉ nhận token từ phiên. | TEST-02 |
| TEST-02 | Tạo, sửa và đọc lại Lead, Customer, Ticket, Deal qua bộ xử lý REST trên site. Xác nhận Ticket liên kết Customer và Order, Deal liên kết Lead, Analytics cập nhật sau thao tác ghi. Giao dịch đã rollback. | Mở Customer 360 và các tab Lead & Deal, Mua hàng, Sau bán, Tương tác. | TEST-03 |
| TEST-03 | Chrome headless kiểm tra After-sales tại 1.440, 820 và 390 px, sidebar mobile, phân trang, lọc, xem chi tiết, thông báo form, lỗi mạng và tải lại. Chrome đăng nhập thật và mở các tuyến nghiệp vụ. | Thu hẹp trình duyệt, mở sidebar, đổi bộ lọc và mở mã Ticket. | TEST-04 |
| TEST-04 | Administrator thao tác được theo quyền. Các tài khoản chuẩn mang vai trò Sales User và Sales Manager bị Frappe từ chối tạo Ticket. Chưa xác nhận một tài khoản CSKH chuyên biệt để chạy ca kiểm thử vai trò đó. | Dùng Frappe Role Permission Manager để xem quyền tại site triển khai. | TEST-05 |
| TEST-05 | `npm run lint` và `npm run build` đạt, kiểm tra cú pháp Python và `git diff --check` đạt. Vite còn cảnh báo bundle JavaScript lớn hơn 500 kB sau minify. | Chạy các lệnh lint và build tại `Web CellphoneS/frontend`. | Kết thúc các mục trong kế hoạch |
