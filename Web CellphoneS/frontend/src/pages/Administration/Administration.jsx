import { useState } from "react";
import Button from "../../components/Button";
import { useAuth } from "../../hooks/useAuth";
import Employees from "./Employees";
import PermissionMatrix from "./PermissionMatrix";
import RoleList from "./RoleList";
import RegistrationRequests from "./RegistrationRequests";

const sections = [
  ["employees", "Quản lý nhân viên"],
  ["roles", "Quản lý vai trò"],
  ["permissions", "Quản lý phân quyền"],
  ["registration", "Xét duyệt đăng ký"],
];

export default function Administration() {
  const { session } = useAuth();
  const [active, setActive] = useState("employees");
  return (
    <div className="min-w-0 space-y-5">
      <h1 className="text-2xl font-bold">Quản trị hệ thống</h1>
      {session?.user?.id === "Administrator" ? (
        <>
          <nav aria-label="Mục quản trị" className="flex flex-wrap gap-2">
            {sections.map(([section, label]) => (
              <Button key={section} onClick={() => setActive(section)} aria-pressed={active === section} variant={active === section ? "primary" : "secondary"}>{label}</Button>
            ))}
          </nav>
          {active === "employees" && <Employees />}
          {active === "roles" && <RoleList />}
          {active === "permissions" && <PermissionMatrix />}
          {active === "registration" && <RegistrationRequests />}
        </>
      ) : <p className="crm-card text-sm text-muted">Các thao tác quản trị tại đây yêu cầu tài khoản Administrator.</p>}
    </div>
  );
}
