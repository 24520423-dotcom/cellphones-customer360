const apiOrigin = (import.meta.env.VITE_FRAPPE_API_ORIGIN ?? "").replace(/\/$/, "");

export async function frappeRequest(path, options) {
  const response = await fetch(`${apiOrigin}${path}`, {
    ...options,
    credentials: "include",
    headers: { Accept: "application/json", ...options?.headers },
  });

  if (!response.ok) {
    throw Object.assign(new Error("Yêu cầu tới Frappe không thành công."), {
      status: response.status,
    });
  }

  return response.json();
}
