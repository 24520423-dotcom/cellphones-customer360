## 4.3. CẤU HÌNH HỆ THỐNG FRAPPE CRM

### 4.3.1. Mục tiêu cấu hình

Sau khi hoàn tất quá trình cài đặt Frappe Framework và Frappe CRM trong môi trường Docker, nhóm tiến hành cấu hình hệ thống nhằm đáp ứng các yêu cầu nghiệp vụ của bài toán Customer 360 tại CellphoneS.

Việc cấu hình tập trung vào thiết lập thông tin hệ thống, quản lý người dùng và phân quyền, tổ chức nhóm bán hàng, xây dựng quy trình quản lý khách hàng tiềm năng và cơ hội bán hàng, đồng thời thiết lập các chức năng hỗ trợ tương tác với khách hàng.

Các cấu hình được thực hiện trên môi trường CRM thử nghiệm, sử dụng tài khoản và dữ liệu giả lập để mô phỏng hoạt động kinh doanh của CellphoneS. Mục tiêu là tạo nền tảng để nhóm tiếp tục nhập dữ liệu, triển khai quy trình nghiệp vụ và phát triển các chức năng Customer 360.

### 4.3.2. Cấu hình thông tin hệ thống

Nhóm đăng nhập vào hệ thống bằng tài khoản Administrator và truy cập các chức năng thiết lập của Frappe Framework để kiểm tra thông tin cấu hình cơ bản.

Các thông số được lựa chọn phù hợp với bối cảnh doanh nghiệp bán lẻ tại Việt Nam.

| Thông số | Giá trị cấu hình dự kiến | Mục đích |
| --- | --- | --- |
| Tên tổ chức | CellphoneS (Demo) | Xác định đơn vị được mô phỏng |
| Múi giờ | Asia/Ho_Chi_Minh | Đồng bộ thời gian hoạt động và giao dịch |
| Tiền tệ | VND | Phù hợp với hoạt động kinh doanh tại Việt Nam |
| Ngôn ngữ | Tiếng Việt hoặc tiếng Anh | Phù hợp với khả năng hỗ trợ của hệ thống |
| Site | crm.localhost | Định danh môi trường CRM thử nghiệm |

Nhóm kiểm tra các thông số có thể thiết lập thông qua giao diện quản trị và ghi nhận những giới hạn cấu hình nếu có.

Hình 4.7. Giao diện thiết lập thông tin hệ thống Frappe

![Hình minh chứng 1](CV03-images/hinh-001.png)

![Hình minh chứng 2](CV03-images/hinh-002.png)

### 4.3.3. Cấu hình người dùng và phân quyền

Để mô phỏng hoạt động phối hợp giữa các bộ phận trong doanh nghiệp, nhóm tiến hành xây dựng các tài khoản người dùng đại diện cho những vai trò tham gia vào quy trình quản lý khách hàng.

Các vai trò được xác định dựa trên nhu cầu quản lý và khai thác thông tin khách hàng trong hệ thống CRM.

| Nhóm người dùng | Vai trò nghiệp vụ | Trách nhiệm |
| --- | --- | --- |
| Administrator | Quản trị hệ thống | Quản lý cấu hình, người dùng và các thiết lập kỹ thuật |
| Sales Manager | Quản lý bán hàng | Theo dõi hoạt động bán hàng và quản lý cơ hội kinh doanh |
| Sales User | Nhân viên bán hàng | Tiếp nhận Lead, tư vấn và cập nhật Deal |
| CSKH | Nhân viên chăm sóc khách hàng | Theo dõi tương tác và hỗ trợ khách hàng sau bán |

Trong môi trường thử nghiệm, nhóm đã xây dựng các tài khoản đại diện cho Sales Manager và Sales User nhằm kiểm tra việc phân công công việc và xử lý dữ liệu bán hàng.

Ví dụ tài khoản thử nghiệm:

Sales Manager: sales.manager@cellphones.example

Sales User: sales.user@cellphones.example

Sau khi tạo tài khoản, nhóm kiểm tra việc gán vai trò và các quyền truy cập đối với dữ liệu CRM, bao gồm quyền xem, tạo và chỉnh sửa thông tin.

Việc phân quyền nhằm hạn chế truy cập không phù hợp và bảo đảm mỗi người dùng thực hiện các chức năng tương ứng với trách nhiệm nghiệp vụ.

Hình 4.8. Danh sách tài khoản người dùng trên hệ thống Frappe

![Hình minh chứng 3](CV03-images/hinh-003.png)

![Hình minh chứng 4](CV03-images/hinh-004.png)

![Hình minh chứng 5](CV03-images/hinh-005.png)

Hình 4.9. Giao diện cấu hình Role và Permission

![Hình minh chứng 6](CV03-images/hinh-006.png)

### 4.3.4. Cấu hình Sales Team

Nhóm tiếp tục cấu hình bộ phận bán hàng trong Frappe CRM để mô phỏng hoạt động tiếp nhận và xử lý cơ hội kinh doanh tại CellphoneS.

Sales Team được tổ chức theo mô hình quản lý gồm người phụ trách và các nhân viên bán hàng. Trong đó, Sales Manager thực hiện vai trò quản lý, theo dõi hoạt động của nhóm; Sales User chịu trách nhiệm trực tiếp xử lý Lead và Deal được phân công.

Cấu hình này hỗ trợ các nghiệp vụ:

Phân công khách hàng tiềm năng cho nhân viên phụ trách.

Gán người chịu trách nhiệm xử lý cơ hội bán hàng.

Theo dõi tiến độ xử lý Lead và Deal.

Hỗ trợ quản lý hoạt động bán hàng theo nhân viên hoặc nhóm.

Việc tổ chức Sales Team giúp xác định trách nhiệm xử lý dữ liệu khách hàng, đồng thời tạo cơ sở cho việc theo dõi hiệu suất bán hàng trong các giai đoạn tiếp theo.

Hình 4.10. Cấu hình Sales Team và thành viên phụ trách

![Hình minh chứng 7](CV03-images/hinh-007.png)

### 4.3.5. Cấu hình quản lý khách hàng tiềm năng (Lead Management)

Lead là đối tượng đại diện cho khách hàng tiềm năng đã thể hiện sự quan tâm đến sản phẩm hoặc dịch vụ nhưng chưa hình thành cơ hội bán hàng được xác nhận.

Trong tình huống kinh doanh của CellphoneS, Lead có thể được tạo từ các nguồn như website, Facebook, Zalo, hotline hoặc thông tin khách hàng được nhân viên ghi nhận tại cửa hàng.

Nhóm tiến hành kiểm tra và cấu hình các trạng thái Lead để hỗ trợ quá trình tiếp nhận, liên hệ và đánh giá nhu cầu khách hàng.

Các trạng thái được lựa chọn cần phản ánh được quá trình xử lý Lead từ khi tiếp nhận đến khi đủ điều kiện chuyển thành cơ hội bán hàng.

| Trạng thái nghiệp vụ | Ý nghĩa |
| --- | --- |
| New | Lead mới được ghi nhận vào hệ thống |
| Contacted | Nhân viên đã liên hệ với khách hàng |
| Nurture | Khách hàng có quan tâm đến sản phẩm nhưng chưa sẵn sàng mua, cần tiếp tục theo dõi, tư vấn và chăm sóc. |
| Qualified | Khách hàng có nhu cầu phù hợp và đủ điều kiện tiếp tục tư vấn |
| Unqualified | Khách hàng chưa phù hợp với tiêu chí chuyển đổi |
| Converted | Lead đã được chuyển sang giai đoạn quản lý cơ hội bán hàng |
| Junk | Lead không hợp lệ, chứa thông tin sai lệch, trùng lặp không cần thiết hoặc nội dung spam, không có giá trị khai thác bán hàng. |

Lưu ý: Đây là bộ trạng thái nghiệp vụ đề xuất; tên trạng thái thực tế cần đối chiếu với cấu hình đã lưu trên Frappe CRM.

Việc sử dụng Lead Status giúp nhân viên theo dõi tình trạng xử lý khách hàng tiềm năng, hạn chế bỏ sót yêu cầu tư vấn và hỗ trợ chuyển đổi Lead sang Deal.

Hình 4.11. Danh sách trạng thái khách hàng tiềm năng (Lead Status) trên Frappe CRM.

![Hình minh chứng 8](CV03-images/hinh-008.png)

### 4.3.6. Cấu hình quy trình quản lý cơ hội bán hàng (Deal Pipeline)

Sau khi Lead được đánh giá có tiềm năng mua hàng, thông tin có thể được chuyển sang Deal để tiếp tục theo dõi quá trình tư vấn và chốt đơn.

Nhóm xây dựng Deal Pipeline nhằm mô phỏng các giai đoạn xử lý cơ hội bán điện thoại tại CellphoneS.

| Giai đoạn | Ý nghĩa nghiệp vụ |
| --- | --- |
| New | Cơ hội bán hàng mới được tạo |
| Qualification | Xác định nhu cầu, khả năng mua và sản phẩm phù hợp |
| Proposal | Tư vấn sản phẩm, cung cấp báo giá và ưu đãi |
| Negotiation | Trao đổi về giá, phương thức thanh toán hoặc điều kiện mua hàng |
| Won | Khách hàng đồng ý mua, cơ hội bán hàng thành công |
| Lost | Khách hàng không tiếp tục mua, cơ hội bán hàng thất bại |

Pipeline giúp chuẩn hóa quá trình theo dõi cơ hội kinh doanh và hỗ trợ nhân viên cập nhật tiến độ tư vấn khách hàng.

Trong quá trình kiểm thử, nhóm sử dụng dữ liệu Deal giả lập để thực hiện thao tác cập nhật giai đoạn và theo dõi kết quả trên giao diện CRM.

Hình 4.12. Giao diện Deal Pipeline trên Frappe CRM

![Hình minh chứng 9](CV03-images/hinh-009.png)

### 4.3.7. Cấu hình lý do thất bại (Lost Reasons)

Không phải tất cả các cơ hội bán hàng đều chuyển đổi thành đơn hàng thành công. Do đó, nhóm thiết lập danh sách Lost Reasons để ghi nhận nguyên nhân khi Deal kết thúc ở trạng thái Lost.

Các lý do được lựa chọn phù hợp với tình huống kinh doanh bán lẻ điện thoại.

| Lost Reason | Diễn giải |
| --- | --- |
| Price Too High | Khách hàng cho rằng giá bán chưa phù hợp |
| Changed Purchase Plan | Khách hàng thay đổi hoặc hoãn kế hoạch mua |
| No Customer Response | Khách hàng không phản hồi sau khi được liên hệ |
| Chose Competitor | Khách hàng lựa chọn sản phẩm hoặc nhà bán lẻ khác |

Việc ghi nhận Lost Reason giúp doanh nghiệp phân tích nguyên nhân không chuyển đổi, từ đó có cơ sở cải thiện hoạt động tư vấn, chính sách bán hàng và chăm sóc khách hàng.

Nhóm đã thử nghiệm trường hợp Deal không thành công với lý do No Customer Response để kiểm tra khả năng ghi nhận thông tin thất bại.

Hình 4.13. Danh sách Lost Reasons trên hệ thống

![Hình minh chứng 10](CV03-images/hinh-010.png)

Hình 4.14. Deal được đánh dấu Lost và ghi nhận lý do thất bại

![Hình minh chứng 11](CV03-images/hinh-011.png)

### 4.3.8. Kiểm tra chức năng Email và ghi nhận tương tác khách hàng

Trong hệ thống Customer 360, việc lưu trữ lịch sử tương tác là yếu tố quan trọng nhằm hỗ trợ doanh nghiệp hiểu được quá trình liên hệ, tư vấn và chăm sóc khách hàng.

Nhóm tiến hành kiểm tra các chức năng ghi nhận tương tác trong Frappe CRM, bao gồm:

Email trao đổi với khách hàng.

Ghi chú (Notes).

Nhiệm vụ cần thực hiện (Tasks).

Lịch sử cuộc gọi (Call Logs).

Trong quá trình thử nghiệm, nhóm đã thực hiện thao tác gửi email và ghi nhận phản hồi trong dữ liệu CRM demo, đồng thời bổ sung ghi chú, nhiệm vụ và lịch sử cuộc gọi cho Deal.

Những thông tin này hỗ trợ nhân viên theo dõi các hoạt động đã thực hiện với khách hàng, tạo nền tảng để xây dựng góc nhìn Customer 360.

Đối với cấu hình Email Account và kết nối dịch vụ email bên ngoài, nhóm cần phân biệt giữa khả năng thao tác email trên giao diện và việc xác nhận tích hợp email thực tế. Chỉ những cấu hình đã kiểm tra thành công mới được ghi nhận là hoàn tất.

Hình 4.15. Giao diện ghi nhận email và lịch sử tương tác trên Deal

![Hình minh chứng 12](CV03-images/hinh-012.png)

### 4.3.9. Thiết kế Print Format cho báo giá sản phẩm

Để hỗ trợ nghiệp vụ tư vấn bán hàng, nhóm tiến hành thiết kế mẫu biểu báo giá sản phẩm trong Frappe Framework.

Print Format được xây dựng cho đối tượng CRM Deal với tên:

CellphoneS - Bao Gia San Pham

Mục đích của mẫu biểu là trình bày thông tin cơ hội bán hàng và sản phẩm được tư vấn dưới định dạng có cấu trúc, hỗ trợ nhân viên xem hoặc in thông tin báo giá khi cần thiết.

Các nhóm thông tin được xem xét đưa vào mẫu bao gồm:

Thông tin khách hàng.

Thông tin sản phẩm được tư vấn.

Giá bán và đơn vị tiền tệ.

Thông tin cơ hội bán hàng.

Nội dung ghi chú hoặc điều kiện báo giá.

Nhóm kiểm tra khả năng hiển thị mẫu Print Format với dữ liệu Deal thử nghiệm và điều chỉnh các trường dữ liệu theo khả năng hỗ trợ của hệ thống.

Hình 4.16. Giao diện thiết kế Print Format cho CRM Deal

![Hình minh chứng 13](CV03-images/hinh-013.png)

![Hình minh chứng 14](CV03-images/hinh-014.png)

Hình 4.17. Kết quả hiển thị mẫu báo giá CellphoneS

![Hình minh chứng 15](CV03-images/hinh-015.png)

### 4.3.10. Kiểm thử cấu hình hệ thống

Sau khi hoàn thành các thiết lập chính, nhóm tiến hành kiểm thử trên dữ liệu giả lập để đánh giá khả năng sử dụng các chức năng CRM trong tình huống kinh doanh của CellphoneS.

Một trường hợp thử nghiệm được xây dựng với khách hàng Nguyễn Minh Anh có nhu cầu mua sản phẩm iPhone 15 128GB, giá bán giả lập 19.990.000 đồng.

Thông tin cơ hội bán hàng được ghi nhận trong hệ thống với mã:

CRM-DEAL-2026-00001

Nhóm sử dụng dữ liệu này để kiểm tra việc tạo và cập nhật Deal, ghi nhận tương tác, quản lý công việc và hiển thị thông tin báo giá.

Bên cạnh đó, một Deal thử nghiệm khác được sử dụng để kiểm tra thao tác đánh dấu Lost và lựa chọn nguyên nhân thất bại.

Bảng tổng hợp các trường hợp kiểm thử:

| STT | Nội dung kiểm thử | Kết quả mong đợi | Tình trạng ghi nhận |
| --- | --- | --- | --- |
| 1 | Đăng nhập bằng tài khoản Administrator | Truy cập được hệ thống | Đã thực hiện |
| 2 | Tạo tài khoản Sales Manager và Sales User | Tài khoản được lưu trên hệ thống | Đã thực hiện |
| 3 | Gán Role và kiểm tra quyền truy cập | Quyền phù hợp với vai trò | Cần đối chiếu kết quả kiểm thử từng quyền |
| 4 | Gán Lead/Deal cho nhân viên | Hiển thị người phụ trách | Cần đối chiếu ảnh minh chứng |
| 5 | Tạo và cập nhật Deal | Deal được lưu và cập nhật thông tin | Đã thực hiện |
| 6 | Đánh dấu Deal Lost | Lưu trạng thái và Lost Reason | Đã thực hiện |
| 7 | Ghi nhận email, ghi chú, nhiệm vụ và cuộc gọi | Hiển thị lịch sử tương tác | Đã thực hiện thao tác demo |
| 8 | Hiển thị Print Format | Mẫu báo giá hiển thị thông tin phù hợp | Cần kiểm tra các trường dữ liệu |

Kết quả kiểm thử bước đầu cho thấy các chức năng quản lý cơ hội bán hàng và ghi nhận tương tác có thể được sử dụng trong môi trường CRM demo. Các nội dung liên quan đến phân quyền chi tiết, tích hợp email thực tế và hiển thị đầy đủ trường dữ liệu cần được xác nhận trước khi kết luận hoàn tất.

[Hình 4.18. Dữ liệu Deal thử nghiệm trên hệ thống]

### 4.3.11. Kết quả thực hiện

Thông qua công việc cấu hình Frappe CRM, nhóm đã xây dựng môi trường thử nghiệm phục vụ bài toán quản lý khách hàng tại CellphoneS, với các thành phần chính gồm người dùng, vai trò nghiệp vụ, Sales Team, trạng thái Lead, Deal Pipeline, Lost Reasons và các chức năng hỗ trợ ghi nhận tương tác.

Các cấu hình này tạo nền tảng cho việc quản lý khách hàng tiềm năng, theo dõi cơ hội bán hàng và lưu trữ lịch sử tương tác của khách hàng.

Đối với mục tiêu Customer 360, đây là bước chuẩn bị quan trọng nhằm hình thành dữ liệu CRM tập trung. Tuy nhiên, việc cấu hình các chức năng CRM cơ bản chưa đồng nghĩa với việc hoàn thành toàn bộ hệ thống Customer 360. Các chức năng tổng hợp dữ liệu khách hàng đa kênh, tích hợp dữ liệu giao dịch và xây dựng hồ sơ khách hàng thống nhất sẽ tiếp tục được triển khai trong những công việc tiếp theo của đồ án.

![Hình minh chứng 16](CV03-images/hinh-016.png)

![Hình minh chứng 17](CV03-images/hinh-017.png)

![Hình minh chứng 18](CV03-images/hinh-018.png)

![Hình minh chứng 19](CV03-images/hinh-019.png)

![Hình minh chứng 20](CV03-images/hinh-020.png)

![Hình minh chứng 21](CV03-images/hinh-021.png)

![Hình minh chứng 22](CV03-images/hinh-022.png)

![Hình minh chứng 23](CV03-images/hinh-023.png)

![Hình minh chứng 24](CV03-images/hinh-024.png)

![Hình minh chứng 25](CV03-images/hinh-025.png)

![Hình minh chứng 26](CV03-images/hinh-026.png)

![Hình minh chứng 27](CV03-images/hinh-027.png)

![Hình minh chứng 28](CV03-images/hinh-028.png)

![Hình minh chứng 29](CV03-images/hinh-029.png)
