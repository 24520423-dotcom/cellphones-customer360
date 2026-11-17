
import { Bell, UserCircle } from "lucide-react";

export default function Header() {
  return (
    <header className="flex h-20 items-center justify-between border-b border-slate-200 bg-white px-8">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">
          Customer 360 Management
        </h2>
        <p className="text-sm text-slate-500">
          Hệ thống quản lý quan hệ khách hàng CellphoneS
        </p>
      </div>

      <div className="flex items-center gap-5">
        <Bell size={22} className="text-slate-600" />

        <div className="flex items-center gap-2">
          <UserCircle size={30} className="text-slate-600" />
          <span className="text-sm font-medium text-slate-700">
            Nhân viên CRM
          </span>
        </div>
      </div>
    </header>
  );
}
