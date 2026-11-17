
import { useState } from "react";
import { Outlet } from "react-router-dom";

import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#F5F5F5]">
      {/* Sidebar trên laptop */}
      <div className="fixed inset-y-0 left-0 z-30 hidden w-64 md:block">
        <Sidebar />
      </div>

      {/* Sidebar trên điện thoại */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          {/* Nền tối khi mở menu */}
          <button
            type="button"
            aria-label="Đóng menu"
            className="absolute inset-0 bg-black/60"
            onClick={() => setSidebarOpen(false)}
          />

          <div className="relative h-full w-64">
            <Sidebar
              onNavigate={() => setSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Khu vực nội dung */}
      <div className="min-w-0 md:ml-64">
        <Header
          onMenuClick={() => setSidebarOpen(true)}
        />

        <main className="min-w-0 p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
