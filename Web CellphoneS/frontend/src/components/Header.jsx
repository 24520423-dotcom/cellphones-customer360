import { LogOut, Menu, UserCircle } from "lucide-react";
import { useState } from "react";

export default function Header({ onMenuClick, sidebarOpen, title, user, logout }) {
  const [logoutPending, setLogoutPending] = useState(false);
  const [logoutError, setLogoutError] = useState(false);

  async function handleLogout() {
    setLogoutPending(true);
    setLogoutError(false);
    try {
      await logout();
    } catch {
      setLogoutError(true);
    } finally {
      setLogoutPending(false);
    }
  }

  return (
    <header className="flex min-h-20 flex-wrap items-center justify-between gap-3 border-b border-border bg-white px-4 py-3 md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Mở menu"
          aria-expanded={sidebarOpen}
          aria-controls={sidebarOpen ? "mobile-navigation" : undefined}
          className="rounded-lg p-2 text-ink hover:bg-primary-soft md:hidden"
        >
          <Menu size={24} aria-hidden="true" />
        </button>
        <div className="min-w-0">
          <p className="text-xs font-bold text-primary sm:text-sm">CellphoneS Customer 360</p>
          <p className="text-lg font-semibold text-ink">{title}</p>
        </div>
      </div>

      <div className="flex min-w-0 flex-wrap items-center gap-3">
        {user && (
          <div className="flex min-w-0 items-center gap-2 text-sm text-ink">
            <UserCircle size={22} className="shrink-0" aria-hidden="true" />
            <span className="break-all">{user.displayName || user.id}</span>
          </div>
        )}
        <button
          type="button"
          disabled={!logout || logoutPending}
          onClick={handleLogout}
          title={logout ? undefined : "Đăng xuất sẽ được tích hợp với Frappe"}
          className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm text-ink enabled:hover:bg-primary-soft disabled:opacity-50"
        >
          <LogOut size={16} aria-hidden="true" />
          Đăng xuất
        </button>
        {logoutError && <p role="alert" className="text-sm text-primary">Không thể đăng xuất. Vui lòng thử lại.</p>}
      </div>
    </header>
  );
}
