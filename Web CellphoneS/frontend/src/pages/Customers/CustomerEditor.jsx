import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import { getCustomerAccess, getCustomerRecord, saveCustomerRecord } from "../../services/customerService";

const fields = [
  { key: "customer_name", label: "Họ tên khách hàng", required: true },
  { key: "phone_number", label: "Số điện thoại", type: "tel" },
  { key: "email", label: "Email", type: "email" },
  { key: "customer_type", label: "Loại khách hàng", required: true, options: [["Individual", "Cá nhân"], ["Business", "Doanh nghiệp"]] },
  { key: "customer_status", label: "Trạng thái", required: true, options: [["Active", "Đang hoạt động"], ["Inactive", "Ngừng hoạt động"]] },
  { key: "source_channel", label: "Kênh nguồn", options: ["", "Website", "App", "Facebook", "Zalo", "Hotline", "Store", "Other"].map((value) => [value, value || "Chưa chọn"]) },
];
const defaults = { customer_type: "Individual", customer_status: "Active" };

export default function CustomerEditor() {
  const { customerId } = useParams();
  const back = customerId ? `/customers/${encodeURIComponent(customerId)}` : "/customers";
  return <Editor key={customerId || "new"} customerId={customerId} back={back} />;
}

function Editor({ customerId, back }) {
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [form, setForm] = useState(defaults);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const submitting = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    async function load() {
      try {
        const access = await getCustomerAccess(customerId, options);
        if (controller.signal.aborted) return;
        const allowed = customerId ? access.canEdit : access.canCreate;
        if (!allowed) {
          setResult({ error: "Bạn không có quyền thực hiện thao tác này." });
          return;
        }
        const data = customerId ? await getCustomerRecord(customerId, options) : defaults;
        if (controller.signal.aborted) return;
        setForm(Object.fromEntries(fields.map(({ key }) => [key, data[key] ?? ""])));
        setResult({ ready: true });
      } catch (error) {
        if (!controller.signal.aborted) setResult({ error: error.message });
      }
    }
    load();
    return () => controller.abort();
  }, [customerId]);

  async function submit(event) {
    event.preventDefault();
    if (submitting.current) return;
    const payload = Object.fromEntries(fields.map(({ key }) => [key, form[key]?.trim() || null]));
    if (!payload.customer_name) {
      setError("Vui lòng nhập tên khách hàng.");
      return;
    }
    submitting.current = true;
    setSaving(true);
    setError("");
    try {
      const record = await saveCustomerRecord(customerId, payload);
      navigate(`/customers/${encodeURIComponent(record.name)}`, { replace: true, state: { notice: "Đã lưu hồ sơ khách hàng." } });
    } catch (error) {
      setError(error.message);
    } finally {
      setSaving(false);
      submitting.current = false;
    }
  }

  return (
    <section className="crm-card space-y-4">
      <Link to={back} className="text-sm text-primary hover:underline">Quay lại</Link>
      <h1 className="text-2xl font-bold">{customerId ? "Chỉnh sửa hồ sơ khách hàng" : "Thêm khách hàng"}</h1>
      {!result && <Loading label="Đang tải thông tin khách hàng…" />}
      {(result?.error || error) && <p role="alert" className="text-sm text-primary">{result?.error || error}</p>}
      {result?.ready && (
        <form onSubmit={submit} className="space-y-4">
          <fieldset disabled={saving} className="grid gap-4 sm:grid-cols-2">
            {fields.map(({ key, label, required, type, options }) => {
              const props = {
                className: "crm-input",
                value: form[key] ?? "",
                required,
                onChange: (event) => setForm((previous) => ({ ...previous, [key]: event.target.value })),
              };
              return (
                <label key={key} className="min-w-0 text-sm font-medium">
                  {label}
                  {options ? <select {...props}>{options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select> : <input {...props} type={type || "text"} maxLength={140} />}
                </label>
              );
            })}
          </fieldset>
          <Button type="submit" loading={saving}>Lưu hồ sơ</Button>
        </form>
      )}
    </section>
  );
}
