import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import AuthProvider from "./pages/Auth/AuthProvider";
import Login from "./pages/Auth/Login";
import Dashboard from "./pages/Dashboard/Dashboard";
import NotFound from "./pages/NotFound";
import { crmRoutes } from "./routes/crmRoutes";
import ProtectedRoute from "./routes/ProtectedRoute";
import Register from "./pages/Auth/Register";
import PendingApproval from "./pages/Auth/PendingApproval";
import LeadList from "./pages/Leads/LeadList";
import DealList from "./pages/Deals/DealList";
import CustomerList from "./pages/Customers/CustomerList";
import CustomerEditor from "./pages/Customers/CustomerEditor";
import CustomerProfile from "./pages/Customers/CustomerProfile";
import AfterSales from "./pages/AfterSales/AfterSales";
import AfterSalesTicketPage from "./pages/AfterSales/AfterSalesTicketPage";
import Analytics from "./pages/Analytics/Analytics";
import Administration from "./pages/Administration/Administration";
import CustomerPreviewFrame from "./pages/Customers/CustomerPreviewFrame";

// Trang hồ sơ dùng cùng quyền với trang danh sách /customers.
const customersPermission = crmRoutes.find(({ path }) => path === "/customers")?.permission;
export default function App({ authAdapter }) {
  return (
    <BrowserRouter>
      <AuthProvider adapter={authAdapter}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/pending-approval" element={<PendingApproval />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              {crmRoutes.map(({ path, permission }) => {
                const page =
                  path === "/dashboard" ? (
                    <Dashboard />
                  ) : path === "/leads" ? (
                    <LeadList />
                  ) : path === "/deals" ? (
                    <DealList />
                  ) : path === "/after-sales" ? (
                    <AfterSales />
                  ) : path === "/analytics" ? (
                    <Analytics />
                  ) : path === "/customers" ? (
                    <CustomerList />
                  ) : (
                    <Administration />
                  );
                return permission ? (
                  <Route key={path} element={<ProtectedRoute permission={permission} />}>
                    <Route path={path} element={page} />
                  </Route>
                ) : <Route key={path} path={path} element={page} />;
              })}
              <Route path="/after-sales/:ticketId" element={<AfterSalesTicketPage />} />
              <Route element={<ProtectedRoute permission={customersPermission} />}>
                <Route path="/customers/new" element={<CustomerEditor />} />
                <Route path="/customers/:customerId/edit" element={<CustomerEditor />} />
                <Route path="/customers/:customerId" element={<CustomerProfile />} />
              </Route>
            </Route>
          </Route>
          {/* Chỉ dùng để xem thử giao diện H03 khi chưa có Backend */}
          {import.meta.env.DEV && (
            <Route path="/preview/leads" element={<LeadList />} />
          )}
          {/* Xem trước giao diện Deal khi chưa đăng nhập, chỉ trong DEV */}
          {import.meta.env.DEV && (
            <Route path="/preview/deals" element={<DealList preview />} />
          )}
          {/* Xem thử L01/L02 không cần Frappe, chỉ khi chạy dev. */}
          {import.meta.env.DEV && (
            <Route path="/preview/customers" element={<CustomerPreviewFrame />}>
              <Route index element={<CustomerList />} />
              <Route path=":customerId" element={<CustomerProfile />} />
            </Route>
          )}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
