
import { useEffect, useId } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

export default function Modal({
  isOpen = false,
  onClose,
  title = "",
  children,
  footer,
  size = "md",
}) {
  const titleId = useId();

  const sizes = {
    sm: "max-w-sm",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
  };

  useEffect(() => {
    if (!isOpen) return;

    // Đóng Modal bằng phím Escape
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose?.();
      }
    };

    // Khóa cuộn trang khi Modal mở
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose?.();
        }
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        aria-label={title ? undefined : "Hộp thoại"}
        className={`
          flex max-h-[90vh] w-full flex-col
          overflow-hidden rounded-xl bg-white shadow-2xl
          ${sizes[size] || sizes.md}
        `}
      >
        {/* Tiêu đề */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2
            id={titleId}
            className="text-lg font-semibold text-[#171717]"
          >
            {title}
          </h2>

          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng hộp thoại"
            className="rounded-lg p-2 text-gray-500 transition hover:bg-red-50 hover:text-[#D70018]"
          >
            <X size={20} />
          </button>
        </div>

        {/* Nội dung */}
        <div className="overflow-y-auto px-6 py-5">
          {children}
        </div>

        {/* Các nút thao tác */}
        {footer && (
          <div className="flex flex-wrap justify-end gap-3 border-t border-gray-200 px-6 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}
