import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Clock3, Headset, Inbox, Plus } from "lucide-react";
import Button from "../../components/Button";
import AfterSalesList from "./AfterSalesList";
import Modal from "../../components/Modal";
import AfterSalesForm from "./AfterSalesForm";
import { createTicket, getTicketCapabilities, listCustomersForTicket, listOrdersByCustomer, listTickets } from "../../services/afterSalesService";
import KPICard from "../Dashboard/KPICard";

const metrics = [
  { key: "total", title: "Tổng yêu cầu hỗ trợ", icon: Headset },
  { key: "open", title: "Đang mở", icon: Inbox },
  { key: "inProgress", title: "Đang xử lý", icon: Clock3 },
  { key: "resolved", title: "Đã giải quyết", icon: CheckCircle2 },
];

export default function AfterSales() {
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState(null);
  const [canCreate, setCanCreate] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const saving = useRef(false);
  const loading = result?.revision !== revision;
  const tickets = loading ? undefined : result?.tickets;
  const error = loading ? null : result?.error;
  const totals = tickets && {
    total: tickets.length,
    open: tickets.filter(({ status }) => status === "Open").length,
    inProgress: tickets.filter(({ status }) => status === "In Progress").length,
    resolved: tickets.filter(({ status }) => status === "Resolved").length,
  };

  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    listTickets(options).then(
      (tickets) => { if (!controller.signal.aborted) setResult({ revision, tickets }); },
      (error) => { if (!controller.signal.aborted) setResult({ revision, error: error.message }); },
    );
    getTicketCapabilities(null, options).then(
      ({ canCreate }) => { if (!controller.signal.aborted) setCanCreate(Boolean(canCreate)); },
      () => { if (!controller.signal.aborted) setCanCreate(false); },
    );
    return () => controller.abort();
  }, [revision]);

  function reload() {
    setRevision((value) => value + 1);
  }

  function closeForm() {
    if (!saving.current) setCreateOpen(false);
  }

  async function saveTicket(payload) {
    saving.current = true;
    try {
      const ticket = await createTicket(payload);
      setCreateOpen(false);
      setNotice(`Đã tạo yêu cầu ${ticket.id}.`);
      reload();
    } finally {
      saving.current = false;
    }
  }
  return (
    <div className="min-w-0 space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-ink">Quản lý hậu mãi</h1>
        <div className="flex flex-col gap-1 sm:items-end">
          <Button disabled={!canCreate} onClick={() => { setNotice(""); setCreateOpen(true); }}>
            <Plus size={18} aria-hidden="true" />
            Tạo yêu cầu hỗ trợ
          </Button>
        </div>
      </div>

      <section aria-label="Thống kê nhanh" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ key, title, icon }) => (
          <KPICard
            key={key}
            title={title}
            icon={icon}
            value={totals?.[key]?.toLocaleString("vi-VN") ?? (
              <span className="text-sm font-medium text-muted">Chưa có dữ liệu</span>
            )}
          />
        ))}
      </section>

      {notice && <p role="status" className="text-sm font-medium text-green-800">{notice}</p>}
      <AfterSalesList tickets={tickets} loading={loading} error={error} onRetry={reload} />
      {createOpen && (
        <Modal isOpen title="Tạo yêu cầu hỗ trợ" onClose={closeForm} size="lg">
          <AfterSalesForm loadCustomers={listCustomersForTicket} loadOrders={listOrdersByCustomer} onSave={saveTicket} onClose={closeForm} />
        </Modal>
      )}
    </div>
  );
}
