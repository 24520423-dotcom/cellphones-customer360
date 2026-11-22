import { useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { ChevronLeft, ChevronRight, RefreshCcw, Search, X, Check, SlidersHorizontal } from "lucide-react";
import Button from "../../components/Button";
import CustomerDataTable from "../../components/customers/CustomerDataTable";
import { DemoBadge, EmptyState, ErrorState } from "../../components/customers/CustomerStates";
import {
  customerDataMode, getCustomerAccess, listCapabilities as apiCapabilities, listCustomers, SORT_OPTIONS,
} from "../../services/customerService";
import {
  customerBasePath, daysSince, displayDate, INSIGHT_RULES, relativeDays,
} from "../../utils/customer360";

// L01 – Danh sách khách hàng Customer 360.
const PAGE_SIZE = 10;
const FILTER_DISABLED_HINT = "Chờ L03 bổ sung tham số lọc/sắp xếp vào API Contract";

function setParam(next, key, value) {
  if (value === null || value === undefined || value === "" || value === false) next.delete(key);
  else next.set(key, String(value));
}

export default function CustomerList() {
  const { pathname, search } = useLocation();
  const base = customerBasePath(pathname);
  const isDemo = base.startsWith("/preview/") || customerDataMode === "demo";
  const listCapabilities = isDemo ? { filters: true, sort: true } : apiCapabilities;
  const [canCreate, setCanCreate] = useState(false);

  useEffect(() => {
    if (isDemo) return;
    const controller = new AbortController();
    getCustomerAccess(null, { signal: controller.signal }).then(
      ({ canCreate }) => { if (!controller.signal.aborted) setCanCreate(Boolean(canCreate)); },
      () => { if (!controller.signal.aborted) setCanCreate(false); },
    );
    return () => controller.abort();
  }, [isDemo]);
  const [params, setParams] = useSearchParams();

  // Trạng thái tìm kiếm/lọc/trang nằm trên URL để giữ nguyên khi mở hồ sơ rồi quay lại.
  const q = params.get("q") ?? "";
  const page = Math.max(1, Number.parseInt(params.get("page"), 10) || 1);
  const openDeal = listCapabilities.filters && params.get("open_deal") === "1";
  const openRequest = listCapabilities.filters && params.get("open_request") === "1";
  const sortParam = params.get("sort");
  const sort = listCapabilities.sort && SORT_OPTIONS.some((o) => o.value === sortParam) ? sortParam : "updated_desc";

  const [draft, setDraft] = useState(q);
  const [syncedQ, setSyncedQ] = useState(q);
  if (q !== syncedQ) {
    // URL đổi từ bên ngoài (Back, bấm menu) → đồng bộ lại ô tìm kiếm.
    setSyncedQ(q);
    if (q !== draft.trim()) setDraft(q);
  }

  const [reload, setReload] = useState(0);
  const requestKey = JSON.stringify([q, page, openDeal, openRequest, sort, reload]);
  const [state, setState] = useState({ key: null, data: null, error: null });
  const loading = state.key !== requestKey;

  function update(changes) {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      Object.entries(changes).forEach(([key, value]) => setParam(next, key, value));
      if (!("page" in changes)) next.delete("page");
      return next;
    }, { replace: true });
  }

  // Debounce ô tìm kiếm rồi ghi lên URL.
  useEffect(() => {
    const value = draft.trim();
    if (value === q) return undefined;
    const timer = setTimeout(() => {
      setParams((prev) => {
        const next = new URLSearchParams(prev);
        setParam(next, "q", value);
        next.delete("page");
        return next;
      }, { replace: true });
    }, 300);
    return () => clearTimeout(timer);
  }, [draft, q, setParams]);

  // Tải dữ liệu. "loading" được suy ra từ requestKey nên không thể bị kẹt.
  useEffect(() => {
    const controller = new AbortController();
    listCustomers({
      search: q, page, page_size: PAGE_SIZE,
      has_open_deal: openDeal, has_open_request: openRequest, order_by: sort,
      signal: controller.signal, demo: isDemo,
    })
      .then((data) => {
        if (!controller.signal.aborted) setState({ key: requestKey, data, error: null });
      })
      .catch((error) => {
        if (!controller.signal.aborted && error.name !== "AbortError") {
          setState({ key: requestKey, data: null, error });
        }
      });
    return () => controller.abort();
  }, [q, page, openDeal, openRequest, sort, requestKey, isDemo]);

  const data = state.data;
  const items = loading ? [] : data?.items ?? [];
  const total = data?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const hasFilter = Boolean(q || openDeal || openRequest);

  // Ở API mode, trường đề xuất chưa có trong contract sẽ trả null → đánh dấu cột "chờ API".
  const available = (key) => isDemo || (data?.items ?? []).some((item) => item[key] !== null);
  const proposedLabel = (text, key) => (available(key) ? text : (
    <span title="Trường đề xuất bổ sung API Contract – API hiện chưa trả về">{text} *</span>
  ));
  const missingProposed = !isDemo && data && ["email_masked", "segments", "updated_at", "open_request_count"]
    .some((key) => !available(key));

  const columns = [
    {
      key: "display_name",
      label: "Khách hàng",
      render: (value, customer) => (
        <div className="min-w-0">
          <Link
            to={`${base}/${encodeURIComponent(customer.customer_id)}`}
            state={{ from: pathname + search }}
            className="font-semibold text-ink hover:text-primary hover:underline"
          >
            {value}
          </Link>
          <p className="mt-0.5 font-mono text-xs text-muted">{customer.customer_id}</p>
        </div>
      ),
    },
    {
      key: "phone_masked",
      label: proposedLabel("Liên hệ", "email_masked"),
      render: (value, customer) => (
        <div className="text-xs">
          <p className="text-ink">{value || <span className="text-muted">Chưa có SĐT</span>}</p>
          {customer.email_masked && <p className="mt-0.5 break-all text-muted">{customer.email_masked}</p>}
        </div>
      ),
    },
    {
      key: "segments",
      label: proposedLabel("Phân khúc", "segments"),
      render: (value) => {
        if (value === null) return <span className="text-muted">—</span>;
        if (!value.length) return <span className="text-xs text-muted">Chưa phân khúc</span>;
        return (
          <div className="flex flex-wrap gap-1">
            {value.map((s) => <span key={s} className="rounded-md bg-gray-100 px-2 py-0.5 text-xs">{s}</span>)}
          </div>
        );
      },
    },
    {
      key: "deal_count",
      label: "Lead · Deal",
      render: (value, customer) => (
        <div className="whitespace-nowrap text-xs">
          <p className="text-ink">{customer.lead_count ?? "—"} Lead · {value ?? "—"} Deal</p>
          {customer.open_deal_count > 0 && (
            <p className="mt-0.5 font-medium text-primary">{customer.open_deal_count} Deal đang mở</p>
          )}
        </div>
      ),
    },
    {
      key: "open_request_count",
      label: proposedLabel("Cần chú ý", "open_request_count"),
      render: (value, customer) => {
        const notes = [];
        if (value > 0) {
          notes.push(<span key="req" className="rounded-md bg-amber-100 px-2 py-0.5 text-amber-900">{value} hỗ trợ đang mở</span>);
        }
        if (available("last_interaction_at")) {
          const idle = daysSince(customer.last_interaction_at);
          if (idle === null) notes.push(<span key="none" className="text-muted">Chưa có tương tác</span>);
          else if (idle > INSIGHT_RULES.INACTIVE_DAYS) notes.push(<span key="idle" className="text-muted">{idle} ngày chưa tương tác</span>);
        }
        return notes.length ? <div className="flex flex-col items-start gap-1 text-xs">{notes}</div> : <span className="text-muted">—</span>;
      },
    },
    {
      key: "updated_at",
      label: proposedLabel("Cập nhật", "updated_at"),
      render: (value) => (
        <span className="whitespace-nowrap text-xs text-muted" title={displayDate(value)}>{relativeDays(value)}</span>
      ),
    },
  ];

  const emptyContent = hasFilter ? (
    <EmptyState title="Không có hồ sơ phù hợp" description="Thử từ khóa khác hoặc bỏ bớt bộ lọc.">
      <Button variant="secondary" size="sm" onClick={() => { setDraft(""); update({ q: null, open_deal: null, open_request: null }); }}>
        Xóa tìm kiếm và bộ lọc
      </Button>
    </EmptyState>
  ) : page > 1 ? (
    <EmptyState title="Trang này không có dữ liệu">
      <Button variant="secondary" size="sm" onClick={() => update({ page: null })}>Về trang đầu</Button>
    </EmptyState>
  ) : (
    <EmptyState title="Chưa có hồ sơ khách hàng" description="Hồ sơ sẽ xuất hiện khi Lead/Deal được hợp nhất vào Customer 360." />
  );

  const from = total ? (page - 1) * PAGE_SIZE + 1 : 0;
  const to = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-[25px] font-bold tracking-tight text-ink">Khách hàng</h1>
            {isDemo && <DemoBadge />}
            {!isDemo && canCreate && <Link className="crm-action" to="/customers/new">Thêm khách hàng</Link>}
          </div>
          <p className="text-[13px] text-muted">Tra cứu và xem toàn bộ hành trình khách hàng trên một hồ sơ.</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="rounded-md bg-white px-3 py-2 ring-1 ring-gray-200">Customer 360</span>
        </div>
      </header>

      <section className="overflow-hidden rounded-xl border border-[#e4e7eb] bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]" aria-labelledby="customer-directory-title">
        <div className="border-b border-[#edf0f2] px-4 py-3.5 sm:px-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 id="customer-directory-title" className="text-[15px] font-semibold text-ink">Danh sách hồ sơ</h2>
              <p className="mt-0.5 text-xs text-gray-500" aria-live="polite">
                {loading ? "Đang tải…" : state.error ? "Không tải được danh sách" : `${total} hồ sơ${hasFilter ? " phù hợp với bộ lọc" : ""}`}
              </p>
            </div>
            <button type="button" disabled={loading} onClick={() => setReload((v) => v + 1)}
              className="inline-flex items-center gap-2 rounded-md border border-[#e4e7eb] bg-white px-3 py-2 text-xs font-medium text-gray-600 transition hover:bg-gray-50 disabled:opacity-50">
              <RefreshCcw size={14} aria-hidden="true" /> Làm mới
            </button>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2.5">
            <div className="relative min-w-[225px] flex-[2_1_330px]">
              <label htmlFor="customer-search" className="sr-only">Tìm khách hàng</label>
              <Search size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
              <input id="customer-search" type="search" value={draft}
                onChange={(event) => setDraft(event.target.value)} autoComplete="off"
                placeholder="Tìm tên, mã hồ sơ, số điện thoại…"
                className="h-10 w-full rounded-lg border border-[#e3e6e9] bg-[#fbfcfd] py-2 pl-10 pr-9 text-sm text-ink outline-none transition focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/10" />
              {draft && (
                <button type="button" onClick={() => setDraft("")} aria-label="Xóa từ khóa"
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted hover:text-ink"><X size={14} /></button>
              )}
            </div>
            <fieldset className="flex flex-wrap items-center gap-2" disabled={!listCapabilities.filters}
              title={listCapabilities.filters ? undefined : FILTER_DISABLED_HINT}>
              <legend className="sr-only">Lọc nhanh</legend>
              <SlidersHorizontal size={15} className="hidden text-gray-400 sm:block" aria-hidden="true" />
              {[["open_deal", "Deal đang mở", openDeal], ["open_request", "Cần hỗ trợ", openRequest]].map(([key, label, active]) => (
                <button key={key} type="button" aria-pressed={active}
                  onClick={() => update({ [key]: active ? null : "1" })}
                  className={`inline-flex h-10 items-center gap-1.5 whitespace-nowrap rounded-lg border px-3 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${active
                    ? "border-[#e9b0b5] bg-[#fff7f8] text-primary"
                    : "border-[#e3e6e9] bg-white text-gray-600 hover:bg-gray-50"}`}>
                  {active && <Check size={13} aria-hidden="true" />}{label}
                </button>
              ))}
            </fieldset>
            <div className="min-w-[168px] flex-[0_1_182px]">
              <label htmlFor="customer-sort" className="sr-only">Sắp xếp</label>
              <select id="customer-sort" className="h-10 w-full rounded-lg border border-[#e3e6e9] bg-white px-3 text-xs text-gray-700 disabled:opacity-50"
                value={sort} disabled={!listCapabilities.sort}
                title={listCapabilities.sort ? undefined : FILTER_DISABLED_HINT}
                onChange={(event) => update({ sort: event.target.value === "updated_desc" ? null : event.target.value })}>
                {SORT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </div>
          </div>
          {hasFilter && (
            <div className="mt-2 flex items-center justify-end gap-2 text-xs text-gray-500">
              <span>Đang áp dụng bộ lọc</span>
              <button type="button" className="font-semibold text-primary hover:underline"
                onClick={() => { setDraft(""); update({ q: null, open_deal: null, open_request: null }); }}>
                Xóa bộ lọc
              </button>
            </div>
          )}
        </div>

        {state.error && !loading ? (
          <ErrorState error={state.error} onRetry={() => setReload((v) => v + 1)}
            notFoundMessage="API Customer 360 (list_customers) chưa được triển khai trên máy chủ." />
        ) : (
          <CustomerDataTable columns={columns} data={items} loading={loading}
            getRowKey={(customer) => customer.customer_id} emptyMessage={emptyContent} />
        )}

        {!state.error && total > 0 && (
          <nav aria-label="Phân trang danh sách khách hàng"
            className="flex flex-wrap items-center justify-between gap-3 border-t border-[#edf0f2] bg-[#fff] px-5 py-3 text-xs text-gray-500">
            <span>Hiển thị {from}–{to} trên {total} hồ sơ</span>
            <div className="flex items-center gap-2">
              <button type="button" aria-label="Trang trước" disabled={page <= 1 || loading}
                onClick={() => update({ page: page - 1 > 1 ? page - 1 : null })}
                className="rounded-md border border-gray-200 p-1.5 text-gray-600 disabled:opacity-30"><ChevronLeft size={17} /></button>
              <span className="px-1 font-medium text-gray-700">{page} / {lastPage}</span>
              <button type="button" aria-label="Trang sau" disabled={page >= lastPage || loading}
                onClick={() => update({ page: page + 1 })}
                className="rounded-md border border-gray-200 p-1.5 text-gray-600 disabled:opacity-30"><ChevronRight size={17} /></button>
            </div>
          </nav>
        )}
      </section>
      {missingProposed && (
        <p className="text-xs text-muted">* Trường đề xuất bổ sung API Contract; API hiện chưa trả về nên đang để trống.</p>
      )}
    </div>
  );
}
