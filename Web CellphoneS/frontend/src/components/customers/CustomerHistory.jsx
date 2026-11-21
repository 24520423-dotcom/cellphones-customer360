import { DataTable, EmptyState, Panel } from "./CustomerStates";
import { formatVnd } from "../../pages/Deals/dealUtils";
import { displayDate, displayOrDash } from "../../utils/customer360";

// L02 – Lịch sử mua hàng / giao dịch.
// API Contract v1.0 CHƯA có nguồn đơn hàng (quyết định D07). orders = null nghĩa là chưa tích hợp.
// Tuyệt đối không suy ra đơn hàng hoặc doanh thu từ Deal Won.

const columns = [
  { key: "order_id", label: "Mã giao dịch", render: (value) => <span className="font-mono text-xs">{value}</span> },
  { key: "product", label: "Sản phẩm" },
  { key: "purchased_at", label: "Ngày", render: (value) => displayDate(value) },
  { key: "channel", label: "Kênh", render: (value) => displayOrDash(value) },
  { key: "total", label: "Giá trị", render: (value) => <span className="whitespace-nowrap">{formatVnd(value)}</span> },
  { key: "status", label: "Trạng thái", render: (value) => displayOrDash(value) },
];

const NOT_INTEGRATED = "API Contract chưa có dữ liệu giao dịch (chờ quyết định D07). Hệ thống không suy ra mua hàng từ Deal Won.";

export default function CustomerHistory({ orders, isDemo }) {
  const sorted = orders ? [...orders].sort((a, b) => String(b.purchased_at || "").localeCompare(String(a.purchased_at || ""))) : [];
  return (
    <Panel id="orders-title" title="Lịch sử mua hàng" count={orders ? orders.length : null}>
      {orders === null ? (
        <EmptyState title="Chưa tích hợp nguồn giao dịch" description={NOT_INTEGRATED} />
      ) : orders.length === 0 ? (
        <EmptyState title="Chưa có giao dịch được ghi nhận" />
      ) : (
        <DataTable caption="Lịch sử giao dịch của khách hàng" columns={columns} rows={sorted} getKey={(o) => o.order_id} />
      )}
      {isDemo && orders?.length > 0 && (
        <p className="border-t border-border px-5 py-2 text-xs text-muted">
          Giao dịch giả lập để thử giao diện, tách riêng khỏi Deal; không phải đơn hàng thật.
        </p>
      )}
    </Panel>
  );
}

export function PurchaseSummary({ orders, onShowAll }) {
  const last = orders?.length
    ? [...orders].sort((a, b) => String(b.purchased_at || "").localeCompare(String(a.purchased_at || "")))[0]
    : null;
  return (
    <Panel id="purchase-summary-title" title="Mua hàng"
      action={<button type="button" onClick={onShowAll} className="text-xs font-medium text-primary hover:underline">Xem chi tiết</button>}>
      <p className="px-5 py-4 text-sm text-muted">
        {orders === null ? "Chưa tích hợp nguồn giao dịch."
          : !orders.length ? "Chưa có giao dịch được ghi nhận."
          : <>{orders.length} giao dịch · gần nhất {displayDate(last.purchased_at)}</>}
      </p>
    </Panel>
  );
}
