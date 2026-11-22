import useAnalytics from "../../hooks/useAnalytics";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import Table from "../../components/Table";
import DashboardFilters from "../Dashboard/DashboardFilters";
import KPICard from "../Dashboard/KPICard";

const sections = [
  ["customers", "Khách hàng", [
    ["total", "Tổng khách hàng", "Số hồ sơ được phép xem, tính đến cuối kỳ."],
    ["new", "Khách hàng mới", "Hồ sơ tạo trong kỳ."],
    ["withOrders", "Khách hàng có đơn", "Khách có ít nhất một đơn hợp lệ trong kỳ."],
    ["repeat", "Khách hàng mua lại", "Khách có ít nhất hai đơn hợp lệ trong kỳ."],
  ], [["bySource", "Kênh nguồn"], ["byType", "Loại khách hàng"]]],
  ["leads", "Lead", [["total", "Tổng Lead", "Lead tạo trong kỳ."]], [["byStatus", "Trạng thái Lead"], ["bySource", "Nguồn Lead"]]],
  ["deals", "Deal", [
    ["total", "Tổng Deal", "Deal tạo trong kỳ."],
    ["won", "Deal Won", "Deal trong kỳ đang ở trạng thái Won."],
    ["lost", "Deal Lost", "Deal trong kỳ đang ở trạng thái Lost."],
    ["pipelineValue", "Giá trị pipeline", "Tổng giá trị các Deal còn mở trong kỳ.", "money"],
    ["winRate", "Tỷ lệ thắng Deal", "Won / (Won + Lost) trong nhóm Deal tạo trong kỳ.", "percent"],
    ["conversionRate", "Tỷ lệ Lead chuyển đổi", "Lead tạo trong kỳ có ít nhất một Deal thắng tạo trong cùng kỳ, chia cho tổng Lead tạo trong kỳ.", "percent"],
  ], [["byStage", "Giai đoạn Deal"]]],
  ["orders", "Đơn hàng", [
    ["total", "Tổng số đơn", "Đơn theo ngày đặt, gồm mọi trạng thái."],
    ["validValue", "Giá trị đơn hợp lệ", "Tổng giá trị đơn đã xác nhận, đang xử lý hoặc hoàn tất.", "money"],
    ["averageValue", "Giá trị đơn trung bình", "Giá trị đơn hợp lệ chia cho số đơn hợp lệ.", "money"],
    ["repeatCustomers", "Khách mua nhiều lần", "Khách có ít nhất hai đơn hợp lệ trong kỳ."],
  ], [["byStatus", "Trạng thái đơn"], ["trend", "Xu hướng đơn hàng"]]],
  ["tickets", "Hậu mãi", [
    ["total", "Tổng Ticket", "Yêu cầu tạo trong kỳ."],
    ["resolutionRate", "Tỷ lệ giải quyết", "Ticket Resolved hoặc Closed chia cho tổng Ticket trong kỳ.", "percent"],
    ["averageResolutionHours", "Thời gian xử lý trung bình", "Số giờ từ tạo đến giải quyết, tính trên Ticket có đủ mốc thời gian."],
  ], [["byStatus", "Trạng thái Ticket"], ["byType", "Loại yêu cầu"], ["trend", "Xu hướng phát sinh"]]],
];

const number = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat("vi-VN", { style: "percent", maximumFractionDigits: 1 });

function format(value, kind) {
  if (value == null) return <span className="text-sm font-medium text-muted">Chưa có dữ liệu</span>;
  if (kind === "percent") return percent.format(value);
  if (kind === "money") return number.format(value) + " ₫";
  return number.format(value);
}

const columns = [{ key: "label", label: "Nhóm" }, { key: "count", label: "Số lượng", render: (value) => number.format(value) }];

function Breakdown({ rows, title }) {
  return (
    <div className="crm-card min-w-0 space-y-4">
      <h3 className="font-semibold">{title}</h3>
      {rows?.length ? (
        <>
          <div className="h-60 w-full" role="img" aria-label={title}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" minTickGap={16} />
                <YAxis allowDecimals={false} />
                <Tooltip formatter={(value) => [number.format(value), "Số lượng"]} />
                <Legend />
                <Bar dataKey="count" name="Số lượng" fill="#d70018" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <Table columns={columns} data={rows} getRowKey={({ label }) => label} />
        </>
      ) : <p className="text-sm text-muted">Chưa có dữ liệu</p>}
    </div>
  );
}

export default function Analytics() {
  const { period, setPeriod, reload, loading, result, error } = useAnalytics();

  return (
    <div className="min-w-0 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-ink">Phân tích khách hàng</h1>
        <div className="flex flex-wrap items-center gap-2">
          <DashboardFilters period={period} onPeriodChange={setPeriod} />
          <Button variant="secondary" onClick={reload}>Tải lại dữ liệu</Button>
        </div>
      </div>
      {loading && <Loading label="Đang tải dữ liệu phân tích…" />}
      {error && <p role="alert" className="rounded-lg bg-primary-soft p-4 text-primary">Không thể tải dữ liệu phân tích. {error}</p>}
      {!result && !loading && !error && <p className="text-sm text-muted">Chưa có dữ liệu trong kỳ.</p>}
      {!loading && !error && sections.map(([key, title, metrics, charts]) => (
        <section key={key} aria-labelledby={`analytics-${key}`} className="space-y-3">
          <h2 id={`analytics-${key}`} className="text-lg font-semibold">{title}</h2>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map(([metric, label, description, kind]) => (
              <KPICard key={metric} title={label} value={format(result?.[key]?.[metric], kind)} description={description} />
            ))}
          </div>
          <div className="grid min-w-0 gap-3 xl:grid-cols-2">
            {charts.map(([chart, title]) => <Breakdown key={chart} title={title} rows={result?.[key]?.[chart]} />)}
          </div>
        </section>
      ))}
    </div>
  );
}
