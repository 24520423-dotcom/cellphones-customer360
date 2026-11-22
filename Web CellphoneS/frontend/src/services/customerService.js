import { frappeRequest } from "./api";
import { DEMO_CUSTOMERS } from "../mocks/customers";
import { isOpenDeal, isOpenRequest, maskEmail, maskPhone } from "../utils/customer360";

// Các trang xem trước truyền adapter demo. Tuyến nghiệp vụ mặc định gọi Frappe.
export const customerDataMode =
  import.meta.env.DEV && import.meta.env.VITE_CUSTOMER360_MODE === "demo" ? "demo" : "api";

// Contract v1.0 list_customers chỉ có search/page/page_size.
// Lọc và sắp xếp là ĐỀ XUẤT bổ sung: chỉ bật ở demo; ở API mode bị khóa cho tới khi L03 hỗ trợ,
// tránh lọc sai trên một trang dữ liệu.
export const listCapabilities = {
  filters: customerDataMode === "demo",
  sort: customerDataMode === "demo",
};

export const SORT_OPTIONS = [
  { value: "updated_desc", label: "Cập nhật gần nhất" },
  { value: "name_asc", label: "Tên A–Z" },
  { value: "interaction_asc", label: "Lâu chưa tương tác nhất" },
];

const METHOD = "/api/method/cellphones_c360.api.customer360.";
const MAX_PAGE_SIZE = 100;

export class CustomerApiError extends Error {
  constructor(kind, message, status) {
    super(message);
    this.name = "CustomerApiError";
    this.kind = kind; // auth | forbidden | not_found | network | server | contract
    this.status = status;
  }
}

function toApiError(error) {
  if (error instanceof CustomerApiError || error?.name === "AbortError") return error;
  const status = error?.status;
  if (status === 401) return new CustomerApiError("auth", "Phiên đăng nhập đã hết hạn.", status);
  if (status === 403) return new CustomerApiError("forbidden", "Bạn không có quyền xem dữ liệu này hoặc phiên đã hết hạn.", status);
  if (status === 404) return new CustomerApiError("not_found", "Không tìm thấy dữ liệu.", status);
  if (status >= 500) return new CustomerApiError("server", "Máy chủ gặp lỗi khi xử lý yêu cầu.", status);
  if (!status) return new CustomerApiError("network", "Không kết nối được tới máy chủ.");
  return new CustomerApiError("server", `Yêu cầu thất bại (HTTP ${status}).`, status);
}

function abortError() {
  return new DOMException("Đã hủy yêu cầu.", "AbortError");
}

async function demoDelay(signal, ms = 200) {
  await new Promise((resolve) => setTimeout(resolve, ms));
  if (signal?.aborted) throw abortError();
}

async function callMethod(name, query, signal) {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") params.set(key, String(value));
  });
  let result;
  try {
    result = await frappeRequest(`${METHOD}${name}?${params}`, { method: "GET", signal });
  } catch (error) {
    throw toApiError(error);
  }
  // Custom method trả { message: ... } (contract §2.1).
  if (!result || typeof result !== "object" || !("message" in result)) {
    throw new CustomerApiError("contract", `API ${name} trả dữ liệu không đúng hợp đồng.`);
  }
  return result.message;
}

const toCount = (value) => (value === null || value === undefined ? null : Number(value) || 0);
const clampPageSize = (size) => Math.min(Math.max(Number(size) || 20, 1), MAX_PAGE_SIZE);

// Chuẩn hóa 1 dòng list_customers. Trường không có trong contract giữ null (KHÔNG tự điền 0/"")
// để giao diện biết là "chưa có dữ liệu" thay vì "bằng 0".
function normalizeListItem(item = {}) {
  return {
    customer_id: String(item.customer_id ?? ""),
    display_name: item.display_name || "Chưa có tên",
    phone_masked: item.phone_masked || null,
    lead_count: toCount(item.lead_count),
    deal_count: toCount(item.deal_count),
    // Các trường dưới đây là ĐỀ XUẤT bổ sung contract:
    email_masked: item.email_masked ?? null,
    segments: Array.isArray(item.segments) ? item.segments : null,
    updated_at: item.updated_at ?? null,
    owner: item.owner ?? null,
    open_deal_count: toCount(item.open_deal_count),
    open_request_count: toCount(item.open_request_count),
    last_interaction_at: item.last_interaction_at ?? null,
  };
}

function normalizeProfile(profile = {}) {
  const list = (value) => (Array.isArray(value) ? value : []);
  return {
    customer_id: String(profile.customer_id ?? ""),
    display_name: profile.display_name || "Chưa có tên",
    phone: profile.phone ?? null,
    email: profile.email ?? null,
    segments: list(profile.segments),
    owner: profile.owner ?? null, // ĐỀ XUẤT
    updated_at: profile.updated_at ?? null, // ĐỀ XUẤT
    leads: list(profile.leads),
    deals: list(profile.deals),
    after_sales_requests: list(profile.after_sales_requests),
    // null = chưa có nguồn giao dịch (contract chưa có orders, chờ D07); [] = có nguồn nhưng chưa mua.
    orders: Array.isArray(profile.orders) ? profile.orders : null,
  };
}

// ----------------------------- Adapter demo -----------------------------
function demoListItem(customer) {
  return {
    customer_id: customer.customer_id,
    display_name: customer.display_name,
    phone_masked: maskPhone(customer.phone),
    lead_count: customer.leads.length,
    deal_count: customer.deals.length,
    email_masked: maskEmail(customer.email),
    segments: customer.segments,
    updated_at: customer.updated_at,
    owner: customer.owner,
    open_deal_count: customer.deals.filter(isOpenDeal).length,
    open_request_count: customer.after_sales_requests.filter(isOpenRequest).length,
    last_interaction_at: customer.timeline[0]?.occurred_at ?? null,
  };
}

function demoSearch(customer, query) {
  if (!query) return true;
  const text = query.toLocaleLowerCase("vi-VN");
  const digits = query.replace(/\D/g, "");
  return customer.display_name.toLocaleLowerCase("vi-VN").includes(text)
    || customer.customer_id.toLocaleLowerCase("vi-VN").includes(text)
    || (digits.length >= 3 && String(customer.phone || "").includes(digits));
}

const sorters = {
  updated_desc: (a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")),
  name_asc: (a, b) => a.display_name.localeCompare(b.display_name, "vi"),
  // Chưa có tương tác xếp đầu, sau đó lâu nhất trước.
  interaction_asc: (a, b) => String(a.last_interaction_at || "").localeCompare(String(b.last_interaction_at || "")),
};

// ------------------------------ API công khai ------------------------------
export async function listCustomers(
  { search = "", page = 1, page_size = 20, has_open_deal = false, has_open_request = false, order_by = "updated_desc", signal, demo = customerDataMode === "demo" } = {},
) {
  const size = clampPageSize(page_size);
  const query = search.trim();

  if (demo) {
    await demoDelay(signal);
    const rows = DEMO_CUSTOMERS.filter((c) => demoSearch(c, query))
      .map(demoListItem)
      .filter((c) => !has_open_deal || c.open_deal_count > 0)
      .filter((c) => !has_open_request || c.open_request_count > 0)
      .sort(sorters[order_by] || sorters.updated_desc);
    return {
      items: rows.slice((page - 1) * size, page * size).map(normalizeListItem),
      page, page_size: size, total: rows.length,
    };
  }

  // API mode: chỉ gửi tham số có trong contract.
  const result = await callMethod("list_customers", { search: query, page, page_size: size }, signal);
  if (!result || !Array.isArray(result.items)) {
    throw new CustomerApiError("contract", "API list_customers trả sai cấu trúc items.");
  }
  return {
    items: result.items.map(normalizeListItem),
    page: Number(result.page ?? page),
    page_size: Number(result.page_size ?? size),
    total: Number(result.total ?? result.items.length),
  };
}

export async function getCustomerProfile(customerId, { signal, demo = customerDataMode === "demo" } = {}) {
  if (!customerId) throw new CustomerApiError("not_found", "Thiếu mã khách hàng.");

  if (demo) {
    await demoDelay(signal);
    const found = DEMO_CUSTOMERS.find((c) => c.customer_id === customerId);
    if (!found) throw new CustomerApiError("not_found", "Không tìm thấy hồ sơ demo.", 404);
    return normalizeProfile(found);
  }

  const result = await callMethod("get_customer_profile", { customer_id: customerId }, signal);
  // Chống hiển thị nhầm hồ sơ của khách khác (contract §7, §11).
  if (!result || String(result.customer_id) !== customerId) {
    throw new CustomerApiError("contract", "Hồ sơ trả về không khớp mã khách hàng.");
  }
  return normalizeProfile(result);
}

export async function getCustomerTimeline(customerId, { page = 1, page_size = 20, signal, demo = customerDataMode === "demo" } = {}) {
  if (!customerId) throw new CustomerApiError("not_found", "Thiếu mã khách hàng.");
  const size = clampPageSize(page_size);

  if (demo) {
    await demoDelay(signal, 150);
    const items = DEMO_CUSTOMERS.find((c) => c.customer_id === customerId)?.timeline || [];
    return { items: items.slice((page - 1) * size, page * size), page, page_size: size, total: items.length };
  }

  const result = await callMethod("get_customer_timeline", { customer_id: customerId, page, page_size: size }, signal);
  if (!result || !Array.isArray(result.items)) {
    throw new CustomerApiError("contract", "API get_customer_timeline trả sai định dạng.");
  }
  // Contract chưa quy định thứ tự; sắp xếp mới nhất trước ở phía client cho trang đã nhận.
  const items = [...result.items].sort((a, b) => String(b.occurred_at || "").localeCompare(String(a.occurred_at || "")));
  return { items, page: Number(result.page ?? page), page_size: Number(result.page_size ?? size), total: Number(result.total ?? items.length) };
}


const customerEndpoint = "/api/resource/C360%20Customer";

export async function getCustomerAccess(id, { signal } = {}) {
  const query = id ? `?${new URLSearchParams({ customer: id })}` : "";
  const { message } = await frappeRequest(`/api/method/cellphones_c360.api.customers.get_access${query}`, { signal });
  return message;
}

export async function getCustomerRecord(id, { signal } = {}) {
  const { data } = await frappeRequest(`${customerEndpoint}/${encodeURIComponent(id)}`, { signal });
  return data;
}

export async function saveCustomerRecord(id, payload) {
  const endpoint = id ? `${customerEndpoint}/${encodeURIComponent(id)}` : customerEndpoint;
  const { data } = await frappeRequest(endpoint, {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return data;
}
