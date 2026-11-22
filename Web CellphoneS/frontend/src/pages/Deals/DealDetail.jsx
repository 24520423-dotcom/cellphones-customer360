import { CalendarDays, Link2, Pencil, UserRound, Wallet } from "lucide-react";
import Button from "../../components/Button";
import { formatVnd, STATUS_LABELS } from "./dealUtils";

export default function DealDetail({ deal, onEdit }) {
  if (!deal) return <p className="deal-detail-empty">Không tìm thấy Deal.</p>;

  return (
    <div className="deal-detail">
      <div className="deal-detail-head">
        <div>
          <div className="deal-detail-overline">{deal.name}</div>
          <h3>{deal.title || "Cơ hội bán hàng"}</h3>
          <span className="deal-stage" data-status={deal.status}><span className="deal-stage-dot" />{STATUS_LABELS[deal.status] || deal.status}</span>
        </div>
        {onEdit && <Button size="sm" onClick={onEdit}><Pencil size={15} /> Chỉnh sửa</Button>}
      </div>

      <div className="deal-detail-finance">
        <div><span>Giá trị dự kiến</span><strong>{formatVnd(deal.expected_deal_value, deal.currency)}</strong></div>
        <div><span>Giá trị Deal</span><strong>{formatVnd(deal.deal_value, deal.currency)}</strong></div>
      </div>

      <div className="deal-detail-grid">
        <div className="deal-detail-field"><UserRound size={17} /><span><small>Lead liên quan</small><strong>{deal.lead || "Chưa liên kết"}</strong></span></div>
        <div className="deal-detail-field"><UserRound size={17} /><span><small>Nhân viên phụ trách</small><strong>{deal.ownerDisplay || "Chưa xác định"}</strong></span></div>
        <div className="deal-detail-field"><CalendarDays size={17} /><span><small>Ngày đóng</small><strong>{deal.closed_date || "Chưa xác định"}</strong></span></div>
        <div className="deal-detail-field"><Wallet size={17} /><span><small>Giai đoạn (mã Frappe)</small><strong>{deal.status}</strong></span></div>
      </div>

      <section className="deal-detail-panel">
        <h4><Link2 size={17} /> Liên kết dữ liệu</h4>
        <p>{deal.lead
          ? `Deal đang liên kết với Lead ${deal.lead}.`
          : "Deal chưa có Lead liên kết."}</p>
      </section>
      <section className="deal-detail-panel">
        <h4>Bước tiếp theo</h4>
        <p className="deal-detail-notes">{deal.notes || "Chưa có ghi chú."}</p>
      </section>
    </div>
  );
}
