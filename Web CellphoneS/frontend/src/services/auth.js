import { frappeRequest } from "./api";

// Adapter contract: getSession returns null for guests or { user, permissions }.
// Auth can add a server-verified permission mapping and a logout operation.
export const frappeAuth = {
  async getSession(signal) {
    let response;
    try {
      response = await frappeRequest("/api/method/frappe.auth.get_logged_user", {
        signal,
        cache: "no-store",
      });
    } catch (error) {
      if (error.status === 401 || error.status === 403) return null;
      throw error;
    }

    const userId = response.message;
    if (userId === "Guest") return null;
    if (typeof userId !== "string" || !userId.trim()) {
      throw new Error("Phản hồi kiểm tra phiên không hợp lệ.");
    }

    return { user: { id: userId }, permissions: [] };
  },

  async login(username, password) {
    await frappeRequest("/api/method/login", {
      method: "POST",
      body: new URLSearchParams({ usr: username, pwd: password }),
    });
  },
};
