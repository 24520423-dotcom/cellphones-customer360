
export default function DashboardFilters({
  period,
  onPeriodChange,
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <label
        htmlFor="dashboard-period"
        className="text-sm font-medium text-slate-600"
      >
        Thời gian:
      </label>

      <select
        id="dashboard-period"
        value={period}
        onChange={(e) => onPeriodChange(e.target.value)}
        className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm"
      >
        <option value="all">Tất cả</option>
        <option value="7d">7 ngày gần nhất</option>
        <option value="30d">30 ngày gần nhất</option>
        <option value="90d">90 ngày gần nhất</option>
      </select>
    </div>
  );
}
