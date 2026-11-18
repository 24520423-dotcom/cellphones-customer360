import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import AuthProvider from "./pages/Auth/AuthProvider";
import Login from "./pages/Auth/Login";
import Dashboard from "./pages/Dashboard/Dashboard";
import NotFound from "./pages/NotFound";
import { crmRoutes } from "./routes/crmRoutes";
import ProtectedRoute from "./routes/ProtectedRoute";

function Placeholder({ title }) {
  return (
    <section className="crm-card">
      <h1 className="text-2xl font-bold text-ink">{title}</h1>
      <p className="mt-2 text-muted">Chức năng đang được phát triển.</p>
    </section>
  );
}

export default function App({ authAdapter }) {
  return (
    <BrowserRouter>
      <AuthProvider adapter={authAdapter}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              {crmRoutes.map(({ path, label, permission }) => {
                const page = path === "/dashboard" ? <Dashboard /> : <Placeholder title={label} />;
                return permission ? (
                  <Route key={path} element={<ProtectedRoute permission={permission} />}>
                    <Route path={path} element={page} />
                  </Route>
                ) : <Route key={path} path={path} element={page} />;
              })}
            </Route>
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
