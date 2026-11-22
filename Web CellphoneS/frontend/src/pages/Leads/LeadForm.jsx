
import { useState } from "react";
import Input from "../../components/Input";
import Button from "../../components/Button";

const empty = {
  name: "",
  phone: "",
  email: "",
  source: "",
  status: "New",
  owner: "",
  notes: "",
};

export default function LeadForm({
  initialValue,
  statuses,
  onSave,
  onCancel,
}) {
  const [form, setForm] = useState({
    ...empty,
    status: statuses.includes("New") ? "New" : (statuses[0] ?? ""),
    ...initialValue,
  });

  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const update = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    setError("");
  };


const submit = async (e) => {
  e.preventDefault();

  if (saving) return;

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
  setSaving(true);

  try {
    await onSave({
      ...form,
      name: form.name.trim(),
    });
  } catch (err) {
    setError(err.message || "Không thể lưu Lead.");
  } finally {
    setSaving(false);
  }
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

        <label className="grid gap-2 text-sm font-medium">
          Nhân viên phụ trách
          <select
          name="owner"
          value={form.owner}
          onChange={update}
          className="crm-input"
          >
    <option value="">Chưa phân công</option>
    <option value="Administrator">
      Administrator
    </option>
    <option value="sales.user@cellphones.example">
      Nhân viên bán hàng
    </option>
    <option value="sales.manager@cellphones.example">
      Quản lý kinh doanh
    </option>
  </select>
</label>

        <label className="grid gap-2 text-sm font-medium">
          Nguồn Lead
          <select
            name="source"
            value={form.source}
            onChange={update}
            className="crm-input"
          >
            <option value="">Chưa xác định</option>
            <option value="Website">Website</option>
            <option value="Web Form">Biểu mẫu website</option>
            <option value="Facebook">Facebook</option>
            <option value="Walk In">Khách tại cửa hàng</option>
            <option value="Cold Calling">Tiếp cận qua điện thoại</option>
            <option value="Email">Email</option>
            <option value="Campaign">Chiến dịch Marketing</option>
            <option value="Advertisement">Quảng cáo</option>
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
            {statuses.map((status) => (
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
          disabled={saving}
        >
          Hủy
        </Button>

        <Button type="submit" disabled={saving}>
          {saving
          ? "Đang lưu..."
          : initialValue
          ? "Lưu thay đổi"
          : "Thêm Lead"}
        </Button>
      </div>
    </form>
  );
}
