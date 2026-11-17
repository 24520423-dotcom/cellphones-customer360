
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
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Leads",
    path: "/leads",
    icon: Users,
  },
  {
    label: "Deals",
    path: "/deals",
    icon: Handshake,
  },
  {
    label: "Customers",
    path: "/customers",
    icon: ContactRound,
  },
  {
    label: "After-sales",
    path: "/after-sales",
    icon: Headset,
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: ChartNoAxesCombined,
  },
];

export default function Sidebar({ onNavigate }) {
  return (
    <aside className="flex h-full w-64 flex-col bg-[#171717] text-white">
      {/* Logo */}
      <div className="border-b border-[#333333] p-6">
        <h1 className="text-xl font-bold text-white">
          Cellphone<span className="text-[#D70018]">S</span>
        </h1>

        <p className="mt-1 text-xs text-gray-400">
          Customer 360 CRM
        </p>
      </div>

      {/* Menu */}
      <nav className="flex-1 space-y-2 overflow-y-auto p-4">
        {menuItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition ${
                isActive
                  ? "bg-[#D70018] text-white"
                  : "text-gray-300 hover:bg-[#333333] hover:text-white"
              }`
            }
          >
            <Icon size={19} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Đăng xuất */}
      <div className="border-t border-[#333333] p-4">
        <button
          type="button"
          disabled
          title="Chức năng sẽ được tích hợp sau"
          className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm text-gray-400"
        >
          <LogOut size={19} />
          Đăng xuất
        </button>
      </div>
    </aside>
  );
}
