
import { useEffect, useState } from "react";
import Input from "../../components/Input";
import Button from "../../components/Button";

const leadStatuses = [
  "Mới",
  "Đang tư vấn",
  "Đã liên hệ",
  "Đã chuyển đổi",
  "Không tiềm năng",
];

const empty = {
  name: "",
  phone: "",
  email: "",
  source: "Website",
  status: "Mới",
  owner: "",
  notes: "",
};

export default function LeadForm({
  initialValue,
  onSave,
  onCancel,
}) {
  const [form, setForm] = useState({
    ...empty,
    ...initialValue,
  });

  const [error, setError] = useState("");

  useEffect(() => {
    setForm({
      ...empty,
      ...initialValue,
    });
    setError("");
  }, [initialValue]);

  const update = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    setError("");
  };

  const submit = (e) => {
    e.preventDefault();

    if (!form.name.trim()) {
      setError("Vui lòng nhập họ tên khách hàng.");
      return;
    }

    if (!/^[0-9+().\s-]{9,16}$/.test(form.phone)) {
      setError("Số điện thoại chưa hợp lệ.");
      return;
    }

    if (
      form.email &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
    ) {
      setError("Email không đúng định dạng.");
      return;
    }

    setError("");

    // Gửi dữ liệu cho component cha (Frontend).
    // Chưa gọi API hay lưu vào Backend.
    onSave?.({
      ...form,
      name: form.name.trim(),
    });
  };

  return (
    <form onSubmit={submit} className="grid gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Họ tên khách hàng"
          name="name"
          value={form.name}
          onChange={update}
          placeholder="Nhập họ tên khách hàng"
          required
        />

        <Input
          label="Số điện thoại"
          name="phone"
          type="tel"
          value={form.phone}
          onChange={update}
          placeholder="Nhập số điện thoại"
          required
        />

        <Input
          label="Email"
          name="email"
          type="email"
          value={form.email}
          onChange={update}
          placeholder="Nhập email"
        />

        <Input
          label="Nhân viên phụ trách"
          name="owner"
          value={form.owner}
          onChange={update}
          placeholder="Nhập tên nhân viên"
        />

        <label className="grid gap-2 text-sm font-medium">
          Nguồn Lead
          <select
            name="source"
            value={form.source}
            onChange={update}
            className="crm-input"
          >
            <option value="Website">Website</option>
            <option value="Facebook">Facebook</option>
            <option value="Hotline">Hotline</option>
            <option value="Cửa hàng">Cửa hàng</option>
            <option value="Khác">Khác</option>
          </select>
        </label>

        <label className="grid gap-2 text-sm font-medium">
          Trạng thái
          <select
            name="status"
            value={form.status}
            onChange={update}
            className="crm-input"
          >
            {leadStatuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="grid gap-2 text-sm font-medium">
        Ghi chú
        <textarea
          name="notes"
          value={form.notes}
          onChange={update}
          rows={3}
          className="crm-input"
          placeholder="Nhu cầu, sản phẩm quan tâm..."
        />
      </label>

      {error && (
        <p
          role="alert"
          className="text-sm font-medium text-primary"
        >
          {error}
        </p>
      )}

      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
        >
          Hủy
        </Button>

        <Button type="submit">
          {initialValue ? "Lưu thay đổi" : "Thêm Lead"}
        </Button>
      </div>
    </form>
  );
}
