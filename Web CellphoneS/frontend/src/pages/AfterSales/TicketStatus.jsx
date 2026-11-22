import { REQUEST_STATUS_LABELS } from "../../utils/customer360";

const styles = {
  Open: "bg-primary-soft text-primary",
  "In Progress": "bg-blue-100 text-blue-800",
  Pending: "bg-amber-100 text-amber-900",
  Resolved: "bg-green-100 text-green-800",
};

export default function TicketStatus({ status }) {
  if (!status) return "—";
  return (
    <span className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${styles[status] ?? "bg-gray-100 text-ink"}`}>
      {status === "Pending" ? "Đang chờ" : REQUEST_STATUS_LABELS[status] ?? status}
    </span>
  );
}
