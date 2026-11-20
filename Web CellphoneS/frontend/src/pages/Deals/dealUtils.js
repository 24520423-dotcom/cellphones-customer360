// K02: tên trạng thái phải trùng tuyệt đối với CRM Deal trong API Contract K01.
export const DEAL_STATUSES = [
  "Qualification",
  "Demo/Making",
  "Proposal/Quotation",
  "Negotiation",
  "Ready to Close",
  "Won",
  "Lost",
];

export const STATUS_LABELS = {
  Qualification: "Đánh giá cơ hội",
  "Demo/Making": "Trình diễn / làm mẫu",
  "Proposal/Quotation": "Đề xuất / báo giá",
  Negotiation: "Đàm phán",
  "Ready to Close": "Sẵn sàng chốt",
  Won: "Thành công",
  Lost: "Thất bại",
};

export function statusClass(status) {
  if (status === "Won") return "bg-green-100 text-green-800";
  if (status === "Lost") return "bg-gray-200 text-gray-700";
  return "bg-primary-soft text-primary";
}

export function formatVnd(value) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(number);
}

// Chỉ phục vụ bản demo K02, KHÔNG lấy từ Frappe hoặc đóng vai dữ liệu thật.
export const INITIAL_MOCK_DEALS = [
  {
    name: "DEMO-DEAL-001",
    title: "Tư vấn điện thoại cho khách A",
    status: "Demo/Making",
    lead: "DEMO-LEAD-001",
    deal_value: 0,
    expected_deal_value: 19990000,
    closed_date: "",
    ownerDisplay: "Nhân viên demo A",
    notes: "Dữ liệu tạo mẫu để kiểm thử giao diện.",
  },
  {
    name: "DEMO-DEAL-002",
    title: "Cơ hội bán phụ kiện",
    status: "Lost",
    lead: "",
    deal_value: 0,
    expected_deal_value: 1490000,
    closed_date: "",
    ownerDisplay: "",
    notes: "Ví dụ Deal chưa có Lead liên kết.",
  },
];
