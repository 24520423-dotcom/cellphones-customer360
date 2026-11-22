
import { frappeRequest, listFrappeResources } from "./api";

const LEAD_ENDPOINT = "/api/resource/CRM%20Lead";

export async function listLeads(options = {}) {
  const fields = [
    "name",
    "lead_name",
    "email",
    "mobile_no",
    "status",
    "source",
    "lead_owner",
    "custom_consultation_notes",
  ];

  const rows = await listFrappeResources("CRM Lead", fields, options);
  return rows.map((lead) => ({
    id: lead.name,
    name: lead.lead_name || lead.name,
    phone: lead.mobile_no?.trim() || "",
    email: lead.email || "",
    source: lead.source || "—",
    status: lead.status || "—",
    owner: lead.lead_owner || "Chưa phân công",
    notes: lead.custom_consultation_notes || "",
  }));
}

function toLeadPayload(form) {
  const fullName = form.name.trim();
  const parts = fullName.split(/\s+/);

  return {
    first_name: parts.slice(0, -1).join(" ") || fullName,
    last_name: parts.length > 1 ? parts.at(-1) : "",
    email: form.email?.trim() || "",
    mobile_no: form.phone?.trim() || "",
    source: form.source || null,
    status: form.status || "New",
    lead_owner: form.owner || null,
    custom_consultation_notes: form.notes?.trim() || "",
  };
}

export async function createLead(form) {
  return frappeRequest(LEAD_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(toLeadPayload(form)),
  });
}

export async function updateLead(id, form) {
  return frappeRequest(
    `${LEAD_ENDPOINT}/${encodeURIComponent(id)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(toLeadPayload(form)),
    }
  );
}

export async function getLeadOptions(id, { signal } = {}) {
  const query = id ? `?${new URLSearchParams({ lead: id })}` : "";
  const { message } = await frappeRequest(`/api/method/cellphones_c360.api.leads.get_options${query}`, { signal });
  return message;
}
