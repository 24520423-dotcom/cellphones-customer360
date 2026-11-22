import { useEffect, useRef, useState } from "react";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import Modal from "../../components/Modal";
import Table from "../../components/Table";
import { changeEmployeeRole, changeEmployeeStatus, listEmployees } from "../../services/employeeAdminService";
import { displayDate } from "../../utils/customer360";

export default function Employees() {
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState({ search: "", page: 1, revision: 0 });
  const [result, setResult] = useState(null);
  const [selection, setSelection] = useState(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const lock = useRef(false);
  const current = result?.query === query ? result : null;

  useEffect(() => {
    const controller = new AbortController();
    listEmployees({ search: query.search, page: query.page }, controller.signal).then(
      (data) => { if (!controller.signal.aborted) setResult({ query, data }); },
      (error) => { if (!controller.signal.aborted) setResult({ query, error: error.message }); },
    );
    return () => controller.abort();
  }, [query]);

  function close() {
    if (!lock.current) setSelection(null);
  }

  function select(employee, action) {
    setNotice("");
    setError("");
    setSelection({ employee, action });
  }

  async function save(event) {
    event.preventDefault();
    if (lock.current) return;
    const { employee, action } = selection;
    const role = new FormData(event.currentTarget).get("role");
    lock.current = true;
    setSaving(true);
    setError("");
    try {
      if (action === "role") {
        await changeEmployeeRole(employee.name, role);
        setNotice("Đã lưu vai trò nhân viên.");
      } else {
        await changeEmployeeStatus(employee.name, !employee.enabled);
        setNotice(employee.enabled ? "Đã vô hiệu hóa tài khoản." : "Đã kích hoạt tài khoản.");
      }
      setSelection(null);
      setQuery((previous) => ({ ...previous, revision: previous.revision + 1 }));
    } catch (error) {
      setError(error.message);
    } finally {
      lock.current = false;
      setSaving(false);
    }
  }

  const columns = [
    { key: "full_name", label: "Họ và tên" },
    { key: "email", label: "Email", render: (value) => <span className="break-all">{value}</span> },
    { key: "roles", label: "Vai trò được gán", render: (value) => value.join(", ") || "—" },
    { key: "enabled", label: "Trạng thái", render: (value) => value ? "Đang hoạt động" : "Đã vô hiệu hóa" },
    { key: "creation", label: "Ngày tạo", render: displayDate },
    { key: "name", label: "Thao tác", render: (_, employee) => employee.manageable ? (
      <div className="flex min-w-36 flex-wrap gap-2">
        <Button size="sm" variant="secondary" onClick={() => select(employee, "role")}>Đổi vai trò</Button>
        <Button size="sm" variant="outline" onClick={() => select(employee, "status")}>{employee.enabled ? "Vô hiệu hóa" : "Kích hoạt lại"}</Button>
      </div>
    ) : <span className="text-sm text-muted">Tài khoản được bảo vệ</span> },
  ];
  const employee = selection?.employee;

  return (
    <section className="crm-card min-w-0 space-y-4">
      <h2 className="text-lg font-semibold">Quản lý nhân viên</h2>
      <form className="flex flex-wrap gap-2" onSubmit={(event) => { event.preventDefault(); setQuery({ search: draft.trim(), page: 1, revision: 0 }); }}>
        <input type="search" className="crm-input max-w-sm" aria-label="Tìm nhân viên" placeholder="Họ tên hoặc email" maxLength={140} value={draft} onChange={(event) => setDraft(event.target.value)} />
        <Button type="submit" variant="secondary">Tìm kiếm</Button>
      </form>
      {notice && <p role="status" className="text-sm text-green-800">{notice}</p>}
      {!current && <Loading label="Đang tải danh sách nhân viên…" />}
      {current?.error && <p role="alert" className="text-primary">{current.error}</p>}
      {current?.data && (
        <>
          <Table data={current.data.items} columns={columns} getRowKey={({ name }) => name} emptyMessage="Không tìm thấy nhân viên phù hợp." />
          {(query.page > 1 || current.data.has_more) && (
            <div className="flex items-center gap-2">
              <Button size="sm" variant="secondary" disabled={query.page === 1} onClick={() => setQuery({ ...query, page: query.page - 1 })}>Trang trước</Button>
              <span className="text-sm">Trang {query.page}</span>
              <Button size="sm" variant="secondary" disabled={!current.data.has_more} onClick={() => setQuery({ ...query, page: query.page + 1 })}>Trang sau</Button>
            </div>
          )}
        </>
      )}
      {employee && (
        <Modal isOpen title={selection.action === "role" ? "Đổi vai trò" : employee.enabled ? "Vô hiệu hóa tài khoản" : "Kích hoạt lại tài khoản"} onClose={close}>
          <form className="space-y-3" onSubmit={save}>
            <p className="break-all text-sm">{employee.email || employee.name}</p>
            {selection.action === "role" ? (
              <label className="block text-sm font-medium">
                Vai trò bán hàng
                <select name="role" className="crm-input" required disabled={saving} defaultValue="">
                  <option value="">Chọn vai trò</option>
                  {current?.data?.roles.map((role) => <option key={role}>{role}</option>)}
                </select>
              </label>
            ) : (
              <p className="text-sm text-muted">{employee.enabled
                ? "Nhân viên sẽ mất quyền đăng nhập và truy cập API."
                : "Nhân viên sẽ có thể đăng nhập lại với vai trò hiện tại."}</p>
            )}
            {error && <p role="alert" className="text-sm text-primary">{error}</p>}
            <div className="flex justify-end gap-2">
              <Button variant="secondary" disabled={saving} onClick={close}>Hủy</Button>
              <Button type="submit" loading={saving}>Xác nhận</Button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
