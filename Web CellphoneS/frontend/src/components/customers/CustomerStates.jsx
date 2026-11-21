import { Link, useLocation } from "react-router-dom";
import { TriangleAlert, Inbox } from "lucide-react";
import Button from "../Button";

// Nhãn dữ liệu demo dùng chung cho L01/L02 – chỉ hiển thị một lần ở đầu trang.
export function DemoBadge() {
  return (
    <span
      className="inline-flex items-center rounded-md border border-[#e4e7eb] bg-[#f8f9fa] px-2 py-1 text-[11px] font-medium text-gray-600"
      title="Dữ liệu giả lập phục vụ dựng giao diện. Không phải dữ liệu khách hàng của CellphoneS."
    >
      Dữ liệu mô phỏng
    </span>
  );
}

const ERROR_HINTS = {
  auth: "Vui lòng đăng nhập lại để tiếp tục.",
  forbidden: "Liên hệ quản trị viên nếu bạn cần quyền truy cập.",
  network: "Kiểm tra kết nối hoặc Backend Frappe rồi thử lại.",
  server: "Thử lại sau ít phút. Nếu lỗi lặp lại, báo cho người phụ trách Backend.",
  contract: "Dữ liệu trả về không khớp API Contract. Báo cho người phụ trách Backend (L03).",
};

export function ErrorState({ error, onRetry, notFoundMessage, compact = false }) {
  const { pathname, search } = useLocation();
  const kind = error?.kind;
  const title = kind === "not_found" && notFoundMessage ? notFoundMessage : error?.message || "Đã có lỗi xảy ra.";
  const hint = kind === "not_found" ? null : ERROR_HINTS[kind];

  return (
    <div className={`flex flex-col items-center gap-2 text-center ${compact ? "px-4 py-6" : "px-5 py-12"}`}>
      <TriangleAlert size={compact ? 20 : 24} className="text-primary" aria-hidden="true" />
      <p role="alert" className="text-sm font-medium text-ink">{title}</p>
      {hint && <p className="max-w-md text-xs text-muted">{hint}</p>}
      <div className="mt-1 flex flex-wrap justify-center gap-2">
        {kind === "auth" && (
          <Link className="crm-action" to="/login" state={{ from: pathname + search }}>Đăng nhập lại</Link>
        )}
        {onRetry && !["auth", "forbidden", "not_found"].includes(kind) && (
          <Button variant="secondary" size="sm" onClick={onRetry}>Thử lại</Button>
        )}
      </div>
    </div>
  );
}

export function EmptyState({ title, description, children, compact = false }) {
  return (
    <div className={`flex flex-col items-center gap-2 text-center text-muted ${compact ? "px-4 py-6" : "px-5 py-10"}`}>
      <Inbox size={compact ? 20 : 24} aria-hidden="true" />
      <p className="text-sm font-medium text-ink">{title}</p>
      {description && <p className="max-w-md text-xs">{description}</p>}
      {children}
    </div>
  );
}

export function SkeletonLines({ lines = 3, label = "Đang tải…" }) {
  return (
    <div role="status" aria-label={label} className="space-y-3 px-5 py-5">
      {Array.from({ length: lines }, (_, index) => (
        <div key={index} className="h-4 animate-pulse rounded bg-gray-100" style={{ width: `${90 - index * 15}%` }} />
      ))}
      <span className="sr-only">{label}</span>
    </div>
  );
}

// Bảng gọn cho các khối trong hồ sơ. Không dùng shared Table vì Table có header tối và
// min-width 650px, phù hợp trang danh sách hơn là panel nhỏ. Giữ cùng token màu của nhóm.
export function DataTable({ caption, columns, rows, getKey }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-gray-50 text-xs text-muted">
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" className="whitespace-nowrap px-5 py-2.5 font-medium">{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map((row, index) => (
            <tr key={getKey ? getKey(row) : index}>
              {columns.map((column) => (
                <td key={column.key} className="px-5 py-3 align-top text-ink">
                  {column.render ? column.render(row[column.key], row) : row[column.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Khung section dùng chung trong hồ sơ để các khối có cùng tiêu đề/đếm/hành động.
export function Panel({ title, count, action, children, id }) {
  return (
    <section className="crm-card !p-0" aria-labelledby={id}>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-5 py-3">
        <h2 id={id} className="text-sm font-semibold text-ink">
          {title}
          {count !== undefined && count !== null && <span className="ml-2 font-normal text-muted">({count})</span>}
        </h2>
        {action}
      </div>
      {children}
    </section>
  );
}
