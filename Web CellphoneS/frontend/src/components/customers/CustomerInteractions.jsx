import { useState } from "react";
import Button from "../Button";
import { EmptyState, ErrorState, Panel, SkeletonLines } from "./CustomerStates";
import { displayDateTime, displayOrDash, INTERACTION_TYPE_LABELS, relativeDays } from "../../utils/customer360";

// L02 – Lịch sử tương tác và tư vấn. Nguồn chính: get_customer_timeline (PROPOSED),
// dự kiến tổng hợp từ CRM Call Log / CRM Task – mapping chờ L03.
// timeline = { status: "loading" | "ready" | "error", items, total, error, loadingMore }

const RELATED_LABELS = { "CRM Lead": "Lead", "CRM Deal": "Deal", "C360 After Sales Request": "Yêu cầu" };

export default function CustomerInteractions({ timeline, onLoadMore, onRetry, compact = false, onShowAll }) {
  const [type, setType] = useState("all");
  const items = timeline.items || [];
  const types = [...new Set(items.map((item) => item.type).filter(Boolean))];
  const shown = (type === "all" ? items : items.filter((item) => item.type === type)).slice(0, compact ? 5 : undefined);
  const hasMore = items.length < (timeline.total ?? 0);

  const action = compact ? (
    items.length > 0 && <button type="button" onClick={onShowAll} className="text-xs font-medium text-primary hover:underline">Xem tất cả</button>
  ) : types.length > 1 && (
    <label className="flex items-center gap-2 text-xs text-muted">
      Loại
      <select className="rounded-md border border-border bg-white px-2 py-1 text-xs text-ink" value={type}
        onChange={(event) => setType(event.target.value)}>
        <option value="all">Tất cả</option>
        {types.map((t) => <option key={t} value={t}>{INTERACTION_TYPE_LABELS[t] || t}</option>)}
      </select>
    </label>
  );

  return (
    <Panel id={compact ? "recent-activity-title" : "interactions-title"}
      title={compact ? "Hoạt động gần đây" : "Lịch sử tương tác"}
      count={timeline.status === "ready" ? timeline.total : undefined} action={action}>
      {timeline.status === "loading" ? <SkeletonLines lines={compact ? 3 : 5} label="Đang tải lịch sử tương tác…" />
        : timeline.status === "error" ? (
          <ErrorState compact error={timeline.error} onRetry={onRetry}
            notFoundMessage="API get_customer_timeline chưa được triển khai trên máy chủ." />
        ) : !items.length ? (
          <EmptyState compact title="Chưa có tương tác nào được ghi nhận" />
        ) : (
          <>
            <ol className="divide-y divide-gray-100">
              {shown.map((event) => (
                <li key={event.id} className="flex gap-3 px-5 py-3">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                      <span className="text-sm font-medium text-ink">{INTERACTION_TYPE_LABELS[event.type] || event.type || "Tương tác"}</span>
                      <time dateTime={event.occurred_at} title={displayDateTime(event.occurred_at)} className="text-xs text-muted">
                        {relativeDays(event.occurred_at)}
                      </time>
                    </div>
                    <p className="mt-0.5 text-sm text-ink">{displayOrDash(event.summary)}</p>
                    {event.related_name && (
                      <p className="mt-0.5 text-xs text-muted">
                        {RELATED_LABELS[event.related_doctype] || event.related_doctype}: <span className="font-mono">{event.related_name}</span>
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
            {!compact && hasMore && (
              <div className="border-t border-border px-5 py-3 text-center">
                <Button variant="secondary" size="sm" onClick={onLoadMore} loading={timeline.loadingMore}>
                  Xem thêm ({items.length}/{timeline.total})
                </Button>
                {timeline.loadMoreError && <p role="alert" className="mt-2 text-xs text-primary">Không tải thêm được. Thử lại.</p>}
              </div>
            )}
            {!compact && type !== "all" && hasMore && (
              <p className="px-5 pb-3 text-xs text-muted">Bộ lọc loại chỉ áp dụng cho các tương tác đã tải.</p>
            )}
          </>
        )}
    </Panel>
  );
}
