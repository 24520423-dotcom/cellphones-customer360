import { DataTable, EmptyState, Panel } from "./CustomerStates";
import { formatVnd, STATUS_LABELS, statusClass } from "../../pages/Deals/dealUtils";
import { displayDate, isOpenDeal, LEAD_STATUS_LABELS } from "../../utils/customer360";

// L02 – Lead & Deal liên quan.
// Nhãn/màu trạng thái Deal dùng lại pages/Deals/dealUtils.js (module Deal) để đồng bộ toàn app.
// deal_value KHÔNG được trình bày như doanh thu (API Contract §5).

function DealStatus({ status }) {
  return (
    <span className={`inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${statusClass(status)}`}>
      {STATUS_LABELS[status] || status || "—"}
    </span>
  );
}

function LeadStatus({ status }) {
  return (
    <span className="inline-block whitespace-nowrap rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-ink">
      {LEAD_STATUS_LABELS[status] || status || "—"}
    </span>
  );
}

const dealColumns = [
  { key: "name", label: "Mã Deal", render: (value) => <span className="font-mono text-xs">{value}</span> },
  { key: "status", label: "Giai đoạn", render: (value) => <DealStatus status={value} /> },
  { key: "expected_deal_value", label: "Giá trị dự kiến", render: (value) => <span className="whitespace-nowrap">{formatVnd(value)}</span> },
  { key: "lead", label: "Lead liên kết", render: (value) => value
    ? <span className="font-mono text-xs">{value}</span>
    : <span className="text-xs text-amber-800">Chưa liên kết</span> },
  { key: "creation", label: "Ngày tạo", render: (value) => displayDate(value) },
  { key: "closed_date", label: "Ngày đóng", render: (value) => displayDate(value) },
];

const leadColumns = [
  { key: "name", label: "Mã Lead", render: (value) => <span className="font-mono text-xs">{value}</span> },
  { key: "status", label: "Trạng thái", render: (value) => <LeadStatus status={value} /> },
  { key: "source", label: "Nguồn" },
  { key: "lead_owner", label: "Phụ trách", render: (value) => <span className="break-all text-xs">{value || "—"}</span> },
  { key: "creation", label: "Ngày tạo", render: (value) => displayDate(value) },
];

export default function CustomerDeals({ leads = [], deals = [] }) {
  const sortedDeals = [...deals].sort((a, b) => Number(isOpenDeal(b)) - Number(isOpenDeal(a)));
  return (
    <div className="space-y-4">
      <Panel id="deals-title" title="Deal" count={deals.length}>
        {deals.length ? (
          <DataTable caption="Danh sách Deal của khách hàng" columns={dealColumns} rows={sortedDeals} getKey={(d) => d.name} />
        ) : <EmptyState compact title="Chưa có Deal liên kết với khách hàng này" />}
        <p className="border-t border-border px-5 py-2 text-xs text-muted">
          Giá trị dự kiến là ước tính của cơ hội bán, không phải doanh thu hay giá trị đơn hàng.
        </p>
      </Panel>
      <Panel id="leads-title" title="Lead" count={leads.length}>
        {leads.length ? (
          <DataTable caption="Danh sách Lead của khách hàng" columns={leadColumns} rows={leads} getKey={(l) => l.name} />
        ) : <EmptyState compact title="Chưa có Lead liên kết với khách hàng này" />}
      </Panel>
    </div>
  );
}

// Tóm tắt cho cột "Đang mở" ở tab Tổng quan.
export function OpenDealsSummary({ leads = [], deals = [], onShowAll }) {
  const open = deals.filter(isOpenDeal);
  return (
    <Panel id="open-deals-title" title="Deal đang mở" count={open.length}
      action={<button type="button" onClick={onShowAll} className="text-xs font-medium text-primary hover:underline">Xem Lead & Deal</button>}>
      {open.length ? (
        <ul className="divide-y divide-gray-100">
          {open.map((deal) => (
            <li key={deal.name} className="space-y-1 px-5 py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono text-xs text-ink">{deal.name}</span>
                <DealStatus status={deal.status} />
              </div>
              <p className="text-xs text-muted">Dự kiến {formatVnd(deal.expected_deal_value)} · tạo {displayDate(deal.creation)}</p>
            </li>
          ))}
        </ul>
      ) : <p className="px-5 py-4 text-sm text-muted">Không có Deal đang mở.</p>}
      <p className="border-t border-border px-5 py-2 text-xs text-muted">
        {leads.length} Lead · {deals.length} Deal (tổng cộng)
      </p>
    </Panel>
  );
}
