import { useEffect, useState } from "react";
import Button from "../../components/Button";
import Loading from "../../components/Loading";
import Table from "../../components/Table";
import { crmRoutes } from "../../routes/crmRoutes";
import { getPermissionMatrix } from "../../services/employeeAdminService";

const modules = [
  ["/dashboard", ["CRM Lead", "CRM Deal", "CRM Call Log", "CRM Task", "Customer Order", "Customer Support Ticket"]],
  ["/leads", ["CRM Lead", "CRM Call Log", "CRM Task"]],
  ["/deals", ["CRM Deal"]],
  ["/customers", ["C360 Customer", "Customer Order", "CRM Lead", "CRM Deal", "Customer Support Ticket"]],
  ["/after-sales", ["Customer Support Ticket", "C360 Customer", "Customer Order"]],
  ["/analytics", ["C360 Customer", "CRM Lead", "CRM Deal", "Customer Order", "Customer Support Ticket"]],
  ["/admin", ["User", "C360 Registration Request"]],
];

const actions = {
  read: "Xem", write: "Sửa", create: "Tạo", delete: "Xóa", select: "Chọn",
  submit: "Gửi", cancel: "Hủy", amend: "Sửa bản đã gửi", report: "Báo cáo",
  export: "Xuất", import: "Nhập", share: "Chia sẻ", print: "In", email: "Email",
};

function PermissionRules({ doctypes, role, matrix }) {
  if (role === "Administrator") return "Toàn quyền DocType";
  return (
    <ul className="min-w-44 space-y-2">
      {doctypes.map((doctype) => {
        const rules = matrix.rules[doctype]?.filter((rule) => rule.role === role || matrix.implicit_roles.includes(rule.role));
        return (
          <li key={doctype}>
            <p className="font-medium">{doctype}</p>
            {rules?.length ? rules.map((rule, index) => (
              <p key={`${rule.role}-${index}`} className="text-xs text-muted">
                {rule.operations.map((operation) => actions[operation] ?? operation).join(", ") || "Không cấp thao tác"}
                {rule.owner_only && " · Chỉ chủ sở hữu"}
                {rule.level > 0 && ` · Cấp trường ${rule.level}`}
                {rule.role !== role && ` · ${rule.role}`}
              </p>
            )) : <p className="text-xs text-muted">Chưa có quy tắc cho các vai trò đang đối chiếu</p>}
          </li>
        );
      })}
    </ul>
  );
}

export default function PermissionMatrix() {
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState(null);
  const current = result?.revision === revision ? result : null;

  useEffect(() => {
    const controller = new AbortController();
    getPermissionMatrix(controller.signal).then(
      (data) => { if (!controller.signal.aborted) setResult({ revision, data }); },
      (error) => { if (!controller.signal.aborted) setResult({ revision, error: error.message }); },
    );
    return () => controller.abort();
  }, [revision]);

  const matrix = current?.data;
  const rows = modules.map(([path, doctypes]) => ({
    id: path, doctypes, module: crmRoutes.find((route) => route.path === path)?.label,
    menu: path === "/admin" ? "Theo quyền Administration của phiên" : "Hiện khi đăng nhập",
    api: path === "/admin" ? "Quản lý nhân viên và quyền yêu cầu Administrator + CSRF"
      : "Yêu cầu tài khoản hoạt động và quyền dữ liệu Frappe tương ứng",
  }));
  const columns = [
    { key: "module", label: "Module" },
    { key: "menu", label: "Menu", render: (value) => <p className="min-w-28">{value}</p> },
    { key: "api", label: "Truy cập API", render: (value) => <p className="min-w-40">{value}</p> },
    ...(matrix?.roles ?? []).map((role) => ({
      key: role, label: role,
      render: (_, row) => <PermissionRules doctypes={row.doctypes} role={role} matrix={matrix} />,
    })),
  ];

  return (
    <section className="crm-card min-w-0 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Quản lý phân quyền</h2>
        <Button size="sm" variant="secondary" onClick={() => setRevision((value) => value + 1)}>Tải lại</Button>
      </div>
      <p className="text-sm text-muted">Ma trận chỉ đọc từ DocType Permission của Frappe. Quyền thực tế trên từng bản ghi còn phụ thuộc vào người sở hữu, chia sẻ, User Permissions, các vai trò khác được gán và quy tắc nghiệp vụ.</p>
      {!current && <Loading label="Đang tải ma trận quyền…" />}
      {current?.error && <p role="alert" className="text-primary">{current.error}</p>}
      {matrix && <Table columns={columns} data={rows} />}
    </section>
  );
}
