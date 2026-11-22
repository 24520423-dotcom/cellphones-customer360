import { useEffect, useState } from "react";

import { History, Pencil } from "lucide-react";
import Button from "../../components/Button";
import Table from "../../components/Table";
import { getLeadOptions } from "../../services/leadService";
import { displayDateTime } from "../../utils/customer360";

const columns = [
  { key: "type", label: "Loại" },
  { key: "title", label: "Nội dung" },
  { key: "status", label: "Trạng thái" },
  { key: "date", label: "Thời gian", render: displayDateTime },
];

export default function LeadDetail({ lead, onEdit }) {
  const leadId = lead?.id;
  const [result, setResult] = useState(null);
  useEffect(() => {
    if (!leadId) return;
    const controller = new AbortController();
    getLeadOptions(leadId, { signal: controller.signal }).then(
      (data) => { if (!controller.signal.aborted) setResult({ leadId, data }); },
      (error) => { if (!controller.signal.aborted) setResult({ leadId, error: error.message }); },
    );
    return () => controller.abort();
  }, [leadId]);
  const current = result?.leadId === leadId ? result : null;

  if (!lead) {
    return (
      <p className="text-sm text-muted">
        Không tìm thấy thông tin Lead.
      </p>
    );
  }

  const fields = [
    { label: "Mã Lead", value: lead.id },
    { label: "Họ và tên", value: lead.name },
    { label: "Số điện thoại", value: lead.phone },
    { label: "Email", value: lead.email },
    { label: "Nguồn Lead", value: lead.source },
    { label: "Trạng thái", value: lead.status },
    { label: "Nhân viên phụ trách", value: lead.owner },
    { label: "Ghi chú", value: lead.notes },
  ];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">
          Chi tiết Lead
        </h1>
        <p className="mt-1 text-sm text-muted">
          Thông tin khách hàng tiềm năng
        </p>
      </div>

      {/* Thông tin Lead */}
      <section className="crm-card">
        <h2 className="mb-4 font-semibold text-ink">
          Thông tin Lead
        </h2>

        <dl className="grid gap-3 sm:grid-cols-2">
          {fields.map((field) => (
            <div
              key={field.label}
              className="rounded-lg bg-gray-50 p-3"
            >
              <dt className="text-xs text-muted">
                {field.label}
              </dt>
              <dd className="mt-1 break-words text-sm text-ink">
                {field.value || "—"}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Lịch sử tư vấn */}
      <section className="crm-card">
        <div className="flex items-center gap-2">
          <History size={18} className="text-primary" />
          <h2 className="font-semibold text-ink">
            Lịch sử tư vấn
          </h2>
        </div>

        <div className="mt-4">
          {current?.error ? <p role="alert" className="text-primary">{current.error}</p> : (
            <Table data={current?.data?.history} columns={columns} loading={!current} emptyMessage="Chưa có cuộc gọi hoặc công việc liên kết." />
          )}
        </div>
      </section>

      {current?.data?.canEdit && (
      <div className="flex justify-end">
        <Button type="button" onClick={onEdit}>
        <Pencil size={16} />
        Chỉnh sửa Lead
        </Button>
      </div>
      )}
    </div>
  );
}
