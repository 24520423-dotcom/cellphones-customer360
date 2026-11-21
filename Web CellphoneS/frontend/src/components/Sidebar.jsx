import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Handshake,
  ContactRound,
  Headset,
  ChartNoAxesCombined,
  Shield,
  PanelLeftClose,
  PanelLeftOpen,
  X,
} from "lucide-react";
import { crmRoutes } from "../routes/crmRoutes";

const icons = {
  "/dashboard": LayoutDashboard,
  "/leads": Users,
  "/deals": Handshake,
  "/customers": ContactRound,
  "/after-sales": Headset,
  "/analytics": ChartNoAxesCombined,
  "/admin": Shield,
};

export default function Sidebar({
  onNavigate,
  collapsed = false,
  onToggle,
  onClose,
  hasPermission = () => false,
  previewMode = false,
}) {
  const ToggleIcon = collapsed ? PanelLeftOpen : PanelLeftClose;
  const menuItems = previewMode ? crmRoutes.filter(({ path }) => path !== "/admin") : crmRoutes.filter(({ permission }) => !permission || hasPermission(permission));

  return (
    <aside className="flex h-full w-full flex-col bg-ink text-white">
      <div className={`flex min-h-20 items-center justify-between gap-2 border-b border-white/15 py-3 ${collapsed ? "px-3" : "px-5"}`}>
        {!collapsed && <span className="text-xl font-bold">Cellphone<span className="text-brand-highlight">S</span></span>}
        {onToggle && (
          <button type="button" onClick={onToggle} aria-expanded={!collapsed}
            aria-label={collapsed ? "Mở rộng sidebar" : "Thu gọn sidebar"}
            className="mx-auto rounded-lg p-2 hover:bg-white/10">
            <ToggleIcon size={20} aria-hidden="true" />
          </button>
        )}
        {onClose && (
          <button type="button" onClick={onClose} aria-label="Đóng menu" className="rounded-lg p-2 hover:bg-white/10">
            <X size={20} aria-hidden="true" />
          </button>
        )}
      </div>
      <nav aria-label="Module CRM" className="flex-1 space-y-2 overflow-y-auto p-3">
        {menuItems.map(({ label, path }) => {
          const Icon = icons[path];
          if (previewMode && path !== "/customers") return (
            <div key={path} title="Module cần đăng nhập Frappe CRM"
              className={`flex cursor-not-allowed items-center gap-3 rounded-lg py-3 text-sm text-gray-500 ${collapsed ? "justify-center" : "px-3"}`}>
              <Icon size={19} className="shrink-0" aria-hidden="true" />
              {!collapsed && <span>{label}</span>}
            </div>
          );
          return (
            <NavLink
              key={path}
              to={previewMode ? "/preview/customers" : path}
              onClick={onNavigate}
              aria-label={label}
              title={collapsed ? label : undefined}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg py-3 text-sm transition ${collapsed ? "justify-center" : "px-3"} ${
                  isActive ? "bg-primary text-white" : "text-gray-300 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              <Icon size={19} className="shrink-0" aria-hidden="true" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
