import { CircleCheck, Handshake, TrendingUp, Users } from "lucide-react";
import useAnalytics from "../../hooks/useAnalytics";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import RecentActivities from "./RecentActivities";
import KPICard from "./KPICard";
import LeadChart from "./LeadChart";
import DealChart from "./DealChart";
import DashboardFilters from "./DashboardFilters";

const number = new Intl.NumberFormat("vi-VN");
const percentage = new Intl.NumberFormat("vi-VN", { style: "percent", maximumFractionDigits: 1 });

function metric(value, formatter = number) {
  return value == null ? <span className="text-sm text-muted">Chưa có dữ liệu</span> : formatter.format(value);
}

export default function Dashboard() {
  const { period, setPeriod, reload, loading, result, error } = useAnalytics(true);
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-ink">Dashboard</h1>
        <div className="flex flex-wrap items-center gap-2">
          <DashboardFilters period={period} onPeriodChange={setPeriod} />
          <Button variant="secondary" onClick={reload}>Tải lại dữ liệu</Button>
        </div>
      </div>
      {loading && <Loading label="Đang tải dữ liệu tổng quan…" />}
      {error && <p role="alert" className="rounded-lg bg-primary-soft p-4 text-primary">Không thể tải dữ liệu tổng quan. {error}</p>}
      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
            <KPICard title="Total Leads" value={metric(result?.leads?.total)} icon={Users} description="Lead tạo trong kỳ." />
            <KPICard title="Total Deals" value={metric(result?.deals?.total)} icon={Handshake} description="Deal tạo trong kỳ." />
            <KPICard title="Won Deals" value={metric(result?.deals?.won)} icon={CircleCheck} description="Deal tạo trong kỳ đang ở giai đoạn thắng." />
            <KPICard title="Conversion Rate" value={metric(result?.deals?.conversionRate, percentage)} icon={TrendingUp} description="Lead tạo trong kỳ có ít nhất một Deal thắng tạo trong cùng kỳ, chia cho tổng Lead tạo trong kỳ." />
          </div>
          <div className="grid min-w-0 grid-cols-1 gap-6 xl:grid-cols-2">
            <LeadChart data={result?.leads?.byStatus} />
            <DealChart data={result?.deals?.byStage} />
          </div>
          <RecentActivities activities={result?.activities} />
        </>
      )}
    </div>
  );
}
