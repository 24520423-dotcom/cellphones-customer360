
import { Bell, UserCircle, Menu } from "lucide-react";

export default function Header({ onMenuClick }) {
  return (
    <header className="flex min-h-20 items-center justify-between gap-3 border-b border-gray-200 bg-white px-4 py-3 md:px-8">
      {/* Bên trái */}
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Mở menu"
          className="rounded-lg p-2 text-[#171717] hover:bg-red-50 md:hidden"
        >
          <Menu size={24} />
        </button>

        <div className="min-w-0">
          <h2 className="text-base font-semibold text-[#171717] md:text-xl">
            Customer 360 Management
          </h2>

          <p className="hidden text-sm text-gray-500 sm:block">
            Hệ thống quản lý khách hàng CellphoneS
          </p>
        </div>
      </div>

      {/* Bên phải */}
      <div className="flex shrink-0 items-center gap-3 md:gap-5">
        <Bell
          size={21}
          className="text-[#D70018]"
        />

        <div className="flex items-center gap-2">
          <UserCircle
            size={29}
            className="text-[#171717]"
          />

          <span className="hidden text-sm font-medium text-[#171717] lg:inline">
            Nhân viên CRM
          </span>
        </div>
      </div>
    </header>
  );
}
