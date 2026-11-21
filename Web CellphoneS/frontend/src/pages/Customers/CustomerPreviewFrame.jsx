import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../../components/Sidebar";
import Header from "../../components/Header";

// DEV-only preview uses the SAME shared Header and Sidebar as the application.
// It intentionally skips auth and only enables the Customer 360 navigation item.
export default function CustomerPreviewFrame() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  return (
    <div className="min-h-dvh bg-[#f7f8fa]">
      <div className={`fixed inset-y-0 left-0 z-40 hidden md:block ${collapsed ? "w-18" : "w-64"}`}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} previewMode />
      </div>
      {mobileMenu && (
        <div className="fixed inset-0 z-50 bg-black/40 md:hidden" onClick={() => setMobileMenu(false)}>
          <div className="h-full w-64" onClick={(event) => event.stopPropagation()}>
            <Sidebar previewMode onClose={() => setMobileMenu(false)} onNavigate={() => setMobileMenu(false)} />
          </div>
        </div>
      )}
      <div className={`min-w-0 ${collapsed ? "md:ml-18" : "md:ml-64"}`}>
        <Header onMenuClick={() => setMobileMenu(true)} sidebarOpen={mobileMenu} title="Khách hàng" previewMode />
        <main className="mx-auto max-w-[1480px] space-y-3 p-4 md:p-6 xl:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
