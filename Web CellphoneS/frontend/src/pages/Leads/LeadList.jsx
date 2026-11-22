
import { useEffect, useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import Button from "../../components/Button";
import Table from "../../components/Table";
import Modal from "../../components/Modal";
import LeadForm from "./LeadForm";
import LeadDetail from "./LeadDetail";
import {
  listLeads,
  getLeadOptions,
  createLead,
  updateLead,
} from "../../services/leadService";

const leadStatuses = [
  "New",
  "Contacted",
  "Nurture",
  "Qualified",
  "Unqualified",
  "Converted",
  "Junk",
];

export default function LeadList() {
  // Ban đầu chưa có Lead nào
  const [leads, setLeads] = useState([]);

  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Tất cả");
  const [selected, setSelected] = useState(null);
  const [mode, setMode] = useState(null);
  const [notice, setNotice] = useState("");

  const [loading, setLoading] = useState(true);
const [error, setError] = useState("");
const [leadOptions, setLeadOptions] = useState({ statuses: [], canCreate: false });
const availableStatuses = [...new Set([...leadOptions.statuses, ...leads.map(({ status }) => status).filter((status) => status !== "—")])];

useEffect(() => {
  const controller = new AbortController();
  getLeadOptions(null, { signal: controller.signal }).then(
    (options) => { if (!controller.signal.aborted) setLeadOptions(options); },
    () => {},
  );
  return () => controller.abort();
}, []);

useEffect(() => {
  let active = true;

  async function loadLeads() {
    try {
      const data = await listLeads();

      if (active) {
        setLeads(data);
      }
    } catch (err) {
      if (active) {
        setError(
          `Không thể tải Lead từ Frappe. ${err.message}`
        );
      }
    } finally {
      if (active) {
        setLoading(false);
      }
    }
  }

  loadLeads();

  return () => {
    active = false;
  };
}, []);

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

  // Lưu vào Frappe và tải lại danh sách.

const save = async (value) => {
  setError("");

  try {
    if (selected) {
      await updateLead(selected.id, value);
    } else {
      await createLead(value);
    }
  } catch (err) {
    throw new Error(`Không thể lưu Lead: ${err.message}`, { cause: err });
  }

  setNotice(
    selected
      ? "Đã cập nhật Lead thành công trên Frappe."
      : "Đã thêm Lead thành công vào Frappe."
  );

  setSelected(null);
  setMode(null);

  try {
    const updatedLeads = await listLeads();
    setLeads(updatedLeads);
  } catch (err) {
    setError(
      `Đã lưu Lead thành công nhưng chưa tải lại được danh sách: ${err.message}`
    );
  }
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
    {loading && (
  <p role="status">Đang tải danh sách Lead từ Frappe...</p>
)}

{error && (
  <p role="alert" className="text-red-600">
    {error}
  </p>
)}
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

        <Button disabled={!leadOptions.canCreate || !availableStatuses.length} onClick={openAdd}>
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

            {(availableStatuses.length ? availableStatuses : leadStatuses).map((item) => (
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
          {notice}
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
            key={selected?.id || selected?.leadId || selected?.name || "new"}
            initialValue={selected}
            statuses={availableStatuses.length ? availableStatuses : leadStatuses}
            onSave={save}
            onCancel={() => setMode(null)}
          />
        ) : null}
      </Modal>
    </div>
  );
}
