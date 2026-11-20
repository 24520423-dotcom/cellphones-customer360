
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Pencil, History } from "lucide-react";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import LeadForm from "./LeadForm";

const fields = [
  "Mã Lead",
  "Họ và tên",
  "Số điện thoại",
  "Email",
  "Nguồn Lead",
  "Trạng thái",
  "Nhân viên phụ trách",
  "Ghi chú",
];

export default function LeadDetail() {
  const navigate = useNavigate();
  const [showEdit, setShowEdit] = useState(false);

  return (
    <div className="space-y-5">
      {/* Tiêu đề */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">
            Chi tiết Lead
          </h1>
          <p className="mt-1 text-sm text-muted">
            Thông tin khách hàng tiềm năng
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate("/leads")}
          className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm hover:bg-gray-50"
        >
          <ArrowLeft size={16} />
          Quay lại danh sách
        </button>
      </div>

      {/* Thông tin Lead */}
      <section className="crm-card">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-ink">
            Thông tin Lead
          </h2>
        </div>

        <dl className="grid gap-3 sm:grid-cols-2">
          {fields.map((label) => (
            <div
              key={label}
              className="rounded-lg bg-gray-50 p-3"
            >
              <dt className="text-xs text-muted">
                {label}
              </dt>
              <dd className="mt-1 text-sm text-ink">
                —
              </dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Lịch sử tư vấn */}
      <section className="crm-card">
        <div className="flex items-center gap-2">
          <History size={18} className="text-primary" />
          <h2 className="font-semibold text-ink">
            Lịch sử tư vấn
          </h2>
        </div>

        <div className="mt-4 rounded-lg border border-dashed border-gray-200 p-6 text-center">
          <p className="text-sm text-muted">
            Chưa có lịch sử tư vấn.
          </p>
        </div>
      </section>

      {/* Nút chỉnh sửa */}
      <div className="flex justify-end">
        <Button
          type="button"
          onClick={() => setShowEdit(true)}
        >
          <span className="flex items-center gap-2">
            <Pencil size={16} />
            Chỉnh sửa Lead
          </span>
        </Button>
      </div>

      {/* Modal chỉnh sửa */}
      <Modal
        open={showEdit}
        onClose={() => setShowEdit(false)}
        title="Chỉnh sửa thông tin Lead"
      >
        <LeadForm
          onCancel={() => setShowEdit(false)}
        />
      </Modal>
    </div>
  );
}
