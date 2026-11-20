
import { Clock3, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import StatusPage from "../StatusPage";

export default function PendingApproval() {
  return (
    <StatusPage title="Tài khoản đang chờ phê duyệt">
      <div className="text-center">

        {/* Biểu tượng chờ duyệt */}
        <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-primary-soft text-primary">
          <Clock3 size={38} />
        </div>

        {/* Thông báo trạng thái */}
        <p className="mb-4 text-sm leading-6 text-muted">
          Yêu cầu đăng ký tài khoản nhân viên CellphoneS
          của bạn đang chờ quản trị viên xét duyệt.
        </p>

        {/* Thông tin hướng dẫn */}
        <div className="mb-6 rounded-xl border border-gray-200 bg-gray-50 p-4 text-left">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-800">
            <ShieldCheck size={18} className="text-primary" />
            Thông tin phê duyệt
          </div>

          <p className="text-sm leading-6 text-gray-600">
            Sau khi tài khoản được quản trị viên phê duyệt,
            bạn có thể đăng nhập để sử dụng hệ thống
            Customer 360.
          </p>
        </div>

        {/* Nút quay lại */}
        <Link
          to="/login"
          className="inline-block rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-primary-hover"
        >
          Quay lại đăng nhập
        </Link>

        <p className="mt-4 text-xs text-muted">
          CellphoneS Customer 360 · Cổng quản trị nhân viên
        </p>
      </div>
    </StatusPage>
  );
}
