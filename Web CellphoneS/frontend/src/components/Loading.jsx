import { LoaderCircle } from "lucide-react";

export default function Loading({ label = "Đang kiểm tra phiên…" }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 p-8 text-muted">
      <LoaderCircle size={20} className="text-primary motion-safe:animate-spin" aria-hidden="true" />
      {label}
    </div>
  );
}
