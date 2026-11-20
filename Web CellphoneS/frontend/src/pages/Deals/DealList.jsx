import { useMemo, useState } from "react";
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
import "./Deals.css";

const TEMP_ID_PREFIX = "TEMP-DEAL-";
const isActive = (deal) => !["Won", "Lost"].includes(deal.status);

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

export default function DealList() {
  // K02: chỉ sử dụng dữ liệu demo trong React state, KHÔNG lấy/lưu vào Frappe.
  const [deals, setDeals] = useState(() => INITIAL_MOCK_DEALS.map((deal) => ({ ...deal })));
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [view, setView] = useState("list");
  const [selectedId, setSelectedId] = useState(null);
  const [mode, setMode] = useState(null); // null | "detail" | "form"
  const [message, setMessage] = useState("");

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

  const summary = useMemo(() => ({
    total: deals.length,
    active: deals.filter(isActive).length,
    won: deals.filter((deal) => deal.status === "Won").length,
    expectedOpen: deals.filter(isActive).reduce((sum, deal) => {
      const amount = Number(deal.expected_deal_value);
      return sum + (Number.isFinite(amount) ? amount : 0);
    }, 0),
  }), [deals]);

  function openNew() {
    setSelectedId(null);
    setMode("form");
  }

  function openDetail(deal) {
    setSelectedId(deal.name);
    setMode("detail");
  }

  function saveDeal(value) {
    if (selectedId) {
      setDeals((previous) => previous.map((deal) => deal.name === selectedId
        ? { ...deal, ...value, name: deal.name }
        : deal));
      setMessage("Đã cập nhật Deal trên bản xem trước. Dữ liệu chưa lưu vào Frappe.");
    } else {
      // ID demo chỉ sử dụng ở K02; K03 phải lấy name do Frappe tạo.
      const name = `${TEMP_ID_PREFIX}${Date.now()}`;
      setDeals((previous) => [{ ...value, name }, ...previous]);
      setMessage("Đã thêm Deal vào bản xem trước. Dữ liệu chưa lưu vào Frappe.");
    }
    setSelectedId(null);
    setMode(null);
  }

  function changeStatus(name, status) {
    if (!DEAL_STATUSES.includes(status)) return;
    setDeals((previous) => previous.map((deal) => deal.name === name ? { ...deal, status } : deal));
    setMessage("Đã chuyển giai đoạn trong bản xem trước. Dữ liệu chưa lưu vào Frappe.");
  }

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
    { key: "expected_deal_value", label: "Giá trị dự kiến", render: (value) => <strong className="deal-table-amount">{formatVnd(value)}</strong> },
    { key: "deal_value", label: "Giá trị Deal", render: (value) => <span className="deal-table-actual">{formatVnd(value)}</span> },
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
        <Button className="deals-add-button" onClick={openNew}>
          <Plus size={18} strokeWidth={2.3} /> Thêm Deal mới
        </Button>
      </header>

      <section className="deals-overview" aria-label="Tổng quan cơ hội bán hàng">
        <SummaryCard icon={BriefcaseBusiness} label="Tổng số Deal" value={summary.total} helper="Toàn bộ cơ hội" />
        <SummaryCard icon={Clock3} label="Đang theo dõi" value={summary.active} helper="Chưa Won / Lost" variant="blue" />
        <SummaryCard icon={CheckCircle2} label="Đã chốt thành công" value={summary.won} helper="Trạng thái Won" variant="green" />
        <SummaryCard icon={CircleDollarSign} label="Giá trị pipeline" value={formatVnd(summary.expectedOpen)} helper="Giá trị dự kiến của Deal đang mở" variant="red" />
      </section>

      <div className="deals-demo-notice" role="note">
        <span className="deals-demo-icon"><Info size={16} /></span>
        <p><strong>Chế độ xem trước K02</strong> · Dữ liệu mẫu được lưu tạm trong phiên trang; tải lại sẽ trở về ban đầu. Chưa kết nối Frappe CRM.</p>
      </div>

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
              {DEAL_STATUSES.map((status) => <option key={status} value={status}>{STATUS_LABELS[status]}</option>)}
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
              getRowKey={(deal) => deal.name}
              onRowClick={openDetail}
              emptyMessage="Không tìm thấy Deal phù hợp. Hãy thử bộ lọc khác hoặc thêm Deal mới."
            />
          </div>
        ) : (
          <DealBoard deals={filtered} onOpenDetail={openDetail} onChangeStatus={changeStatus} />
        )}

        <div className="deals-workspace-footer">
          <span>Chọn một Deal để xem thông tin chi tiết</span>
          <span className="deals-footer-mark">Customer 360 <ArrowUpRight size={14} /></span>
        </div>
      </section>

      <Modal isOpen={mode !== null} onClose={() => setMode(null)} size="lg" title={mode === "detail" ? "Chi tiết Deal" : selected ? "Chỉnh sửa Deal" : "Tạo Deal mới"}>
        {mode === "detail" ? (
          <DealDetail deal={selected} onEdit={() => setMode("form")} />
        ) : mode === "form" ? (
          <DealForm key={selectedId || "new"} initialValue={selected} onSave={saveDeal} onCancel={() => setMode(null)} />
        ) : null}
      </Modal>
    </div>
  );
}
