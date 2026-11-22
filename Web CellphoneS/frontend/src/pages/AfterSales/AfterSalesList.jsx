import { useState } from "react";
import { Search } from "lucide-react";
import Button from "../../components/Button";
import { Link } from "react-router-dom";
import Table from "../../components/Table";
import { displayDate, REQUEST_STATUS_LABELS } from "../../utils/customer360";
import TicketStatus from "./TicketStatus";
import { filterTickets } from "./ticketFilters";

const statusLabels = { ...REQUEST_STATUS_LABELS, Pending: "Đang chờ" };
const pageSize = 10;
const defaults = { query: "", status: "", from: "", to: "", order: "desc" };

const fields = [
  { key: "customer", label: "Khách hàng", render: (value, row) => row.customerName || value || "—" },
  { key: "relatedOrder", label: "Đơn hàng" },
  { key: "subject", label: "Tiêu đề yêu cầu" },
  { key: "type", label: "Loại yêu cầu" },
  { key: "status", label: "Trạng thái", render: (value) => <TicketStatus status={value} /> },
  { key: "createdAt", label: "Ngày tạo", render: displayDate },
  { key: "assignedTo", label: "Nhân viên phụ trách" },
];

export default function AfterSalesList({ tickets, loading, error, onRetry }) {
  const [filters, setFilters] = useState(defaults);
  const [requestedPage, setRequestedPage] = useState(1);
  const invalidDates = filters.from && filters.to && filters.from > filters.to;
  const matching = invalidDates ? [] : filterTickets(tickets ?? [], filters);
  const pageCount = Math.max(1, Math.ceil(matching.length / pageSize));
  const page = Math.min(requestedPage, pageCount);
  const rows = matching.slice((page - 1) * pageSize, page * pageSize);
  const statuses = [...new Set([...Object.keys(statusLabels), ...(tickets ?? []).map(({ status }) => status).filter(Boolean)])];
  const columns = [
    {
      key: "id",
      label: "Mã Ticket",
      render: (id) => (
        <Link className="whitespace-nowrap font-semibold text-primary hover:underline" to={`/after-sales/${encodeURIComponent(id)}`}>
          {id}
        </Link>
      ),
    },
    ...fields,
  ];

  function updateFilter(key, value) {
    setFilters((previous) => ({ ...previous, [key]: value }));
    setRequestedPage(1);
  }

  let emptyMessage = "Chưa có dữ liệu. Nguồn dữ liệu hậu mãi chưa được kết nối.";
  if (tickets) emptyMessage = tickets.length ? "Không tìm thấy yêu cầu phù hợp." : "Chưa có yêu cầu hỗ trợ.";
  if (invalidDates) emptyMessage = "Ngày kết thúc phải từ ngày bắt đầu trở đi.";

  return (
    <section aria-labelledby="ticket-list-title" aria-busy={loading} className="crm-card min-w-0 space-y-4 p-4 lg:p-6">
      <h2 id="ticket-list-title" className="text-lg font-semibold">Danh sách yêu cầu hỗ trợ</h2>
      <fieldset disabled={!tickets || loading || Boolean(error)} className="grid min-w-0 gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <label className="min-w-0 space-y-1 text-sm font-medium">
          <span>Tìm kiếm</span>
          <span className="relative block">
            <Search size={17} className="absolute top-3 left-3 text-muted" aria-hidden="true" />
            <input type="search" className="crm-input pl-9 disabled:bg-gray-50" placeholder="Mã, khách hàng, tiêu đề" value={filters.query} onChange={(event) => updateFilter("query", event.target.value)} />
          </span>
        </label>
        <label className="min-w-0 space-y-1 text-sm font-medium">
          <span>Trạng thái</span>
          <select className="crm-input" value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
            <option value="">Tất cả trạng thái</option>
            {statuses.map((status) => <option key={status} value={status}>{statusLabels[status] ?? status}</option>)}
          </select>
        </label>
        {Object.entries({ from: "Từ ngày", to: "Đến ngày" }).map(([key, label]) => (
          <label key={key} className="min-w-0 space-y-1 text-sm font-medium">
            <span>{label}</span>
            <input type="date" className="crm-input" aria-invalid={Boolean(invalidDates)} value={filters[key]} onChange={(event) => updateFilter(key, event.target.value)} />
          </label>
        ))}
        <label className="min-w-0 space-y-1 text-sm font-medium">
          <span>Ngày tạo</span>
          <select className="crm-input" value={filters.order} onChange={(event) => updateFilter("order", event.target.value)}>
            <option value="desc">Mới nhất trước</option>
            <option value="asc">Cũ nhất trước</option>
          </select>
        </label>
      </fieldset>
      {error ? (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-primary-soft p-4 text-sm text-primary">
          <p>Không thể tải yêu cầu hỗ trợ. {error}</p>
          {onRetry && <Button variant="outline" size="sm" onClick={onRetry}>Thử lại</Button>}
        </div>
      ) : (
        <>
          <Table columns={columns} data={rows} loading={loading} emptyMessage={emptyMessage} />
          {!loading && matching.length > 0 && (
            <nav aria-label="Phân trang yêu cầu hỗ trợ" className="flex flex-wrap items-center justify-between gap-3">
              <p role="status" className="text-sm text-muted">
                {(page - 1) * pageSize + 1}–{(page - 1) * pageSize + rows.length} / {matching.length} yêu cầu
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Button size="sm" variant="secondary" disabled={page <= 1} onClick={() => setRequestedPage(page - 1)}>Trước</Button>
                <span className="text-sm">Trang {page}/{pageCount}</span>
                <Button size="sm" variant="secondary" disabled={page >= pageCount} onClick={() => setRequestedPage(page + 1)}>Sau</Button>
              </div>
            </nav>
          )}
        </>
      )}
    </section>
  );
}
