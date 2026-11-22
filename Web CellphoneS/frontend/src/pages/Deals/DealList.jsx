import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowUpRight,
  BriefcaseBusiness,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  Columns3,
  Info,
  List,
  Plus,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import Table from "../../components/Table";
import DealBoard from "./DealBoard";
import DealDetail from "./DealDetail";
import DealForm from "./DealForm";
import {
  DEAL_STATUSES,
  INITIAL_MOCK_DEALS,
  STATUS_LABELS,
  formatVnd,
} from "./dealUtils";
import { getDeal, getDealCapabilities, listDeals, saveDeal as persistDeal, updateDealStage } from "../../services/dealService";
import "./Deals.css";

const TEMP_ID_PREFIX = "TEMP-DEAL-";
const previewStatuses = DEAL_STATUSES.map((name) => ({ name, type: ["Won", "Lost"].includes(name) ? name : "Open" }));

function StatusBadge({ status }) {
  return (
    <span className="deal-stage" data-status={status}>
      <span className="deal-stage-dot" aria-hidden="true" />
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function SummaryCard({ icon: Icon, label, value, helper, variant = "neutral" }) {
  return (
    <div className={`deal-stat deal-stat--${variant}`}>
      <div className="deal-stat-top">
        <span className="deal-stat-label">{label}</span>
        <span className="deal-stat-icon"><Icon size={19} strokeWidth={1.9} /></span>
      </div>
      <strong className="deal-stat-value">{value}</strong>
      <span className="deal-stat-hint">{helper}</span>
    </div>
  );
}

export default function DealList({ preview = false }) {
  const [deals, setDeals] = useState(() => preview ? INITIAL_MOCK_DEALS.map((deal) => ({ ...deal })) : []);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [view, setView] = useState("list");
  const [selectedId, setSelectedId] = useState(null);
  const [mode, setMode] = useState(null); // null | "detail" | "form"
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!preview);
  const [options, setOptions] = useState(() => preview ? { statuses: previewStatuses, canCreate: true, canMove: true } : { statuses: [] });
  const [detail, setDetail] = useState(null);
  const [saving, setSaving] = useState(false);
  const busy = useRef(false);
  const { statuses, canCreate, canMove } = options;
  const stageNames = statuses.map(({ name }) => name);

  useEffect(() => {
    if (preview) return;
    const controller = new AbortController();
    listDeals({ signal: controller.signal }).then(
      ({ deals, ...options }) => {
        if (controller.signal.aborted) return;
        setDeals(deals);
        setOptions(options);
        setLoading(false);
      },
      (error) => {
        if (controller.signal.aborted) return;
        setError(error.message);
        setLoading(false);
      },
    );
    return () => controller.abort();
  }, [preview]);

  const selected = useMemo(
    () => deals.find((deal) => deal.name === selectedId) || null,
    [deals, selectedId],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLocaleLowerCase("vi-VN");
    return deals.filter((deal) => {
      if (statusFilter !== "all" && deal.status !== statusFilter) return false;
      if (!q) return true;
      return [deal.name, deal.title, deal.lead, deal.ownerDisplay, deal.status]
        .some((value) => String(value || "").toLocaleLowerCase("vi-VN").includes(q));
    });
  }, [deals, search, statusFilter]);

  const stageTypes = new Map(statuses.map(({ name, type }) => [name, type]));
  const active = deals.filter(({ status }) => ["Open", "Ongoing", "On Hold"].includes(stageTypes.get(status)));
  const summary = {
    total: deals.length,
    active: active.length,
    won: deals.filter(({ status }) => stageTypes.get(status) === "Won").length,
    expectedOpen: active.every((deal) => deal.expected_deal_value != null && (preview || deal.currency === "VND"))
      ? active.reduce((sum, deal) => sum + Number(deal.expected_deal_value), 0)
      : null,
  };

  function openNew() {
    setSelectedId(null);
    setMode("form");
  }

  async function openDetail(deal) {
    if (busy.current) return;
    setSelectedId(deal.name);
    setDetail(preview ? { deal, canEdit: true } : null);
    setMode("detail");
    if (preview) return;

    try {
      const [record, { canEdit }] = await Promise.all([
        getDeal(deal.name),
        getDealCapabilities(deal.name).catch(() => ({ canEdit: false })),
      ]);
      setDetail({ id: deal.name, deal: record, canEdit });
    } catch (error) {
      setDetail({ id: deal.name, error: error.message });
    }
  }

  function close() {
    if (!busy.current) setMode(null);
  }

  async function saveDeal(value) {
    if (busy.current) return;
    busy.current = true;
    setSaving(true);
    try {
      const record = preview
        ? { ...value, name: selectedId || `${TEMP_ID_PREFIX}${Date.now()}` }
        : await persistDeal(selectedId, value);
      setDeals((previous) => selectedId
        ? previous.map((deal) => deal.name === record.name ? record : deal)
        : [record, ...previous]);
      setMessage(preview ? "Đã lưu trong bản xem trước." : "Đã lưu Deal vào Frappe.");
      setSelectedId(null);
      setMode(null);
    } finally {
      busy.current = false;
      setSaving(false);
    }
  }

  async function changeStatus(name, status) {
    if (busy.current || !canMove || !stageNames.includes(status)) return;
    busy.current = true;
    setSaving(true);
    setError("");
    try {
      const record = preview ? { ...deals.find((deal) => deal.name === name), status } : await updateDealStage(name, status);
      setDeals((previous) => previous.map((deal) => deal.name === name ? record : deal));
      setMessage("Đã chuyển giai đoạn.");
    } catch (error) {
      setError(error.message);
    } finally {
      busy.current = false;
      setSaving(false);
    }
  }

  const currentDetail = preview || detail?.id === selectedId ? detail : null;
  const columns = [
    {
      key: "name",
      label: "Cơ hội bán hàng",
      render: (value, deal) => (
        <div className="deal-table-name">
          <span className="deal-table-avatar" aria-hidden="true"><BriefcaseBusiness size={17} /></span>
          <div className="deal-table-name-text">
            <strong>{deal.title || value}</strong>
            <span>{value}</span>
          </div>
        </div>
      ),
    },
    {
      key: "lead",
      label: "Khách hàng / nhân viên",
      render: (value, deal) => (
        <div className="deal-table-stack">
          <strong>{value || "Chưa liên kết Lead"}</strong>
          <span>{deal.ownerDisplay || "Chưa phân công"}</span>
        </div>
      ),
    },
    { key: "expected_deal_value", label: "Giá trị dự kiến", render: (value, deal) => <strong className="deal-table-amount">{formatVnd(value, deal.currency)}</strong> },
    { key: "deal_value", label: "Giá trị Deal", render: (value, deal) => <span className="deal-table-actual">{formatVnd(value, deal.currency)}</span> },
    { key: "status", label: "Giai đoạn", render: (status) => <StatusBadge status={status} /> },
  ];

  const hasFilters = Boolean(search.trim()) || statusFilter !== "all";

  return (
    <div className="deals-ui">
      <header className="deals-header">
        <div className="deals-header-copy">
          <div className="deals-eyebrow"><span className="deals-eyebrow-line" /> SALES CRM <span className="deals-eyebrow-separator">/</span> DEAL MANAGEMENT</div>
          <h1>Quản lý <span>Deal</span></h1>
          <p>Theo dõi cơ hội bán hàng, quản lý pipeline và tiến độ chốt giao dịch.</p>
        </div>
        <Button className="deals-add-button" disabled={!canCreate || saving} onClick={openNew}>
          <Plus size={18} strokeWidth={2.3} /> Thêm Deal mới
        </Button>
      </header>

      <section className="deals-overview" aria-label="Tổng quan cơ hội bán hàng">
        <SummaryCard icon={BriefcaseBusiness} label="Tổng số Deal" value={loading || (error && !options.statuses.length) ? "—" : summary.total} helper="Toàn bộ cơ hội" />
        <SummaryCard icon={Clock3} label="Đang theo dõi" value={loading || !statuses.length ? "—" : summary.active} helper="Chưa Won / Lost" variant="blue" />
        <SummaryCard icon={CheckCircle2} label="Đã chốt thành công" value={loading || !statuses.length ? "—" : summary.won} helper="Trạng thái Won" variant="green" />
        <SummaryCard icon={CircleDollarSign} label="Giá trị pipeline" value={formatVnd(loading || !statuses.length ? null : summary.expectedOpen)} helper="Giá trị dự kiến của Deal đang mở" variant="red" />
      </section>

      {preview && (
        <div className="deals-demo-notice" role="note">
          <span className="deals-demo-icon"><Info size={16} /></span>
          <p>Bản xem trước với dữ liệu mẫu trong phiên trang.</p>
        </div>
      )}
      {error && <p role="alert" className="text-primary">{error}</p>}

      <section className="deals-workspace" aria-label="Danh sách và pipeline Deal">
        <div className="deals-workspace-header">
          <div>
            <h2>Cơ hội bán hàng</h2>
            <p>Quản lý và cập nhật từng cơ hội trong quy trình bán hàng.</p>
          </div>
          <span className="deals-count"><span className="deals-count-dot" /> {filtered.length} / {deals.length} Deal</span>
        </div>

        <div className="deals-toolbar">
          <div className="deals-search">
            <Search size={19} aria-hidden="true" />
            <input
              aria-label="Tìm kiếm Deal"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Tìm cơ hội, mã Deal, Lead hoặc nhân viên..."
            />
            {search && (
              <button type="button" onClick={() => setSearch("")} className="deals-search-clear" aria-label="Xóa từ khóa tìm kiếm"><X size={16} /></button>
            )}
          </div>
          <div className="deals-filter">
            <SlidersHorizontal size={18} aria-hidden="true" />
            <select aria-label="Lọc Deal theo giai đoạn" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">Tất cả giai đoạn</option>
              {stageNames.map((status) => <option key={status} value={status}>{STATUS_LABELS[status] || status}</option>)}
            </select>
          </div>
          <div className="deals-view-switch" role="group" aria-label="Chọn chế độ xem Deal">
            <button type="button" aria-pressed={view === "list"} className={view === "list" ? "is-active" : ""} onClick={() => setView("list")}><List size={17} /> Danh sách</button>
            <button type="button" aria-pressed={view === "board"} className={view === "board" ? "is-active" : ""} onClick={() => setView("board")}><Columns3 size={17} /> Pipeline</button>
          </div>
        </div>

        {hasFilters && (
          <div className="deals-active-filters">
            <span>Đang lọc kết quả</span>
            <button type="button" onClick={() => { setSearch(""); setStatusFilter("all"); }}>Xóa bộ lọc <X size={14} /></button>
          </div>
        )}

        {message && (
          <div className="deals-feedback" role="status"><CheckCircle2 size={18} /><span>{message}</span><button type="button" onClick={() => setMessage("")} aria-label="Đóng thông báo"><X size={16} /></button></div>
        )}

        {view === "list" ? (
          <div className="deals-table">
            <Table
              columns={columns}
              data={filtered}
              loading={loading}
              getRowKey={(deal) => deal.name}
              onRowClick={openDetail}
              emptyMessage="Không tìm thấy Deal phù hợp. Hãy thử bộ lọc khác hoặc thêm Deal mới."
            />
          </div>
        ) : (
          <DealBoard deals={filtered} statuses={stageNames} disabled={!canMove || saving} onOpenDetail={openDetail} onChangeStatus={changeStatus} />
        )}

        <div className="deals-workspace-footer">
          <span>Chọn một Deal để xem thông tin chi tiết</span>
          <span className="deals-footer-mark">Customer 360 <ArrowUpRight size={14} /></span>
        </div>
      </section>

      <Modal isOpen={mode !== null} onClose={close} size="lg" title={mode === "detail" ? "Chi tiết Deal" : selected ? "Chỉnh sửa Deal" : "Tạo Deal mới"}>
        {mode === "detail" ? (
          (currentDetail?.error ? <p role="alert">{currentDetail.error}</p> : currentDetail?.deal ? <DealDetail deal={currentDetail.deal} onEdit={currentDetail.canEdit ? () => setMode("form") : undefined} /> : <p role="status">Đang tải Deal…</p>)
        ) : mode === "form" ? (
          <DealForm key={selectedId || "new"} initialValue={selectedId ? currentDetail?.deal ?? selected : null} statuses={stageNames} preview={preview} onSave={saveDeal} onCancel={close} />
        ) : null}
      </Modal>
    </div>
  );
}
