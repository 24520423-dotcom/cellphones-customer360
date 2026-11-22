import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Input from "../../components/Input";
import Button from "../../components/Button";
import StatusPage from "../StatusPage";
import { submitRegistration } from "../../services/registrationService";

const departments = [
  ["Sales", "Kinh doanh"],
  ["Customer Service", "Chăm sóc khách hàng"],
  ["Operations", "Vận hành"],
  ["Other", "Khác"],
];

export default function Register() {
  const navigate = useNavigate();
  const lock = useRef(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (lock.current) return;
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    lock.current = true;
    setSubmitting(true);
    setError("");
    try {
      await submitRegistration(payload);
      navigate("/pending-approval", { replace: true });
    } catch (error) {
      setError(error.status === 429
        ? "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau 10 phút."
        : "Không gửi được yêu cầu. Vui lòng kiểm tra thông tin và thử lại.");
    } finally {
      lock.current = false;
      setSubmitting(false);
    }
  }

  return (
    <StatusPage title="Đăng ký tài khoản nhân viên">
      <form onSubmit={handleSubmit} className="grid gap-4 text-left">
        <Input label="Họ và tên" name="full_name" autoComplete="name" required minLength={2} maxLength={140} />
        <Input label="Email" name="email" type="email" autoComplete="email" required maxLength={140} />
        <Input label="Số điện thoại" name="phone" type="tel" autoComplete="tel" required maxLength={40} />
        <label className="grid gap-1 text-sm font-medium">
          Bộ phận mong muốn
          <select name="department" className="crm-input" defaultValue="" required>
            <option value="" disabled>Chọn bộ phận</option>
            {departments.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <div className="absolute h-px w-px overflow-hidden opacity-0" aria-hidden="true">
          <label>Website <input name="website" tabIndex={-1} autoComplete="off" /></label>
        </div>
        {error && <p role="alert" className="text-sm text-primary">{error}</p>}
        <Button type="submit" loading={submitting}>Gửi yêu cầu đăng ký</Button>
        <Link className="text-center text-sm font-semibold text-primary hover:underline" to="/login">Quay lại đăng nhập</Link>
      </form>
    </StatusPage>
  );
}
