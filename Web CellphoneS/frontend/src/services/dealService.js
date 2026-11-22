import { frappeRequest, listFrappeResources } from "./api";

const doctype = "CRM Deal";
const endpoint = "/api/resource/CRM%20Deal";
const fields = ["name", "lead", "status", "deal_owner", "organization_name", "lead_name", "deal_value", "expected_deal_value", "closed_date", "next_step", "currency"];

function normalize(row) {
  return {
    ...row,
    title: row.organization_name || row.lead_name || row.name,
    ownerDisplay: row.deal_owner ?? "",
    notes: row.next_step ?? "",
  };
}

export async function listDeals({ signal } = {}) {
  const [{ message: options }, records] = await Promise.all([
    frappeRequest("/api/method/cellphones_c360.api.deals.get_options", { signal }),
    listFrappeResources(doctype, fields, { signal }),
  ]);
  return { ...options, deals: records.map(normalize) };
}

async function save(path, method, payload) {
  const { data } = await frappeRequest(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return normalize(data);
}

const recordPath = (id) => `${endpoint}/${encodeURIComponent(id)}`;

export async function getDeal(id, { signal } = {}) {
  const { data } = await frappeRequest(recordPath(id), { signal });
  return normalize(data);
}

export async function getDealCapabilities(id, { signal } = {}) {
  const query = new URLSearchParams({ deal: id });
  const { message } = await frappeRequest(`/api/method/cellphones_c360.api.deals.get_options?${query}`, { signal });
  return message;
}

export function saveDeal(id, values) {
  const payload = {
    organization_name: values.title || null,
    lead: values.lead || null,
    status: values.status,
    expected_deal_value: values.expected_deal_value,
    deal_value: values.deal_value,
    closed_date: values.closed_date || null,
    deal_owner: values.ownerDisplay || null,
    next_step: values.notes || null,
    currency: values.currency || "VND",
  };
  return save(id ? recordPath(id) : endpoint, id ? "PUT" : "POST", payload);
}

export function updateDealStage(id, status) {
  return save(recordPath(id), "PUT", { status });
}
