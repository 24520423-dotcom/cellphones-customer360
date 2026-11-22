
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function LeadChart({ data }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-5 text-lg font-semibold text-slate-800">
        Lead by Status
      </h3>

      {data?.length ? <div className="h-72 min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" fill="#B91C1C" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div> : <p className="text-sm text-muted">Chưa có dữ liệu</p>}
    </div>
  );
}
