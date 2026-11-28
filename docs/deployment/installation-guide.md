# Hướng dẫn cài đặt

Docker Desktop cần chạy Linux containers. Repo dùng PowerShell và bind mount từ `backend/cellphones_c360`. Máy triển khai mới cần kết nối tới nguồn phụ thuộc của Frappe, CRM và Yarn.

## Môi trường hiện có

Từ repo gốc, kiểm tra phiên bản và site:

```powershell
.\deployment\cellphones-c360\setup.ps1 -Mode Verify -Container crm-frappe-1 -Site crm.localhost
```

Mở [CRM hiện có](http://crm.localhost:8000/crm). Phần cập nhật dùng [Deployment Guide](deployment-guide.md).

## Máy cài mới được chọn cho đồ án

1. Clone repo, checkout `feature/frappe-crm-native`, rồi vào `deployment/cellphones-c360`.
2. Sao chép `.env.example` thành `.env`, đặt mật khẩu MariaDB riêng và kiểm tra cổng web/socket. `C360_WEB_PORT` mặc định là 8001.
3. Chạy `.\setup.ps1 -Mode New -ProjectName cellphones-c360-source`. Script yêu cầu mật khẩu Administrator khi khởi tạo site và chỉ tiếp tục với project Compose mới.
4. Mở `http://crm.localhost:8001/crm`, đăng nhập và kiểm tra giao diện, nhận diện CellphoneS và các API.
5. Chạy `.\import-demo.ps1 -Container cellphones-c360-source-frappe-1` từ thư mục triển khai để kiểm tra trial. Dùng `-Apply` trên site demo khi cần lưu bộ mẫu.

Môi trường mới chưa được khởi tạo trong đợt này theo phạm vi máy được phép sử dụng. Các công cụ kiểm tra package và site hiện có được ghi trong [Test Report](../testing/test-report.md).
