import Table from "../../components/Table";
import { displayDateTime } from "../../utils/customer360";

const columns = [
  { key: "type", label: "Loại" },
  { key: "title", label: "Nội dung" },
  { key: "customer", label: "Khách hàng" },
  { key: "employee", label: "Nhân viên" },
  { key: "date", label: "Thời gian", render: displayDateTime },
  { key: "status", label: "Trạng thái" },
];

export default function RecentActivities({ activities }) {
  return (
    <section className="crm-card min-w-0 space-y-4" aria-labelledby="recent-activities">
      <h2 id="recent-activities" className="text-lg font-semibold">Hoạt động gần đây</h2>
      <Table data={activities} columns={columns} emptyMessage="Chưa có hoạt động trong kỳ." />
    </section>
  );
}
