// L01/L02 – Customer 360: hàm hiển thị và quy tắc insight dùng chung trong module Khách hàng.
// Không chứa dữ liệu. Không gọi API.

// ---------------------------------------------------------------------------
// Ngưỡng insight: GIẢ ĐỊNH CỦA NHÓM phục vụ đồ án, không phải quy định của CellphoneS.
// Đổi tại đây khi nhóm thống nhất lại.
// ---------------------------------------------------------------------------
export const INSIGHT_RULES = {
  DEAL_IDLE_DAYS: 7, // Deal đang mở quá số ngày này không có tương tác liên kết
  REQUEST_SLA_DAYS: 3, // Yêu cầu sau bán mở quá số ngày này được coi là quá hạn
  INACTIVE_DAYS: 30, // Khách không có tương tác quá số ngày này
};

// Giá trị trạng thái đúng theo API Contract v1.0 (§4, §5, §8).
export const CLOSED_DEAL_STATUSES = ["Won", "Lost"];
export const OPEN_REQUEST_STATUSES = ["Open", "In Progress"];

export const LEAD_STATUS_LABELS = {
  New: "Mới",
  Contacted: "Đã liên hệ",
  Nurture: "Nuôi dưỡng",
  Qualified: "Đủ điều kiện",
  Converted: "Đã chuyển đổi",
  Unqualified: "Không đủ điều kiện",
  Junk: "Rác",
};

export const REQUEST_STATUS_LABELS = {
  Open: "Mới tiếp nhận",
  "In Progress": "Đang xử lý",
  Resolved: "Đã giải quyết",
  Closed: "Đã đóng",
};

// Contract mới có ví dụ "Warranty"; các loại còn lại là đề xuất của nhóm (chờ chốt D06).
export const REQUEST_CATEGORY_LABELS = {
  Warranty: "Bảo hành",
  Return: "Đổi trả",
  Complaint: "Khiếu nại",
  Support: "Hỗ trợ kỹ thuật",
};

export const INTERACTION_TYPE_LABELS = {
  call: "Cuộc gọi",
  email: "Email",
  note: "Ghi chú",
  chat: "Tin nhắn",
  meeting: "Gặp trực tiếp",
  task: "Công việc",
};

const DAY_MS = 24 * 60 * 60 * 1000;

export const isOpenDeal = (deal) => Boolean(deal?.status) && !CLOSED_DEAL_STATUSES.includes(deal.status);
export const isOpenRequest = (request) => OPEN_REQUEST_STATUSES.includes(request?.status);

export function toDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function displayDate(value) {
  const date = toDate(value);
  if (!date) return "—";
  return date.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function displayDateTime(value) {
  const date = toDate(value);
  if (!date) return "—";
  return date.toLocaleString("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

export function daysSince(value, now = new Date()) {
  const date = toDate(value);
  if (!date) return null;
  return Math.max(0, Math.floor((now.getTime() - date.getTime()) / DAY_MS));
}

export function relativeDays(value, now = new Date()) {
  const days = daysSince(value, now);
  if (days === null) return "—";
  if (days === 0) return "Hôm nay";
  if (days === 1) return "Hôm qua";
  return `${days} ngày trước`;
}

export const displayOrDash = (value) =>
  value === null || value === undefined || value === "" ? "—" : String(value);

export function initials(name) {
  const parts = String(name || "KH").trim().split(/\s+/);
  return parts.slice(-2).map((part) => part[0]).join("").toUpperCase();
}

// Che dữ liệu cá nhân mặc định. Xem đầy đủ là TO-BE và phải do server cấp quyền.
export function maskPhone(phone) {
  const digits = String(phone || "").replace(/\D/g, "");
  if (!digits) return null;
  return `${"*".repeat(Math.max(digits.length - 3, 4))}${digits.slice(-3)}`;
}

export function maskEmail(email) {
  const value = String(email || "");
  const at = value.indexOf("@");
  if (at < 1) return null;
  return `${value[0]}***${value.slice(at)}`;
}

export function customerBasePath(pathname) {
  return pathname.startsWith("/preview/customers") ? "/preview/customers" : "/customers";
}

// ---------------------------------------------------------------------------
// Insight L02. Mỗi insight ghi rõ điều kiện tính và nguồn dữ liệu để hiển thị cho người dùng.
// Chỉ tính khi đủ dữ liệu; thiếu dữ liệu thì KHÔNG đưa ra kết luận.
// timeline: { items, total, complete } – complete=true khi đã tải hết các trang.
// ---------------------------------------------------------------------------
export function computeAlerts(profile, timeline, now = new Date()) {
  if (!profile) return [];
  const alerts = [];
  const { DEAL_IDLE_DAYS, REQUEST_SLA_DAYS, INACTIVE_DAYS } = INSIGHT_RULES;
  const openDeals = profile.deals.filter(isOpenDeal);
  const openRequests = profile.after_sales_requests.filter(isOpenRequest);

  // I3 – Yêu cầu sau bán chưa xử lý (ưu tiên giải quyết trước khi chào bán).
  openRequests.forEach((request) => {
    const age = daysSince(request.created_at, now);
    const overdue = age !== null && age > REQUEST_SLA_DAYS;
    alerts.push({
      id: `request-${request.request_id}`,
      level: overdue || openDeals.length ? "high" : "medium",
      title: `${REQUEST_CATEGORY_LABELS[request.category] || "Yêu cầu"} ${request.request_id} ${overdue ? `đã mở ${age} ngày` : "chưa xử lý xong"}`,
      detail: openDeals.length
        ? "Khách đang có Deal mở. Nên xử lý yêu cầu hỗ trợ trước khi tiếp tục chào bán."
        : "Theo dõi để phản hồi khách đúng hạn.",
      rule: `Trạng thái ∈ {Open, In Progress}; quá hạn khi mở > ${REQUEST_SLA_DAYS} ngày (ngưỡng giả định của nhóm).`,
      source: "after_sales_requests (PROPOSED – chờ chốt DocType D06)",
    });
  });

  // I2 – Deal đang mở chưa được theo dõi. Chỉ kết luận khi tìm thấy tương tác hoặc đã tải đủ timeline.
  if (timeline) {
    openDeals.forEach((deal) => {
      const related = timeline.items.filter(
        (item) => item.related_doctype === "CRM Deal" && item.related_name === deal.name,
      );
      const last = related.map((item) => toDate(item.occurred_at)).filter(Boolean)
        .sort((a, b) => b - a)[0];
      if (!last && !timeline.complete) return; // chưa đủ dữ liệu → không kết luận
      const idle = last ? daysSince(last, now) : null;
      if (last && idle <= DEAL_IDLE_DAYS) return;
      alerts.push({
        id: `deal-idle-${deal.name}`,
        level: "high",
        title: last
          ? `Deal ${deal.name} chưa có tương tác ${idle} ngày`
          : `Deal ${deal.name} chưa có tương tác nào được ghi nhận`,
        detail: "Liên hệ lại khách hoặc cập nhật trạng thái Deal.",
        rule: `Deal chưa Won/Lost và tương tác cuối có related_name = mã Deal cách đây > ${DEAL_IDLE_DAYS} ngày (ngưỡng giả định).`,
        source: "CRM Deal (status) + get_customer_timeline (PROPOSED)",
      });
    });
  }

  // I1 – Lead đủ điều kiện nhưng chưa có Deal.
  profile.leads
    .filter((lead) => lead.status === "Qualified")
    .filter((lead) => !profile.deals.some((deal) => deal.lead === lead.name))
    .forEach((lead) => {
      alerts.push({
        id: `lead-no-deal-${lead.name}`,
        level: "medium",
        title: `Lead ${lead.name} đủ điều kiện nhưng chưa có Deal`,
        detail: "Cân nhắc tạo Deal để theo dõi cơ hội bán.",
        rule: "Lead.status = Qualified và không có Deal nào có trường lead = mã Lead.",
        source: "CRM Lead (status), CRM Deal (lead)",
      });
    });

  // I4 – Lâu chưa tương tác (chỉ kết luận khi timeline tải thành công).
  if (timeline) {
    const last = timeline.items.map((item) => toDate(item.occurred_at)).filter(Boolean)
      .sort((a, b) => b - a)[0];
    const idle = last ? daysSince(last, now) : null;
    if ((!last && timeline.complete) || (idle !== null && idle > INACTIVE_DAYS)) {
      alerts.push({
        id: "inactive",
        level: "medium",
        title: last ? `Chưa tương tác ${idle} ngày` : "Chưa có tương tác nào được ghi nhận",
        detail: "Khách có thể cần được chăm sóc lại.",
        rule: `Tương tác gần nhất cách đây > ${INACTIVE_DAYS} ngày (ngưỡng giả định).`,
        source: "get_customer_timeline (PROPOSED)",
      });
    }
  }

  // I5 – Chất lượng hồ sơ.
  const qualityIssues = [];
  if (!profile.phone && !profile.email) qualityIssues.push("thiếu cả số điện thoại và email");
  const orphanDeals = profile.deals.filter((deal) => !deal.lead).map((deal) => deal.name);
  if (orphanDeals.length) qualityIssues.push(`Deal không liên kết Lead: ${orphanDeals.join(", ")}`);
  if (qualityIssues.length) {
    alerts.push({
      id: "data-quality",
      level: "low",
      title: "Hồ sơ cần bổ sung dữ liệu",
      detail: `Hồ sơ ${qualityIssues.join("; ")}.`,
      rule: "Thiếu phone và email; hoặc CRM Deal có lead = null.",
      source: "get_customer_profile (PROPOSED), CRM Deal (lead)",
    });
  }

  const order = { high: 0, medium: 1, low: 2 };
  return alerts.sort((a, b) => order[a.level] - order[b.level]);
}
