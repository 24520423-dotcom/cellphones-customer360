import { DataTable, EmptyState, Panel } from "./CustomerStates";
import {
  daysSince, displayDate, INSIGHT_RULES, isOpenRequest, REQUEST_CATEGORY_LABELS, REQUEST_STATUS_LABELS,
} from "../../utils/customer360";

// L02 – Chăm sóc sau bán: CHỈ HIỂN THỊ. Tạo/cập nhật yêu cầu thuộc L04 After-sales.
// Nguồn: after_sales_requests trong get_customer_profile (PROPOSED; DocType chờ chốt D06).

function RequestStatus({ request }) {
  const open = isOpenRequest(request);
  const age = open ? daysSince(request.created_at) : null;
  const overdue = age !== null && age > INSIGHT_RULES.REQUEST_SLA_DAYS;
  return (
    <span className="inline-flex flex-col items-start gap-0.5">
      <span className={`whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${
        open ? "bg-amber-100 text-amber-900" : "bg-gray-100 text-ink"}`}>
        {REQUEST_STATUS_LABELS[request.status] || request.status || "—"}
      </span>
      {open && age !== null && (
        <span className={`text-xs ${overdue ? "font-medium text-primary" : "text-muted"}`}>Mở {age} ngày</span>
      )}
    </span>
  );
}

const columns = [
  { key: "request_id", label: "Mã yêu cầu", render: (value) => <span className="font-mono text-xs">{value}</span> },
  { key: "category", label: "Loại", render: (value) => REQUEST_CATEGORY_LABELS[value] || value || "—" },
  { key: "subject", label: "Nội dung" },
  { key: "status", label: "Trạng thái", render: (_value, row) => <RequestStatus request={row} /> },
  { key: "assigned_to", label: "Phụ trách", render: (value) => <span className="break-all text-xs">{value || "Chưa phân công"}</span> },
  { key: "created_at", label: "Ngày tạo", render: (value) => displayDate(value) },
];

export default function CustomerSupport({ requests = [] }) {
  const sorted = [...requests].sort((a, b) => Number(isOpenRequest(b)) - Number(isOpenRequest(a))
    || String(b.created_at || "").localeCompare(String(a.created_at || "")));
  return (
    <Panel id="support-title" title="Yêu cầu sau bán" count={requests.length}>
      {requests.length ? (
        <DataTable caption="Yêu cầu chăm sóc sau bán của khách hàng" columns={columns} rows={sorted} getKey={(r) => r.request_id} />
      ) : <EmptyState compact title="Chưa có yêu cầu chăm sóc sau bán" />}
    </Panel>
  );
}

export function OpenRequestsSummary({ requests = [], onShowAll }) {
  const open = requests.filter(isOpenRequest);
  return (
    <Panel id="open-requests-title" title="Hỗ trợ đang mở" count={open.length}
      action={<button type="button" onClick={onShowAll} className="text-xs font-medium text-primary hover:underline">Xem tất cả</button>}>
      {open.length ? (
        <ul className="divide-y divide-gray-100">
          {open.map((request) => (
            <li key={request.request_id} className="space-y-1 px-5 py-3">
              <p className="text-sm text-ink">{request.subject}</p>
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                <span>{REQUEST_CATEGORY_LABELS[request.category] || request.category}</span>
                <span aria-hidden="true">·</span>
                <RequestStatus request={request} />
              </div>
            </li>
          ))}
        </ul>
      ) : <p className="px-5 py-4 text-sm text-muted">Không có yêu cầu đang mở.</p>}
    </Panel>
  );
}
