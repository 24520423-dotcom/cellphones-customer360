import { useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import { useAuth } from "../../hooks/useAuth";
import StatusPage from "../StatusPage";
import SessionError from "./SessionError";

export default function Login() {
  const { status, login } = useAuth();
  const { state } = useLocation();
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  if (status === "loading") return <Loading />;
  if (status === "error") return <SessionError />;
  if (status === "authenticated") {
    const from = state?.from;
    const safeDestination = typeof from === "string" && /^\/(?![/\\])/.test(from);
    return <Navigate to={safeDestination ? from : "/dashboard"} replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");
    setSubmitting(true);
    const data = new FormData(event.currentTarget);
    try {
      await login(data.get("username"), data.get("password"));
      setMessage("Không tìm thấy phiên đăng nhập. Vui lòng thử lại.");
    } catch (error) {
      setMessage([401, 403].includes(error.status)
        ? "Đăng nhập bị từ chối. Vui lòng kiểm tra thông tin tài khoản."
        : "Không thể đăng nhập vào Frappe. Vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <StatusPage title="Đăng nhập">
      <form className="grid gap-4 text-left" onSubmit={handleSubmit}>
        <label className="grid gap-1 text-sm font-medium">
          Tài khoản
          <input className="crm-input" name="username" autoComplete="username" required />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          Mật khẩu
          <input className="crm-input" name="password" type="password" autoComplete="current-password" required />
        </label>
        {message && <p role="alert" className="text-sm text-primary">{message}</p>}
        <Button type="submit" loading={submitting}>Đăng nhập</Button>
      </form>
    </StatusPage>
  );
}
