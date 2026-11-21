import { CalendarDays, Mail, Phone, UserRound } from "lucide-react";
import { DemoBadge } from "./CustomerStates";
import { displayDate, initials, maskEmail, maskPhone } from "../../utils/customer360";

// L02: compact, single source of truth for the customer identity.
export default function CustomerInfo({ customer, isDemo }) {
  const fields = [
    { label: "Điện thoại", value: maskPhone(customer.phone), icon: Phone },
    { label: "Email", value: maskEmail(customer.email), icon: Mail },
    { label: "Phụ trách", value: customer.owner, icon: UserRound },
    { label: "Cập nhật gần nhất", value: displayDate(customer.updated_at), icon: CalendarDays },
  ];

  return (
    <section className="overflow-hidden rounded-xl border border-[#e4e7eb] bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]" aria-labelledby="customer-name">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-5">
        <div className="flex min-w-0 items-center gap-3.5">
          <span aria-hidden="true" className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#fff0f1] text-sm font-bold text-primary">
            {initials(customer.display_name)}
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 id="customer-name" className="break-words text-[22px] font-bold tracking-tight text-ink">{customer.display_name}</h1>
              {isDemo && <DemoBadge />}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
              <span className="font-mono">{customer.customer_id}</span>
              <span className="text-gray-300" aria-hidden="true">·</span>
              <span>{customer.segments.length ? customer.segments.join(", ") : "Chưa phân khúc"}</span>
            </div>
          </div>
        </div>
        <p className="rounded-md border border-[#e9edf1] bg-[#f8fafb] px-3 py-1.5 text-[11px] text-gray-500">
          Hồ sơ Customer 360
        </p>
      </div>
      <dl className="grid gap-x-5 gap-y-3 border-t border-[#edf0f2] bg-[#fcfcfd] px-5 py-3.5 sm:grid-cols-2 xl:grid-cols-4">
        {fields.map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex min-w-0 items-start gap-2.5">
            <Icon size={15} className="mt-0.5 shrink-0 text-gray-400" aria-hidden="true" />
            <div className="min-w-0">
              <dt className="text-[11px] text-gray-500">{label}</dt>
              <dd className="mt-0.5 break-words text-[13px] font-medium text-gray-800">{value || "Chưa có"}</dd>
            </div>
          </div>
        ))}
      </dl>
    </section>
  );
}
