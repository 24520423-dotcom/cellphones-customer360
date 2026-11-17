
export default function KPICard({ title, value, icon: Icon, description }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">
          {title}
        </p>

        {Icon && <Icon size={22} className="text-red-600" />}
      </div>

      <h2 className="mt-4 text-3xl font-bold text-slate-800">
        {value}
      </h2>

      <p className="mt-2 text-sm text-slate-500">
        {description}
      </p>
    </div>
  );
}
