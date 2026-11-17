
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Handshake,
  ContactRound,
  Headset,
  ChartNoAxesCombined,
  LogOut,
} from "lucide-react";

const menuItems = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { label: "Leads", path: "/leads", icon: Users },
  { label: "Deals", path: "/deals", icon: Handshake },
  { label: "Customers", path: "/customers", icon: ContactRound },
  { label: "After-sales", path: "/after-sales", icon: Headset },
  { label: "Analytics", path: "/analytics", icon: ChartNoAxesCombined },
];

export default function Sidebar() {
  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col bg-slate-900 text-white">
      <div className="border-b border-slate-700 p-6">
        <h1 className="text-xl font-bold">CellphoneS</h1>
        <p className="mt-1 text-xs text-slate-400">Customer 360 CRM</p>
      </div>

      <nav className="flex-1 space-y-2 p-4">
        {menuItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition ${
                isActive
                  ? "bg-red-600 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`
            }
          >
            <Icon size={19} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-700 p-4">
        <button
          type="button"
          disabled
          title="Sẽ kết nối đăng xuất khi tích hợp Authentication"
          className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm text-slate-400"
        >
          <LogOut size={19} />
          Đăng xuất
        </button>
      </div>
    </aside>
  );
}
