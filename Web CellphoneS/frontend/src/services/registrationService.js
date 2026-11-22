import { frappeRequest, publicFrappeRequest } from "./api";

const endpoint = "/api/method/cellphones_c360.api.registration.";

export async function submitRegistration(form) {
  const { message } = await publicFrappeRequest(endpoint + "submit", form);
  if (!message?.accepted) throw new Error("Frappe chưa xác nhận yêu cầu.");
}

export async function listRegistrationRequests(status, page, signal) {
  const { message } = await frappeRequest(endpoint + "list_requests?" + new URLSearchParams({ status, page }), { signal, cache: "no-store" });
  return message;
}

async function action(method, payload) {
  const { message } = await frappeRequest(endpoint + method, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return message;
}

export const reviewRegistration = (payload) => action("review", payload);
export const retryRegistrationInvitation = (name) => action("retry_invitation", { name });
