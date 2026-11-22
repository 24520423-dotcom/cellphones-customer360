import { frappeRequest, listFrappeResources } from "./api";

const ticketType = "Customer Support Ticket";
const customerType = "C360 Customer";
const orderType = "Customer Order";
const resource = (doctype) => `/api/resource/${encodeURIComponent(doctype)}`;
const ticketFields = ["name", "customer", "related_order", "subject", "ticket_type", "ticket_status", "priority", "created_date", "assigned_to"];



function normalizeTicket(row) {
  return {
    id: row.name,
    customer: row.customer,
    relatedOrder: row.related_order,
    subject: row.subject,
    description: row.description,
    type: row.ticket_type,
    status: row.ticket_status,
    priority: row.priority,
    createdAt: row.created_date,
    modifiedAt: row.modified,
    assignedTo: row.assigned_to,
    resolvedAt: row.resolved_date,
    resolution: row.resolution,
  };
}

export async function listTickets(options = {}) {
  const rows = await listFrappeResources(ticketType, ticketFields, options);
  const customerIds = [...new Set(rows.map(({ customer }) => customer).filter(Boolean))];
  const labels = new Map();
  for (let offset = 0; offset < customerIds.length; offset += 100) {
    const ids = customerIds.slice(offset, offset + 100);
    try {
      const customers = await listFrappeResources(customerType, ["name", "customer_name"], {
        signal: options.signal,
        filters: [["name", "in", ids]],
      });
      for (const { name, customer_name } of customers) labels.set(name, customer_name);
    } catch (error) {
      if (error.status === 403) break;
      throw error;
    }
  }
  return rows.map((row) => ({ ...normalizeTicket(row), customerName: labels.get(row.customer) }));
}

export async function getTicket(id, { signal } = {}) {
  const { data } = await frappeRequest(`${resource(ticketType)}/${encodeURIComponent(id)}`, { signal });
  return normalizeTicket(data);
}

async function saveTicket(path, method, payload) {
  const { data } = await frappeRequest(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return normalizeTicket(data);
}

export function createTicket(payload) {
  return saveTicket(resource(ticketType), "POST", {
    customer: payload.customer,
    related_order: payload.relatedOrder || null,
    subject: payload.subject,
    description: payload.description,
    ticket_type: payload.type,
    ticket_status: payload.status,
    priority: payload.priority,
  });
}

export function updateTicket(id, payload) {
  return saveTicket(`${resource(ticketType)}/${encodeURIComponent(id)}`, "PUT", {
    ticket_status: payload.status,
    resolution: payload.resolution,
  });
}

export async function listCustomersForTicket({ signal } = {}) {
  const rows = await listFrappeResources(customerType, ["name", "customer_name"], { signal });
  return rows.map(({ name, customer_name }) => ({ id: name, label: customer_name || name }));
}

export async function listOrdersByCustomer(customer, { signal } = {}) {
  const rows = await listFrappeResources(orderType, ["name"], { filters: [["customer", "=", customer]], signal });
  return rows.map(({ name }) => ({ id: name, label: name }));
}

export async function getTicketCapabilities(id, { signal } = {}) {
  const query = id ? `?${new URLSearchParams({ ticket: id })}` : "";
  const { message } = await frappeRequest(`/api/method/cellphones_c360.api.after_sales.get_capabilities${query}`, { signal });
  return message;
}
