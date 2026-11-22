import { frappeRequest } from "./api";

export async function getAnalyticsOverview(period, { signal, activities = false } = {}) {
  const query = new URLSearchParams({ period, activities: activities ? "1" : "0" });
  const { message } = await frappeRequest(`/api/method/cellphones_c360.api.analytics.get_analytics_overview?${query}`, { signal });
  if (!message || typeof message !== "object") throw new Error("Frappe chưa trả kết quả phân tích.");
  return message;
}
