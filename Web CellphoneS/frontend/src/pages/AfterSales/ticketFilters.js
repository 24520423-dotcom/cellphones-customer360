import { toDate } from "../../utils/customer360.js";

function normalize(value) {
  return String(value ?? "").toLocaleLowerCase("vi-VN").normalize("NFD")
    .replace(/\p{Mark}/gu, "").replaceAll("đ", "d");
}

export function filterTickets(tickets, { query = "", status = "", from = "", to = "", order = "desc" }) {
  const search = normalize(query.trim());
  const start = from ? toDate(`${from}T00:00:00`) : null;
  const end = to ? toDate(`${to}T00:00:00`) : null;
  if (end) end.setDate(end.getDate() + 1);

  return tickets
    .map((ticket) => ({ ticket, date: toDate(ticket.createdAt?.replace(" ", "T")) }))
    .filter(({ ticket, date }) => {
      if (status && ticket.status !== status) return false;
      if ((start || end) && !date) return false;
      if ((start && date < start) || (end && date >= end)) return false;
      return [ticket.id, ticket.customer, ticket.customerName, ticket.subject]
        .some((value) => normalize(value).includes(search));
    })
    .sort((a, b) => {
      if (!a.date) return b.date ? 1 : 0;
      if (!b.date) return -1;
      return order === "asc" ? a.date - b.date : b.date - a.date;
    })
    .map(({ ticket }) => ticket);
}
