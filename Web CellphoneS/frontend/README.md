# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Chạy frontend CRM

Với site Frappe local trong API Contract, đặt cấu hình sau trong tệp .env.local của frontend rồi chạy npm run dev.

    FRAPPE_PROXY_TARGET=http://crm.localhost:8000

Vite chuyển tiếp /api đến site Frappe. Khi triển khai, ưu tiên reverse proxy cùng origin, chuyển tiếp /api đến Frappe và trả index.html cho các URL frontend khi tải trực tiếp. Nếu frontend gọi Frappe khác origin, đặt VITE_FRAPPE_API_ORIGIN và cấu hình CORS, cookie và CSRF trên môi trường triển khai.

Các đường dẫn frontend dự kiến gồm /login, /dashboard, /leads, /deals, /customers, /after-sales, /analytics và /admin. Đường dẫn / chuyển về /dashboard. Đường dẫn còn lại hiển thị 404.

### Tích hợp Auth

Adapter mặc định gửi usr và pwd dưới dạng form tới /api/method/login. Sau đó frontend đọc /api/method/frappe.auth.get_logged_user với cookie phiên để xác nhận danh tính. Cả hai thao tác cần kiểm thử với site Frappe triển khai.

AuthProvider nhận adapter từ App qua prop authAdapter. getSession(signal) trả null khi là khách hoặc { user: { id, displayName? }, permissions: string[] } khi có phiên. Adapter hỗ trợ login(username, password) và có thể thêm logout(). Chỉ cấp quyền administration từ thông tin quyền do backend xác nhận. Adapter hiện tại chỉ có định danh nên trả danh sách quyền rỗng và nút đăng xuất đang chờ tích hợp. Nhóm Auth cần chốt endpoint lấy quyền, trạng thái duyệt tài khoản và luồng CSRF/đăng xuất. Backend chịu trách nhiệm kiểm tra phiên, trạng thái duyệt và quyền ở từng endpoint.

Dashboard hiển thị dữ liệu minh họa hiện có. Các module còn lại chỉ có trang giữ chỗ.
