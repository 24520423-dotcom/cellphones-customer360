import { BriefcaseBusiness, ChevronRight } from "lucide-react";
import { STATUS_LABELS, formatVnd } from "./dealUtils";

export default function DealBoard({ deals = [], statuses, disabled, onOpenDetail, onChangeStatus }) {
  return (
    <div className="deals-board-scroll" role="region" aria-label="Bảng tiến trình Deal" tabIndex={0}>
      <div className="deals-board">
        {statuses.map((status) => {
          const items = deals.filter((deal) => deal.status === status);
          const expectedTotal = items.every((deal) => deal.expected_deal_value != null && (!deal.currency || deal.currency === "VND")) ? items.reduce((sum, deal) => sum + Number(deal.expected_deal_value), 0) : null;
          return (
            <section key={status} className="deals-board-column" data-status={status}>
              <div className="deals-board-column-top" />
              <header className="deals-board-column-heading">
                <div className="deals-board-heading-line">
                  <h3>{STATUS_LABELS[status] || status}</h3>
                  <span className="deals-board-number">{items.length}</span>
                </div>
                <span className="deals-board-total">{formatVnd(expectedTotal)} dự kiến</span>
              </header>
              <div className="deals-board-items">
                {items.length === 0 ? (
                  <div className="deals-board-empty">Chưa có cơ hội ở giai đoạn này</div>
                ) : items.map((deal) => (
                  <article key={deal.name} className="deals-board-card">
                    <button type="button" className="deals-board-open" onClick={() => onOpenDetail?.(deal)} aria-label={`Xem Deal ${deal.name}`}>
                      <span className="deals-board-card-icon"><BriefcaseBusiness size={16} /></span>
                      <span className="deals-board-open-text">
                        <strong>{deal.title || deal.name}</strong>
                        <small>{deal.name}</small>
                      </span>
                      <ChevronRight size={17} className="deals-board-chevron" aria-hidden="true" />
                    </button>
                    <div className="deals-board-card-meta">
                      <span>Lead</span>
                      <strong>{deal.lead || "Chưa liên kết"}</strong>
                    </div>
                    <div className="deals-board-card-amount">{formatVnd(deal.expected_deal_value, deal.currency)}</div>
                    <label className="deals-board-card-change">
                      <span>Chuyển giai đoạn</span>
                      <select
                        aria-label={`Chuyển giai đoạn Deal ${deal.name}`}
                        value={deal.status}
                        disabled={disabled}
                        onChange={(event) => onChangeStatus?.(deal.name, event.target.value)}
                      >
                        {statuses.map((target) => <option key={target} value={target}>{STATUS_LABELS[target] || target}</option>)}
                      </select>
                    </label>
                  </article>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
