
import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import Button from "../../components/Button";
import Table from "../../components/Table";
import Modal from "../../components/Modal";
import LeadForm from "./LeadForm";
import LeadDetail from "./LeadDetail";

const leadStatuses = [
  "Mới",
  "Đang tư vấn",
  "Đã liên hệ",
  "Đã chuyển đổi",
  "Không tiềm năng",
];

export default function LeadList() {
  // Ban đầu chưa có Lead nào
  const [leads, setLeads] = useState([]);

  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Tất cả");
  const [selected, setSelected] = useState(null);
  const [mode, setMode] = useState(null);
  const [notice, setNotice] = useState("");

  // Tìm kiếm và lọc Lead
  const filtered = useMemo(() => {
    return leads.filter((lead) => {
      const matchStatus =
        status === "Tất cả" || lead.status === status;

      const matchQuery = [
        lead.name,
        lead.phone,
        lead.email,
        lead.id,
      ].some((value) =>
        String(value || "")
          .toLowerCase()
          .includes(query.toLowerCase())
      );

      return matchStatus && matchQuery;
    });
  }, [leads, query, status]);

  // Mở form thêm Lead
  const openAdd = () => {
    setSelected(null);
    setNotice("");
    setMode("form");
  };

  // Mở chi tiết Lead
  const openDetail = (lead) => {
    setSelected(lead);
    setMode("detail");
  };

  // Lưu dữ liệu tạm thời trên Frontend
  const save = (value) => {
    if (selected) {
      setLeads((old) =>
        old.map((lead) =>
          lead.id === selected.id
            ? { ...lead, ...value }
            : lead
        )
      );

      setNotice("Đã cập nhật Lead trên giao diện.");
    } else {
      const newLead = {
        ...value,
        id: `LEAD-${Date.now()}`,
        history: [],
      };

      setLeads((old) => [newLead, ...old]);

      setNotice("Đã thêm Lead trên giao diện.");
    }

    setSelected(null);
    setMode(null);
  };

  // Cấu hình bảng
  const columns = [
    {
      key: "name",
      label: "Khách hàng",
      render: (value, row) => (
        <div>
          <strong className="text-ink">
            {value}
          </strong>
          <div className="text-xs text-muted">
            {row.id}
          </div>
        </div>
      ),
    },
    {
      key: "phone",
      label: "Điện thoại",
    },
    {
      key: "email",
      label: "Email",
    },
    {
      key: "source",
      label: "Nguồn",
    },
    {
      key: "status",
      label: "Trạng thái",
      render: (value) => (
        <span className="inline-block rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary">
          {value}
        </span>
      ),
    },
    {
      key: "owner",
      label: "Phụ trách",
    },
  ];

  return (
    <div className="space-y-5">
      {/* Tiêu đề */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">
            Quản lý Lead
          </h1>
          <p className="mt-1 text-sm text-muted">
            Theo dõi và quản lý khách hàng tiềm năng
          </p>
        </div>

        <Button onClick={openAdd}>
          <Plus size={17} />
          Thêm Lead
        </Button>
      </div>

      {/* Tìm kiếm và lọc */}
      <div className="crm-card flex flex-wrap items-end gap-3">
        <label className="min-w-[220px] flex-1 text-sm font-medium">
          Tìm kiếm
          <div className="relative mt-2">
            <Search
              size={17}
              className="absolute left-3 top-3 text-muted"
            />

            <input
              className="crm-input pl-10"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Tên, email, SĐT, mã Lead..."
            />
          </div>
        </label>

        <label className="text-sm font-medium">
          Trạng thái
          <select
            className="crm-input mt-2 min-w-[180px]"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="Tất cả">Tất cả</option>

            {leadStatuses.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Thông báo */}
      {notice && (
        <p
          role="status"
          className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800"
        >
          {notice} Dữ liệu sẽ mất khi tải lại trang.
        </p>
      )}

      {/* Số lượng Lead */}
      <p className="text-sm text-muted">
        Hiển thị {filtered.length}/{leads.length} Lead
        {" · "}
        Nhấn vào một dòng để xem chi tiết
      </p>

      {/* Bảng danh sách */}
      <Table
        columns={columns}
        data={filtered}
        getRowKey={(lead) => lead.id}
        onRowClick={openDetail}
        emptyMessage="Chưa có Lead nào. Nhấn Thêm Lead để bắt đầu."
      />

      {/* Modal thêm, sửa và xem chi tiết */}
      <Modal
        isOpen={mode !== null}
        onClose={() => setMode(null)}
        size="lg"
        title={
          mode === "detail"
            ? "Chi tiết Lead"
            : selected
              ? "Chỉnh sửa Lead"
              : "Thêm Lead mới"
        }
      >
        {mode === "detail" ? (
          <LeadDetail
            lead={selected}
            onEdit={() => setMode("form")}
          />
        ) : mode === "form" ? (
          <LeadForm
            initialValue={selected}
            onSave={save}
            onCancel={() => setMode(null)}
          />
        ) : null}
      </Modal>
    </div>
  );
}
