import { useEffect, useRef, useState } from "react";
import Button from "../../components/Button";

const types = ["Warranty", "Return", "Exchange", "Complaint", "Technical Support", "Other"];
const priorities = ["Low", "Medium", "High", "Urgent"];
const initial = { customer: "", relatedOrder: "", subject: "", description: "", type: "Warranty", priority: "Medium" };

export default function AfterSalesForm({ loadCustomers, loadOrders, onSave, onClose }) {
  const [form, setForm] = useState(initial);
  const [customers, setCustomers] = useState({});
  const [orderResult, setOrderResult] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const submitLock = useRef(false);
  const { customer } = form;
  const orders = orderResult.customer === customer ? orderResult.items : undefined;

  useEffect(() => {
    const controller = new AbortController();
    loadCustomers({ signal: controller.signal }).then(
      (items) => { if (!controller.signal.aborted) setCustomers({ items }); },
      (error) => { if (!controller.signal.aborted) setCustomers({ error: error.message }); },
    );
    return () => controller.abort();
  }, [loadCustomers]);

  useEffect(() => {
    if (!customer) return;
    const controller = new AbortController();
    loadOrders(customer, { signal: controller.signal }).then(
      (items) => { if (!controller.signal.aborted) setOrderResult({ customer, items }); },
      (error) => { if (!controller.signal.aborted) setOrderResult({ customer, error: error.message }); },
    );
    return () => controller.abort();
  }, [customer, loadOrders]);

  function change(key, value) {
    setForm((previous) => ({
      ...previous,
      ...(key === "customer" ? { relatedOrder: "" } : {}),
      [key]: value,
    }));
  }

  async function submit(event) {
    event.preventDefault();
    if (submitLock.current) return;
    const subject = form.subject.trim();
    const description = form.description.trim();
    if (!customer || !subject || !description) {
      setError("Vui lòng chọn khách hàng và nhập tiêu đề, nội dung.");
      return;
    }
    if (form.relatedOrder && !orders?.some(({ id }) => id === form.relatedOrder)) {
      setError("Đơn hàng phải thuộc khách hàng đang chọn.");
      return;
    }

    submitLock.current = true;
    setSaving(true);
    setError("");
    try {
      await onSave({ ...form, subject, description, status: "Open" });
    } catch (error) {
      setError(error.message);
    } finally {
      submitLock.current = false;
      setSaving(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={submit}>
      <fieldset disabled={saving} className="grid gap-4 sm:grid-cols-2">
        <label className="min-w-0 text-sm font-medium">
          Khách hàng
          <select className="crm-input" required disabled={!customers.items} value={customer} onChange={(event) => change("customer", event.target.value)}>
            <option value="">{customers.items ? "Chọn khách hàng" : customers.error ? "Không tải được khách hàng" : "Đang tải khách hàng…"}</option>
            {customers.items?.map(({ id, label }) => <option key={id} value={id}>{label}</option>)}
          </select>
        </label>
        <label className="min-w-0 text-sm font-medium">
          Đơn hàng liên quan
          <select className="crm-input" disabled={!orders?.length} value={form.relatedOrder} onChange={(event) => change("relatedOrder", event.target.value)}>
            <option value="">{customer && !orders && !orderResult.error ? "Đang tải đơn hàng…" : "Không chọn đơn hàng"}</option>
            {orders?.map(({ id, label }) => <option key={id} value={id}>{label}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium sm:col-span-2">
          Tiêu đề yêu cầu
          <input className="crm-input" required maxLength={140} value={form.subject} onChange={(event) => change("subject", event.target.value)} />
        </label>
        <label className="text-sm font-medium sm:col-span-2">
          Nội dung yêu cầu
          <textarea className="crm-input" required rows={4} value={form.description} onChange={(event) => change("description", event.target.value)} />
        </label>
        {[["type", "Loại yêu cầu", types], ["priority", "Mức ưu tiên", priorities]].map(([key, label, options]) => (
          <label key={key} className="text-sm font-medium">
            {label}
            <select className="crm-input" required value={form[key]} onChange={(event) => change(key, event.target.value)}>
              {options.map((option) => <option key={option}>{option}</option>)}
            </select>
          </label>
        ))}
      </fieldset>
      {(error || customers.error || (orderResult.customer === customer && orderResult.error)) && (
        <p role="alert" className="text-sm text-primary">{error || customers.error || orderResult.error}</p>
      )}
      <div className="flex flex-wrap justify-end gap-2">
        <Button variant="secondary" disabled={saving} onClick={onClose}>Hủy</Button>
        <Button type="submit" disabled={!customers.items?.length} loading={saving}>Lưu yêu cầu</Button>
      </div>
    </form>
  );
}
