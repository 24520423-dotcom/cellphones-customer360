const apiOrigin = (
  import.meta.env.VITE_FRAPPE_API_ORIGIN ?? ""
).replace(/\/$/, "");

const CSRF_ENDPOINT =
  "/api/method/cellphones_c360.api.customer360.get_session_csrf_token";

let csrfTokenRequest = null;

async function fetchCsrfToken() {
  const response = await fetch(`${apiOrigin}${CSRF_ENDPOINT}`, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error("Không thể lấy CSRF Token từ Frappe.");
  }

  const data = await response.json();
  if (!data.message) {
    throw new Error("Frappe không trả về CSRF Token.");
  }
  return data.message;
}

function getCsrfToken() {
  if (!csrfTokenRequest) {
    const pending = fetchCsrfToken();
    csrfTokenRequest = pending;
    pending.catch(() => {
      if (csrfTokenRequest === pending) csrfTokenRequest = null;
    });
  }
  return csrfTokenRequest;
}

export async function frappeRequest(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();

  const headers = {
    Accept: "application/json",
    ...options.headers,
  };

  // Frappe starts the application session at login. Subsequent writes use its CSRF token.
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && path !== "/api/method/login") {
    headers["X-Frappe-CSRF-Token"] = await getCsrfToken();
  }

  return request(path, { ...options, method, credentials: "include", headers });
}

async function request(path, options) {
  const response = await fetch(`${apiOrigin}${path}`, {
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));

    if (
      errorData.exc_type === "CSRFTokenError" ||
      errorData.exception?.includes("CSRFTokenError")
    ) {
      csrfTokenRequest = null;
    }

    throw Object.assign(
      new Error(
        errorData.message ||
          validationMessage(errorData) ||
          errorData.exc_type ||
          "Yêu cầu tới Frappe không thành công."
      ),
      { status: response.status }
    );
  }

  return response.json();
}

function validationMessage(data) {
  if (!["ValidationError", "MandatoryError", "UniqueValidationError"].includes(data.exc_type)) return null;
  try {
    const entries = JSON.parse(data._server_messages ?? "[]");
    const message = JSON.parse(entries.at(-1) ?? "{}").message;
    return typeof message === "string" ? message.replace(/<[^>]+>/g, "") : null;
  } catch {
    return null;
  }
}

export async function listFrappeResources(doctype, fields, options = {}) {
  const { filters = [], signal } = options;
  const rows = [];
  const pageSize = 100;

  for (let start = 0; ; start += pageSize) {
    const params = new URLSearchParams({
      fields: JSON.stringify(fields),
      filters: JSON.stringify(filters),
      order_by: "name asc",
      limit_start: start,
      limit_page_length: pageSize,
    });
    const { data } = await frappeRequest(`/api/resource/${encodeURIComponent(doctype)}?${params}`, { signal });
    if (!Array.isArray(data)) throw new Error("Frappe trả danh sách không hợp lệ.");
    rows.push(...data);
    if (data.length < pageSize) return rows;
  }
}

export function clearCsrfToken() {
  csrfTokenRequest = null;
}


export function publicFrappeRequest(path, body) {
  return request(path, {
    method: "POST",
    credentials: "omit",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
