import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button";
import { displayDateTime, REQUEST_STATUS_LABELS } from "../../utils/customer360";

import TicketStatus from "./TicketStatus";

const ticketStatusLabels = { ...REQUEST_STATUS_LABELS, Pending: "Đang chờ" };

export default function AfterSalesDetail({ ticket, onUpdate, canEdit = false }) {
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const submitLock = useRef(false);

  async function submit(event) {
    event.preventDefault();
    if (submitLock.current) return;
    const resolution = draft.resolution.trim();
    if (["Resolved", "Closed"].includes(draft.status) && !resolution) {
      setError("Vui lòng nhập nội dung xử lý.");
      return;
    }

    submitLock.current = true;
    setSaving(true);
    setError("");
    try {
      await onUpdate(ticket.id, { ...draft, resolution });
      setDraft(null);
    } catch (error) {
      setError(error.message);
    } finally {
      submitLock.current = false;
      setSaving(false);
    }
  }

  const fields = [
    ["Khách hàng", ticket.customer && <Link className="text-primary hover:underline" to={`/customers/${encodeURIComponent(ticket.customer)}`}>{ticket.customerName || ticket.customer}</Link>],
    ["Đơn hàng", ticket.relatedOrder],
    ["Tiêu đề", ticket.subject],
    ["Loại yêu cầu", ticket.type],
    ["Trạng thái", <TicketStatus status={ticket.status} />],
    ["Mức ưu tiên", ticket.priority],
    ["Phụ trách", ticket.assignedTo],
    ["Ngày tạo", displayDateTime(ticket.createdAt)],
    ["Cập nhật", displayDateTime(ticket.modifiedAt)],
    ["Giải quyết lúc", displayDateTime(ticket.resolvedAt)],
    ["Nội dung", ticket.description],
    ["Nội dung xử lý", ticket.resolution],
  ];

  return (
    <div className="space-y-5">
      <dl className="grid gap-4 sm:grid-cols-2">
        {fields.map(([label, value]) => (
          <div className="min-w-0" key={label}>
            <dt className="text-sm text-muted">{label}</dt>
            <dd className="whitespace-pre-wrap break-words font-medium">{value || "—"}</dd>
          </div>
        ))}
      </dl>
      {canEdit && !draft && (
        <Button variant="secondary" onClick={() => setDraft({ status: ticket.status, resolution: ticket.resolution ?? "" })}>Cập nhật xử lý</Button>
      )}
      {canEdit && draft && (
        <form className="space-y-3" onSubmit={submit}>
          <fieldset disabled={saving} className="space-y-3">
            <label className="block text-sm font-medium">
              Trạng thái xử lý
              <select className="crm-input" value={draft.status} onChange={(event) => setDraft({ ...draft, status: event.target.value })}>
                {Object.entries(ticketStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
            <label className="block text-sm font-medium">
              Nội dung xử lý
              <textarea className="crm-input" rows={3} value={draft.resolution} onChange={(event) => setDraft({ ...draft, resolution: event.target.value })} />
            </label>
          </fieldset>
          {error && <p role="alert" className="text-sm text-primary">{error}</p>}
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="secondary" disabled={saving} onClick={() => { setDraft(null); setError(""); }}>Hủy</Button>
            <Button type="submit" loading={saving}>Lưu thay đổi</Button>
          </div>
        </form>
      )}
    </div>
  );
}
