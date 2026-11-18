import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import Loading from "../components/Loading";
import { useAuth } from "../hooks/useAuth";
import SessionError from "../pages/Auth/SessionError";
import StatusPage from "../pages/StatusPage";

export default function ProtectedRoute({ permission }) {
  const { status, hasPermission } = useAuth();
  const { pathname, search, hash } = useLocation();

  if (status === "loading") return <Loading />;
  if (status === "error") return <SessionError />;
  if (status !== "authenticated") {
    return <Navigate to="/login" state={{ from: pathname + search + hash }} replace />;
  }
  if (permission && !hasPermission(permission)) {
    return (
      <StatusPage embedded code="403" title="Bạn không có quyền truy cập trang này.">
        <Link className="crm-action" to="/dashboard">Quay về Dashboard</Link>
      </StatusPage>
    );
  }

  return <Outlet />;
}
