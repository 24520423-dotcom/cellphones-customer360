import { useEffect, useState } from "react";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import Table from "../../components/Table";
import { listRoles } from "../../services/employeeAdminService";

const columns = [
  { key: "name", label: "Vai trò", render: (name) => <span className="font-semibold">{name}</span> },
  { key: "is_custom", label: "Nguồn gốc", render: (value) => value ? "Tùy chỉnh" : "Hệ thống" },
  { key: "disabled", label: "Trạng thái", render: (value) => value ? "Đã vô hiệu hóa" : "Đang sử dụng" },
  { key: "employee_count", label: "Nhân viên được gán", render: (value) => value.toLocaleString("vi-VN") },
];

export default function RoleList() {
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState({ search: "", page: 1 });
  const [result, setResult] = useState(null);
  const current = result?.query === query ? result : null;

  useEffect(() => {
    const controller = new AbortController();
    listRoles(query, controller.signal).then(
      (data) => { if (!controller.signal.aborted) setResult({ query, data }); },
      (error) => { if (!controller.signal.aborted) setResult({ query, error: error.message }); },
    );
    return () => controller.abort();
  }, [query]);

  return (
    <section className="crm-card min-w-0 space-y-4">
      <h2 className="text-lg font-semibold">Quản lý vai trò</h2>
      <form className="flex flex-wrap gap-2" onSubmit={(event) => { event.preventDefault(); setQuery({ search: draft.trim(), page: 1 }); }}>
        <input type="search" aria-label="Tìm vai trò" placeholder="Tên vai trò" maxLength={140} value={draft} onChange={(event) => setDraft(event.target.value)} className="crm-input max-w-sm" />
        <Button type="submit" variant="secondary">Tìm kiếm</Button>
      </form>
      {!current && <Loading label="Đang tải vai trò…" />}
      {current?.error && (
        <div className="flex flex-wrap items-center gap-3">
          <p role="alert" className="text-sm text-primary">{current.error}</p>
          <Button size="sm" variant="secondary" onClick={() => setQuery({ ...query })}>Thử lại</Button>
        </div>
      )}
      {current?.data && (
        <>
          <Table columns={columns} data={current.data.items} getRowKey={({ name }) => name} emptyMessage="Không tìm thấy vai trò phù hợp." />
          {(query.page > 1 || current.data.has_more) && (
            <nav aria-label="Phân trang vai trò" className="flex flex-wrap items-center gap-2">
              <Button size="sm" variant="secondary" disabled={query.page === 1} onClick={() => setQuery({ ...query, page: query.page - 1 })}>Trang trước</Button>
              <span className="text-sm">Trang {query.page}</span>
              <Button size="sm" variant="secondary" disabled={!current.data.has_more} onClick={() => setQuery({ ...query, page: query.page + 1 })}>Trang sau</Button>
            </nav>
          )}
        </>
      )}
    </section>
  );
}
