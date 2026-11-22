import { useRef, useState } from "react";
import { Info } from "lucide-react";
import Button from "../../components/Button";
import Input from "../../components/Input";
import { STATUS_LABELS } from "./dealUtils";

const EMPTY_DEAL = {
  title: "", lead: "", status: "Qualification", expected_deal_value: "",
  deal_value: "", closed_date: "", ownerDisplay: "", notes: "",
};

function initialForm(deal, firstStage) {
  if (!deal) return { ...EMPTY_DEAL, status: firstStage ?? "" };
  return {
    ...EMPTY_DEAL, ...deal,
    expected_deal_value: deal.expected_deal_value ?? "",
    deal_value: deal.deal_value ?? "",
    closed_date: deal.closed_date ?? "",
  };
}

export default function DealForm({ initialValue = null, statuses, preview, onSave, onCancel }) {
  const [form, setForm] = useState(() => initialForm(initialValue, statuses[0]));
  const [error, setError] = useState("");

  const [saving, setSaving] = useState(false);
  const submitLock = useRef(false);

  function update(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
    setError("");
  }

  async function submit(event) {
    event.preventDefault();
    if (submitLock.current) return;
    if (!statuses.includes(form.status)) {
      setError("Giai đoạn Deal không hợp lệ.");
      return;
    }
    for (const field of ["deal_value", "expected_deal_value"]) {
      if (form[field] !== "" && (!Number.isFinite(Number(form[field])) || Number(form[field]) < 0)) {
        setError("Giá trị Deal phải là số không âm.");
        return;
      }
    }
    submitLock.current = true;
    setSaving(true);
    setError("");
    try {
      await onSave({
        ...form,
        title: form.title.trim(),
        lead: form.lead.trim(),
        ownerDisplay: form.ownerDisplay.trim(),
        notes: form.notes.trim(),
        deal_value: form.deal_value === "" ? null : Number(form.deal_value),
        expected_deal_value: form.expected_deal_value === "" ? null : Number(form.expected_deal_value),
      });
    } catch (error) {
      setError(error.message);
    } finally {
      submitLock.current = false;
      setSaving(false);
    }
  }

  return (
    <form className="deal-form" onSubmit={submit}>
      {preview && <div className="deal-form-note"><Info size={17} /><span>Giao diện xem trước K02. Thông tin chỉ được giữ tạm trong trình duyệt, chưa ghi vào Frappe.</span></div>}
      {initialValue?.name && <div className="deal-form-id"><span>Mã Deal</span><strong>{initialValue.name}</strong></div>}
      <h3>Thông tin cơ hội</h3>
      <Input label="Tên tổ chức" name="title" value={form.title} onChange={update} placeholder="Ví dụ: Tư vấn điện thoại cho khách A" />
      <div className="deal-form-grid">
        <Input label="Mã Lead liên quan" name="lead" value={form.lead} onChange={update} placeholder="CRM-LEAD-... hoặc để trống" />
        <label className="deal-form-select">Giai đoạn Pipeline
          <select name="status" className="crm-input" value={form.status} onChange={update}>
            {statuses.map((status) => <option key={status} value={status}>{STATUS_LABELS[status] || status}</option>)}
          </select>
        </label>
      </div>
      <h3>Giá trị & phụ trách ({form.currency || "VND"})</h3>
      <div className="deal-form-grid">
        <Input label="Giá trị dự kiến" name="expected_deal_value" type="number" min="0" step="1" value={form.expected_deal_value} onChange={update} placeholder="0" />
        <Input label="Giá trị Deal" name="deal_value" type="number" min="0" step="1" value={form.deal_value} onChange={update} placeholder="0" helperText="Không đồng nghĩa doanh thu đã thanh toán." />
        <Input label="Ngày đóng Deal (nếu có)" name="closed_date" type="date" value={form.closed_date} onChange={update} />
        <Input label="Tài khoản nhân viên" name="ownerDisplay" value={form.ownerDisplay} onChange={update} placeholder="Nhân viên phụ trách" />
      </div>
      <label className="deal-form-notes">Bước tiếp theo
        <textarea className="crm-input" name="notes" value={form.notes} onChange={update} rows={3} placeholder="Thông tin thêm về cơ hội bán hàng..." />
      </label>
      {error && <p className="deal-form-error" role="alert">{error}</p>}
      <div className="deal-form-actions">
        <Button variant="secondary" type="button" onClick={onCancel} disabled={saving}>Hủy</Button>
        <Button type="submit" loading={saving}>{initialValue ? "Lưu thay đổi" : "Tạo Deal mới"}</Button>
      </div>
    </form>
  );
}
