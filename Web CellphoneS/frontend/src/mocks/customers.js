// ===========================================================================
// DỮ LIỆU DEMO – CHỈ DÙNG ĐỂ DỰNG VÀ KIỂM THỬ GIAO DIỆN L01/L02.
// - Không phải dữ liệu khách hàng, đơn hàng hay hạng thành viên của CellphoneS.
// - Tên người là tên giả; số điện thoại dải 0000xxxxxx và email @example.com không tồn tại.
// - Shape bám API Contract v1.0 (§7, §8). Trường đánh dấu [ĐỀ XUẤT] chưa có trong contract.
// - Đơn hàng (orders) là nguồn giao dịch giả lập ĐỘC LẬP với Deal; không suy ra từ Deal Won.
// - Ngày được tính tương đối so với thời điểm mở trang để các insight luôn có thể kiểm thử.
// ===========================================================================

const DAY_MS = 24 * 60 * 60 * 1000;
const at = (daysAgo, hour = 9) => {
  const date = new Date(Date.now() - daysAgo * DAY_MS);
  date.setHours(hour, 0, 0, 0);
  return date.toISOString();
};

const OWNERS = ["sales.demo1@example.com", "sales.demo2@example.com", "cskh.demo1@example.com"];

// Kịch bản có chủ đích để kiểm thử từng insight (xem HUONG_DAN_L01_L02.md, mục kiểm thử).
const scenarios = [
  {
    // I2: Deal mở, tương tác cuối với Deal cách đây 9 ngày
    name: "Nguyễn Minh Anh", owner: 0,
    leads: [["Qualified", "Website", 20]],
    deals: [["Proposal/Quotation", 0, 14990000, 0, 15]],
    timeline: [["call", "Tư vấn cấu hình, khách hẹn xem báo giá", 9, "deal", 0], ["note", "Ghi nhận nhu cầu ban đầu", 18, "lead", 0]],
  },
  {
    // I3: Có yêu cầu bảo hành mở 5 ngày, không có Deal mở
    name: "Trần Thu Hà", owner: 2,
    leads: [["Converted", "Cửa hàng", 60]],
    deals: [["Won", 0, 8990000, 0, 55, 50]],
    orders: [["Điện thoại demo A", 8990000, 48, "Cửa hàng"]],
    requests: [["Warranty", "Kiểm tra lỗi loa ngoài", "Open", 5, null]],
    timeline: [["call", "Tiếp nhận yêu cầu bảo hành qua tổng đài", 5, "request", 0], ["call", "Gọi chăm sóc sau giao hàng", 40, "deal", 0]],
  },
  {
    // I1: Lead Qualified nhưng chưa có Deal
    name: "Lê Quốc Bảo", owner: 1,
    leads: [["Qualified", "Facebook", 6]],
    timeline: [["chat", "Hỏi tình trạng hàng và trả góp", 3, "lead", 0]],
  },
  {
    // I3 mức cao: Deal mở + yêu cầu khiếu nại đang xử lý 6 ngày
    name: "Phạm Ngọc Lan", owner: 0,
    leads: [["Converted", "Ứng dụng", 90]],
    deals: [["Won", 0, 12990000, 0, 85, 80], ["Negotiation", 0, 24990000, 0, 4]],
    orders: [["Laptop demo B", 12990000, 78, "Online"]],
    requests: [["Complaint", "Phản ánh thời gian giao hàng", "In Progress", 6, "cskh.demo1@example.com"]],
    timeline: [["call", "Trao đổi phương án nâng cấp máy", 2, "deal", 1], ["email", "Phản hồi tiến độ xử lý khiếu nại", 3, "request", 0]],
  },
  {
    // I4: Đã mua, 45 ngày chưa tương tác
    name: "Võ Minh Khang", owner: 1,
    leads: [["Converted", "Cửa hàng", 120]],
    deals: [["Won", 0, 1990000, 0, 110, 100]],
    orders: [["Tai nghe demo C", 1990000, 98, "Cửa hàng"], ["Sạc dự phòng demo D", 690000, 60, "Online"]],
    timeline: [["call", "Gọi khảo sát mức độ hài lòng", 45, "deal", 0]],
  },
  {
    // Không có cảnh báo: Lead mới, tương tác hôm qua
    name: "Đặng Thảo Nhi", owner: 0,
    leads: [["New", "Website", 2]],
    timeline: [["call", "Gọi lại theo form đăng ký tư vấn", 1, "lead", 0]],
  },
  {
    // Deal Lost – không phải Deal mở
    name: "Bùi Hoàng Phúc", owner: 1,
    leads: [["Unqualified", "Hotline", 40]],
    deals: [["Lost", 0, 9990000, 0, 35, 20]],
    timeline: [["note", "Khách chọn mua nơi khác", 20, "deal", 0]],
  },
  {
    // I5: Không có SĐT, Deal không liên kết Lead (giống CRM-DEAL-2026-00002 trong contract)
    name: "Mai Khánh Linh", owner: 2, noPhone: true, noEmail: true,
    deals: [["Qualification", null, 4990000, 0, 3]],
    timeline: [["meeting", "Khách ghé cửa hàng xem sản phẩm", 3, "deal", 0]],
  },
  {
    // Không có cảnh báo: Deal sắp chốt, tương tác 2 ngày trước
    name: "Hoàng Minh Trí", owner: 0,
    leads: [["Converted", "Website", 14]],
    deals: [["Ready to Close", 0, 15990000, 0, 10]],
    timeline: [["call", "Xác nhận phương thức thanh toán", 2, "deal", 0]],
  },
  {
    // I4: Chưa có tương tác nào
    name: "Nguyễn Bảo Ngọc", owner: 1,
    leads: [["Contacted", "Facebook", 12]],
    timeline: [],
  },
  {
    // Yêu cầu đã giải quyết – không cảnh báo
    name: "Phan Đức Huy", owner: 2,
    leads: [["Converted", "Hotline", 70]],
    deals: [["Won", 0, 9990000, 0, 65, 60]],
    orders: [["Máy tính bảng demo E", 9990000, 58, "Online"]],
    requests: [["Return", "Hỏi điều kiện đổi trả", "Resolved", 20, "cskh.demo1@example.com"]],
    timeline: [["call", "Hướng dẫn điều kiện đổi trả", 19, "request", 0], ["call", "Gọi chăm sóc định kỳ", 12, "deal", 0]],
  },
  {
    name: "Đỗ Tuyết Mai", owner: 0,
    leads: [["Nurture", "Ứng dụng", 25]],
    timeline: [["email", "Gửi thông tin chương trình khuyến mãi demo", 8, "lead", 0]],
  },
];

// Hồ sơ đơn giản để có đủ dữ liệu kiểm thử phân trang (25 hồ sơ).
const fillerNames = [
  "Trịnh Gia Hân", "Lý Thành Đạt", "Châu Mỹ Duyên", "Tạ Quang Vinh", "Kiều Ngọc Hân",
  "Dương Khôi Nguyên", "Tô Bảo Châu", "Lâm Nhật Quang", "Hồ Thanh Tâm", "Vũ Hải Yến",
  "Cao Minh Hiếu", "La Thùy Dung", "Quách Tuấn Kiệt",
];
fillerNames.forEach((name, i) => {
  scenarios.push({
    name, owner: i % 3,
    leads: [[i % 2 ? "Contacted" : "New", ["Website", "Cửa hàng", "Facebook", "Hotline"][i % 4], 3 + i]],
    timeline: [["call", "Liên hệ tư vấn ban đầu", 1 + (i % 6), "lead", 0]],
  });
});

function build(scenario, index) {
  const no = String(index + 1).padStart(3, "0");
  const customer_id = `C360-DEMO-${no}`;
  const leads = (scenario.leads || []).map(([status, source, createdDaysAgo], j) => ({
    name: `DEMO-LEAD-${no}-${j + 1}`,
    lead_name: scenario.name,
    status,
    source,
    lead_owner: OWNERS[scenario.owner],
    creation: at(createdDaysAgo),
  }));
  const deals = (scenario.deals || []).map(([status, leadIndex, expected, value, createdDaysAgo, closedDaysAgo], j) => ({
    name: `DEMO-DEAL-${no}-${j + 1}`,
    status,
    lead: leadIndex === null ? null : leads[leadIndex]?.name ?? null,
    expected_deal_value: expected,
    deal_value: value, // giữ 0 như snapshot contract; không dùng làm doanh thu
    closed_date: closedDaysAgo ? at(closedDaysAgo).slice(0, 10) : null,
    creation: at(createdDaysAgo),
  }));
  const after_sales_requests = (scenario.requests || []).map(([category, subject, status, createdDaysAgo, assigned], j) => ({
    request_id: `AS-DEMO-${no}-${j + 1}`,
    customer_id,
    category,
    subject,
    status,
    assigned_to: assigned,
    created_at: at(createdDaysAgo, 10),
  }));
  const orders = (scenario.orders || []).map(([product, total, daysAgo, channel], j) => ({
    order_id: `ORD-DEMO-${no}-${j + 1}`,
    product,
    total,
    status: "Hoàn tất (demo)",
    purchased_at: at(daysAgo, 15),
    channel,
  }));
  const related = { lead: leads, deal: deals, request: after_sales_requests };
  const doctype = { lead: "CRM Lead", deal: "CRM Deal", request: "C360 After Sales Request" };
  const timeline = (scenario.timeline || []).map(([type, summary, daysAgo, kind, refIndex], j) => ({
    id: `TL-DEMO-${no}-${j + 1}`,
    type,
    summary,
    occurred_at: at(daysAgo, 9 + j),
    related_doctype: doctype[kind],
    related_name: related[kind][refIndex]?.name ?? related[kind][refIndex]?.request_id ?? null,
  })).sort((a, b) => b.occurred_at.localeCompare(a.occurred_at));

  const phone = scenario.noPhone ? null : `0000${String(100000 + index * 37).slice(-6)}`;
  const email = scenario.noEmail ? null : `demo.customer${no}@example.com`;
  const modified = [...leads.map((l) => l.creation), ...deals.map((d) => d.creation),
    ...after_sales_requests.map((r) => r.created_at), ...timeline.map((t) => t.occurred_at)].sort().pop() ?? null;

  return {
    customer_id,
    display_name: scenario.name,
    phone,
    email,
    segments: [], // Contract §9: phân khúc "not_configured" – chưa có quy tắc
    owner: OWNERS[scenario.owner], // [ĐỀ XUẤT]
    updated_at: modified, // [ĐỀ XUẤT] mốc thay đổi mới nhất của bản ghi liên kết
    leads,
    deals,
    interactions: [], // Lịch sử tương tác lấy từ timeline (nguồn chính)
    after_sales_requests,
    orders, // [ĐỀ XUẤT – BLOCKED D07] nguồn giao dịch giả lập
    timeline, // chỉ dùng trong adapter demo cho get_customer_timeline
  };
}

export const DEMO_CUSTOMERS = scenarios.map(build);
