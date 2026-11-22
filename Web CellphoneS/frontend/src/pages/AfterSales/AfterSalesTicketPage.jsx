import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Loading from "../../components/Loading";
import { getTicket, getTicketCapabilities, updateTicket } from "../../services/afterSalesService";
import AfterSalesDetail from "./AfterSalesDetail";

export default function AfterSalesTicketPage() {
  const { ticketId } = useParams();
  return <TicketPage key={ticketId} ticketId={ticketId} />;
}

function TicketPage({ ticketId }) {
  const [result, setResult] = useState(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };

    Promise.all([
      getTicket(ticketId, options),
      getTicketCapabilities(ticketId, options).catch(() => ({ canEdit: false })),
    ]).then(
      ([ticket, capabilities]) => {
        if (!controller.signal.aborted) setResult({ ticket, canEdit: capabilities.canEdit });
      },
      (error) => {
        if (!controller.signal.aborted) setResult({ error });
      },
    );

    return () => controller.abort();
  }, [ticketId]);

  async function save(id, payload) {
    const saved = await updateTicket(id, payload);
    const ticket = await getTicket(id).catch(() => saved);
    setResult((previous) => ({ ...previous, ticket }));
    setNotice("Đã lưu thay đổi.");
  }

  return (
    <section className="crm-card space-y-5">
      <Link to="/after-sales" className="text-sm font-medium text-primary hover:underline">Về danh sách hậu mãi</Link>
      <h1 className="break-words text-2xl font-bold">Ticket {ticketId}</h1>
      {!result && <Loading label="Đang tải Ticket…" />}
      {result?.error && <p role="alert" className="text-primary">{result.error.status === 404 ? "Không tìm thấy Ticket." : result.error.message}</p>}
      {notice && <p role="status" className="text-sm font-medium text-green-800">{notice}</p>}
      {result?.ticket && <AfterSalesDetail ticket={result.ticket} canEdit={result.canEdit} onUpdate={save} />}
    </section>
  );
}
