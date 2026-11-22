import { useEffect, useRef, useState } from "react";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import Modal from "../../components/Modal";
import Table from "../../components/Table";
import { listRegistrationRequests, retryRegistrationInvitation, reviewRegistration } from "../../services/registrationService";
import { displayDateTime } from "../../utils/customer360";

const statuses = { Pending: "Chờ duyệt", Approved: "Đã duyệt", Rejected: "Đã từ chối", All: "Tất cả" };
const invitations = { "Not Queued": "Chưa gửi", Queued: "Đang chờ gửi", Sent: "Đã gửi", Failed: "Gửi thất bại" };

export default function RegistrationRequests() {
  const [status, setStatus] = useState("Pending");
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState(null);
  const [selection, setSelection] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lock = useRef(false);
  const key = [status, page, revision].join("/");
  const current = result?.key === key ? result : null;

  useEffect(() => {
    const controller = new AbortController();
    listRegistrationRequests(status, page, controller.signal).then(
      (data) => { if (!controller.signal.aborted) setResult({ key, data }); },
      (error) => { if (!controller.signal.aborted) setResult({ key, error: error.message }); },
    );
    return () => controller.abort();
  }, [status, page, key]);

  function reload() {
    setRevision((value) => value + 1);
  }

  function close() {
    if (!lock.current) {
      setSelection(null);
      setError("");
    }
  }

  async function run(request) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const response = await request();
      setSelection(null);
      setNotice(response.status === "Rejected"
        ? "Đã từ chối yêu cầu."
        : `Đã duyệt. Email thiết lập mật khẩu: ${invitations[response.invitation_status] ?? "Chưa xác định"}.`);
      reload();
    } catch (error) {
      setError(error.message || "Không thể xử lý yêu cầu.");
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget, event.nativeEvent.submitter);
    const reason = String(form.get("reason") ?? "").trim();
    if (!reason) {
      setError("Vui lòng nhập lý do.");
      return;
    }
    run(() => reviewRegistration({ name: selection.name, decision: form.get("decision"), reason, role: form.get("role") }));
  }

  const columns = [
    { key: "full_name", label: "Họ tên", render: (value, row) => (
      <div className="min-w-44">
        <p className="font-medium">{value}</p>
        <p className="break-all text-xs text-muted">{row.email}</p>
        <p className="text-xs text-muted">{row.phone}</p>
      </div>
    ) },
    { key: "department", label: "Bộ phận" },
    { key: "creation", label: "Đã gửi", render: displayDateTime },
    { key: "status", label: "Trạng thái", render: (value, row) => (
      <div className="min-w-36">
        <p className="font-medium">{statuses[value]}</p>
        {row.assigned_role && <p className="text-xs text-muted">{row.assigned_role} · {invitations[row.invitation_status]}</p>}
        {row.reason && <p className="mt-1 whitespace-pre-wrap break-words text-xs text-muted">{row.reason}</p>}
      </div>
    ) },
    { key: "name", label: "Thao tác", render: (id, row) => (
      row.status === "Pending" ? <Button size="sm" disabled={busy} onClick={() => { setError(""); setSelection(row); }}>Xét duyệt</Button>
        : row.invitation_status === "Failed" ? <Button size="sm" variant="outline" disabled={busy} onClick={() => run(() => retryRegistrationInvitation(id))}>Gửi lại email</Button>
          : "—"
    ) },
  ];

  return (
    <section className="crm-card min-w-0 space-y-4" aria-labelledby="registration-requests">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="registration-requests" className="text-lg font-semibold">Yêu cầu đăng ký nhân viên</h2>
        <div className="flex flex-wrap items-center gap-2">
          <select className="crm-input w-auto" aria-label="Trạng thái yêu cầu" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
            {Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <Button size="sm" variant="secondary" onClick={reload}>Tải lại</Button>
        </div>
      </div>
      {notice && <p role="status" className="text-sm text-green-800">{notice}</p>}
      {(current?.error || (!selection && error)) && <p role="alert" className="text-sm text-primary">{current?.error || error}</p>}
      {!current && <Loading label="Đang tải yêu cầu…" />}
      {current?.data && (
        <>
          <Table columns={columns} data={current.data.items} getRowKey={({ name }) => name} emptyMessage="Chưa có yêu cầu ở trạng thái này." />
          {(page > 1 || current.data.has_more) && (
            <div className="flex items-center gap-3">
              <Button size="sm" variant="secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>Trang trước</Button>
              <span className="text-sm">{page}</span>
              <Button size="sm" variant="secondary" disabled={!current.data.has_more} onClick={() => setPage(page + 1)}>Trang sau</Button>
            </div>
          )}
        </>
      )}
      {selection && (
        <Modal isOpen title="Xét duyệt yêu cầu" onClose={close}>
          <form className="space-y-4" onSubmit={submit}>
            <p className="break-words font-medium">{selection.full_name} · {selection.email}</p>
            <fieldset disabled={busy} className="space-y-3">
              <label className="block text-sm font-medium">
                Vai trò khi phê duyệt
                <select name="role" className="crm-input" defaultValue="">
                  <option value="">Chọn vai trò</option>
                  {current?.data?.roles.map((role) => <option key={role}>{role}</option>)}
                </select>
              </label>
              <label className="block text-sm font-medium">
                Lý do
                <textarea name="reason" className="crm-input" required maxLength={1000} rows={3} />
              </label>
            </fieldset>
            {error && <p role="alert" className="text-sm text-primary">{error}</p>}
            <div className="flex flex-wrap justify-end gap-2">
              <Button type="submit" variant="secondary" name="decision" value="Rejected" loading={busy}>Từ chối</Button>
              <Button type="submit" name="decision" value="Approved" loading={busy}>Phê duyệt</Button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
