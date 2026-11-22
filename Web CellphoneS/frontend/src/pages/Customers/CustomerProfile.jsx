import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import CustomerInfo from "../../components/customers/CustomerInfo";
import CustomerAlerts from "../../components/customers/CustomerAlerts";
import CustomerHistory, { PurchaseSummary } from "../../components/customers/CustomerHistory";
import CustomerInteractions from "../../components/customers/CustomerInteractions";
import CustomerDeals, { OpenDealsSummary } from "../../components/customers/CustomerDeals";
import CustomerSupport, { OpenRequestsSummary } from "../../components/customers/CustomerSupport";
import { ErrorState, SkeletonLines } from "../../components/customers/CustomerStates";
import { customerDataMode, getCustomerAccess, getCustomerProfile, getCustomerTimeline } from "../../services/customerService";
import { computeAlerts, customerBasePath } from "../../utils/customer360";

// L02 – Hồ sơ Customer 360.
// Bố cục: nhận diện → cần chú ý → (tab) Tổng quan: hoạt động gần đây + các việc đang mở.
const TABS = [
  { id: "overview", label: "Tổng quan" },
  { id: "deals", label: "Lead & Deal" },
  { id: "orders", label: "Mua hàng" },
  { id: "interactions", label: "Tương tác" },
  { id: "support", label: "Sau bán" },
];
const TIMELINE_PAGE_SIZE = 20;

export default function CustomerProfile() {
  const { customerId } = useParams();
  const location = useLocation();
  const base = customerBasePath(location.pathname);
  const isDemo = base.startsWith("/preview/") || customerDataMode === "demo";
  const [editableId, setEditableId] = useState(null);

  useEffect(() => {
    if (isDemo) return;
    const controller = new AbortController();
    getCustomerAccess(customerId, { signal: controller.signal }).then(
      ({ canEdit }) => { if (!controller.signal.aborted) setEditableId(canEdit ? customerId : null); },
      () => { if (!controller.signal.aborted) setEditableId(null); },
    );
    return () => controller.abort();
  }, [customerId, isDemo]);
  const backTo = typeof location.state?.from === "string" && location.state.from.startsWith(base) ? location.state.from : base;

  const [params, setParams] = useSearchParams();
  const activeTab = TABS.some((tab) => tab.id === params.get("tab")) ? params.get("tab") : "overview";
  const tabRefs = useRef({});

  const [reload, setReload] = useState(0);
  const profileKey = `${customerId}|${reload}`;
  const [profileState, setProfileState] = useState({ key: null, data: null, error: null });

  const [timelineReload, setTimelineReload] = useState(0);
  const timelineKey = `${customerId}|${timelineReload}`;
  const [timelineState, setTimelineState] = useState({ key: null, items: [], total: 0, page: 0, error: null });
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadMoreError, setLoadMoreError] = useState(false);

  // Hồ sơ và timeline tải song song; lỗi timeline không làm mất hồ sơ.
  useEffect(() => {
    const controller = new AbortController();
    getCustomerProfile(customerId, { signal: controller.signal, demo: isDemo })
      .then((data) => { if (!controller.signal.aborted) setProfileState({ key: profileKey, data, error: null }); })
      .catch((error) => {
        if (!controller.signal.aborted && error.name !== "AbortError") setProfileState({ key: profileKey, data: null, error });
      });
    return () => controller.abort();
  }, [customerId, isDemo, profileKey]);

  useEffect(() => {
    const controller = new AbortController();
    getCustomerTimeline(customerId, { page: 1, page_size: TIMELINE_PAGE_SIZE, signal: controller.signal, demo: isDemo })
      .then((result) => {
        if (!controller.signal.aborted) {
          setTimelineState({ key: timelineKey, items: result.items, total: result.total, page: 1, error: null });
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted && error.name !== "AbortError") {
          setTimelineState({ key: timelineKey, items: [], total: 0, page: 0, error });
        }
      });
    return () => controller.abort();
  }, [customerId, isDemo, timelineKey]);

  async function loadMoreTimeline() {
    const key = timelineState.key;
    setLoadingMore(true);
    setLoadMoreError(false);
    try {
      const result = await getCustomerTimeline(customerId, { page: timelineState.page + 1, page_size: TIMELINE_PAGE_SIZE, demo: isDemo });
      setTimelineState((prev) => (prev.key !== key ? prev : {
        ...prev,
        items: [...prev.items, ...result.items.filter((item) => !prev.items.some((old) => old.id === item.id))],
        total: result.total,
        page: prev.page + 1,
      }));
    } catch {
      setLoadMoreError(true);
    } finally {
      setLoadingMore(false);
    }
  }

  const profile = profileState.key === profileKey ? profileState.data : null;
  const profileError = profileState.key === profileKey ? profileState.error : null;
  const timelineReady = timelineState.key === timelineKey;
  const timeline = {
    status: !timelineReady ? "loading" : timelineState.error ? "error" : "ready",
    items: timelineReady ? timelineState.items : [],
    total: timelineReady ? timelineState.total : 0,
    error: timelineState.error,
    loadingMore,
    loadMoreError,
  };

  const timelineForAlerts = timeline.status === "ready"
    ? { items: timeline.items, complete: timeline.items.length >= timeline.total }
    : null;
  // Tính rẻ (vài chục bản ghi) nên tính lại mỗi lần render, không cần memo.
  const alerts = profile ? computeAlerts(profile, timelineForAlerts) : [];

  function selectTab(id, focus = false) {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (id === "overview") next.delete("tab");
      else next.set("tab", id);
      return next;
    }, { replace: true });
    if (focus) tabRefs.current[id]?.focus();
  }

  function onTabKeyDown(event) {
    const index = TABS.findIndex((tab) => tab.id === activeTab);
    const moves = { ArrowRight: 1, ArrowLeft: -1, Home: -index, End: TABS.length - 1 - index };
    if (!(event.key in moves)) return;
    event.preventDefault();
    selectTab(TABS[(index + moves[event.key] + TABS.length) % TABS.length].id, true);
  }

  const backLink = (
    <Link to={backTo} className="inline-flex items-center gap-2 text-sm text-muted hover:text-primary">
      <ArrowLeft size={16} aria-hidden="true" /> Danh sách khách hàng
    </Link>
  );

  if (profileError) {
    return (
      <div className="space-y-4">
        {backLink}
        <div className="crm-card !p-0">
          <ErrorState error={profileError} onRetry={() => setReload((v) => v + 1)}
            notFoundMessage="Không tìm thấy hồ sơ, hoặc bạn không có quyền xem hồ sơ này." />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="space-y-4">
        {backLink}
        <div className="crm-card !p-0"><SkeletonLines lines={4} label="Đang tải hồ sơ khách hàng…" /></div>
      </div>
    );
  }


  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {backLink}
        <span className="text-xs text-gray-500">Hồ sơ / {profile.customer_id}</span>
      </div>
      {location.state?.notice && <p role="status" className="text-sm text-green-800">{location.state.notice}</p>}
      {!isDemo && editableId === customerId && (
        <Link className="crm-action" to={`/customers/${encodeURIComponent(customerId)}/edit`}>Chỉnh sửa hồ sơ</Link>
      )}
      <CustomerInfo customer={profile} isDemo={isDemo} />
      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_310px]">
        <div className="min-w-0 space-y-3">
          <div role="tablist" aria-label="Các mục hồ sơ khách hàng" onKeyDown={onTabKeyDown}
            className="flex gap-1 overflow-x-auto rounded-t-lg border-b border-[#e4e7eb] bg-white px-2 pt-1">
            {TABS.map((tab) => {
              const selected = tab.id === activeTab;
              return (
                <button key={tab.id} type="button" role="tab" id={`tab-${tab.id}`} aria-selected={selected}
                  aria-controls={`panel-${tab.id}`} tabIndex={selected ? 0 : -1}
                  ref={(node) => { tabRefs.current[tab.id] = node; }} onClick={() => selectTab(tab.id)}
                  className={`-mb-px shrink-0 border-b-2 px-3.5 py-3 text-[13px] transition-colors ${selected
                    ? "border-primary font-semibold text-primary"
                    : "border-transparent text-gray-600 hover:text-gray-900"}`}>
                  {tab.label}
                </button>
              );
            })}
          </div>
          <div role="tabpanel" id={`panel-${activeTab}`} aria-labelledby={`tab-${activeTab}`} tabIndex={0}
            className="min-w-0 space-y-3 focus-visible:outline-none">
            {activeTab === "overview" && (
              <>
                <CustomerInteractions compact timeline={timeline} onShowAll={() => selectTab("interactions")}
                  onRetry={() => setTimelineReload((v) => v + 1)} />
                <PurchaseSummary orders={profile.orders} onShowAll={() => selectTab("orders")} />
              </>
            )}
            {activeTab === "deals" && <CustomerDeals leads={profile.leads} deals={profile.deals} />}
            {activeTab === "orders" && <CustomerHistory orders={profile.orders} isDemo={isDemo} />}
            {activeTab === "interactions" && (
              <CustomerInteractions timeline={timeline} onLoadMore={loadMoreTimeline}
                onRetry={() => setTimelineReload((v) => v + 1)} />
            )}
            {activeTab === "support" && <CustomerSupport requests={profile.after_sales_requests} linkTickets={!isDemo} />}
          </div>
        </div>
        <aside className="order-first min-w-0 space-y-3 xl:order-last" aria-label="Tình trạng và việc cần xử lý">
          <CustomerAlerts alerts={alerts} timelinePending={timeline.status === "loading"} />
          <OpenDealsSummary leads={profile.leads} deals={profile.deals} onShowAll={() => selectTab("deals")} />
          <OpenRequestsSummary requests={profile.after_sales_requests} onShowAll={() => selectTab("support")} />
        </aside>
      </div>
    </div>
  );
}
