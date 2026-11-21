import { useEffect, useRef, useState } from "react";
import { matchPath, Outlet, useLocation } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { useAuth } from "../hooks/useAuth";
import { crmRoutes } from "../routes/crmRoutes";

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const { pathname } = useLocation();
  const { session, hasPermission, logout } = useAuth();
  const drawer = useRef(null);
  const title = crmRoutes.find(({ path }) => matchPath(path, pathname))?.label
    || (pathname.startsWith("/customers/") ? "Customer 360" : undefined);

  useEffect(() => {
    if (!sidebarOpen) return;
    const dialog = drawer.current;
    dialog.showModal();
    const desktop = window.matchMedia("(min-width: 48rem)");
    function closeOnDesktop(event) {
      if (event.matches) setSidebarOpen(false);
    }

    desktop.addEventListener("change", closeOnDesktop);
    return () => {
      desktop.removeEventListener("change", closeOnDesktop);
      dialog.close();
    };
  }, [sidebarOpen]);

  return (
    <div className="min-h-dvh bg-background">
      <div className={`fixed inset-y-0 left-0 z-30 hidden md:block ${collapsed ? "w-18" : "w-64"}`}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} hasPermission={hasPermission} />
      </div>

      <dialog
        ref={drawer}
        id="mobile-navigation"
        aria-label="Điều hướng CRM"
        onClose={() => setSidebarOpen(false)}
        onClick={(event) => {
          if (event.target === event.currentTarget) setSidebarOpen(false);
        }}
        className="fixed inset-0 h-dvh max-h-none w-full max-w-none bg-transparent backdrop:bg-black/60"
      >
        <div className="h-full w-64 max-w-[85vw]">
          <Sidebar
            onClose={() => setSidebarOpen(false)}
            onNavigate={() => setSidebarOpen(false)}
            hasPermission={hasPermission}
          />
        </div>
      </dialog>

      <div className={`min-w-0 ${collapsed ? "md:ml-18" : "md:ml-64"}`}>
        <Header
          onMenuClick={() => setSidebarOpen(true)}
          sidebarOpen={sidebarOpen}
          title={title}
          user={session.user}
          logout={logout}
        />
        <main className="min-w-0 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
