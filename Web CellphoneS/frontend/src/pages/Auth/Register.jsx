
import { useState } from "react";
import { Link } from "react-router-dom";
import Input from "../../components/Input";
import Button from "../../components/Button";
import StatusPage from "../StatusPage";

export default function Register() {
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!form.fullName.trim() || !form.email.trim() ||
        !form.password || !form.confirmPassword) {
      setError("Vui lòng nhập đầy đủ thông tin.");
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError("Email không đúng định dạng.");
      return;
    }

    if (form.password.length < 8) {
      setError("Mật khẩu phải có ít nhất 8 ký tự.");
      return;
    }

    if (form.password !== form.confirmPassword) {
      setError("Mật khẩu xác nhận không khớp.");
      return;
    }

    setError("");
    setSuccess(
      "Thông tin hợp lệ! Chức năng đăng ký sẽ được kết nối sau."
    );
  };

  return (
    <StatusPage title="Đăng ký tài khoản nhân viên">
      <p className="mb-5 text-sm text-muted">
        CellphoneS Customer 360 · Cổng quản trị nhân viên
      </p>

      <form onSubmit={handleSubmit} className="grid gap-4 text-left">
        <Input
          label="Họ và tên"
          name="fullName"
          value={form.fullName}
          onChange={handleChange}
          placeholder="Nhập họ và tên"
        />

        <Input
          label="Email"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          placeholder="Nhập email nhân viên"
        />

        <Input
          label="Mật khẩu"
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          placeholder="Nhập mật khẩu"
        />

        <Input
          label="Xác nhận mật khẩu"
          name="confirmPassword"
          type="password"
          value={form.confirmPassword}
          onChange={handleChange}
          placeholder="Nhập lại mật khẩu"
        />

        {error && (
          <p role="alert" className="text-sm font-medium text-red-600">
            {error}
          </p>
        )}

        {success && (
          <p role="status" className="text-sm font-medium text-green-600">
            {success}
          </p>
        )}

        <Button type="submit">
          Đăng ký
        </Button>

        <p className="text-center text-sm">
          Đã có tài khoản?{" "}
          <Link
            to="/login"
            className="font-semibold text-primary"
          >
            Đăng nhập
          </Link>
        </p>
      </form>
    </StatusPage>
  );
}
