import { CheckCircle2, CircleAlert, Info } from "lucide-react";

const colors = {
  high: "text-[#c7353f] bg-[#fff4f5]",
  medium: "text-[#9a6700] bg-[#fffaec]",
  low: "text-gray-600 bg-gray-100",
};

export default function CustomerAlerts({ alerts, timelinePending }) {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e4e7eb] bg-white" aria-labelledby="customer-alerts-heading">
      <div className="flex items-center justify-between border-b border-[#edf0f2] px-4 py-3">
        <h2 id="customer-alerts-heading" className="text-[13px] font-semibold text-gray-900">Việc cần chú ý</h2>
        <span className="rounded-md bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600">{alerts.length}</span>
      </div>
      {!alerts.length ? (
        <div className="flex items-start gap-2.5 px-4 py-4 text-[13px] text-gray-600">
          <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-emerald-600" aria-hidden="true" />
          <span>{timelinePending ? "Đang kiểm tra dữ liệu tương tác…" : "Chưa ghi nhận việc cần ưu tiên theo các quy tắc hiện có."}</span>
        </div>
      ) : (
        <ol className="divide-y divide-[#edf0f2]">
          {alerts.map((alert) => {
            const Icon = alert.level === "low" ? Info : CircleAlert;
            return (
              <li key={alert.id} className="px-4 py-3.5">
                <div className="flex items-start gap-2.5">
                  <span className={`mt-0.5 rounded-md p-1.5 ${colors[alert.level] || colors.low}`}><Icon size={15} aria-hidden="true" /></span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] font-semibold leading-5 text-gray-900">{alert.title}</p>
                    <p className="mt-1 text-xs leading-5 text-gray-600">{alert.detail}</p>
                    <details className="mt-1.5 text-[11px] text-gray-500">
                      <summary className="cursor-pointer font-medium hover:text-primary">Xem căn cứ & cách tính</summary>
                      <p className="mt-1 leading-relaxed">{alert.rule}</p>
                      <p className="mt-1 leading-relaxed">Nguồn: {alert.source}</p>
                    </details>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}
      {timelinePending && alerts.length > 0 && <p className="border-t border-[#edf0f2] px-4 py-2 text-[11px] text-gray-500">Đang kiểm tra thêm lịch sử tương tác.</p>}
    </section>
  );
}
