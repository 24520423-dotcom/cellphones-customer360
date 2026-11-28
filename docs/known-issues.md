# Các mục còn cần xác nhận

- **Role và Role Profile trên site hiện có.** Migration thay đổi quyền đang chờ xác nhận của chủ site. Mã cấu hình, ma trận và bộ test đã chuẩn bị. [Ma trận quyền](design/permission-matrix.md)
- **Đồng bộ GitHub.** Có commit cục bộ ở cả hai phạm vi Git. Push nhánh Windows đang chờ xác nhận gửi mã và ảnh minh chứng tới remote đã chỉ định. [Git workflow](deployment/git-workflow.md)
- **Triển khai New/Snapshot.** Đợt triển khai dùng site Docker hiện có. Cần chạy cài mới và smoke test trên máy hoặc project được cấp quyền. Snapshot ngày 22/11 phụ thuộc bộ sao lưu riêng của nhóm. [Deployment Guide](deployment/deployment-guide.md)
- **Nguồn dữ liệu và kế toán.** CSV và quy trình sau bán dùng dữ liệu giả lập. Kết nối thật Website, POS, Facebook, Zalo và các dịch vụ thanh toán cần dữ liệu, quyền và hợp đồng tích hợp tương ứng.
- **Thông tin lịch sử và phân khúc.** Đơn cũ thiếu mốc thanh toán không đóng góp KPI tiền thu. RFM dựa trên giao dịch đủ điều kiện trong phạm vi quyền. Nhóm sản phẩm quan tâm cần dữ liệu ý định từ Lead/Deal. [Định nghĩa KPI](design/kpi-definition.md)
