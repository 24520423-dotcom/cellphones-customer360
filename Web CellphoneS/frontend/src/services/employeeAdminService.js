import { frappeRequest } from "./api";

async function adminAction(action, payload = {}, signal) {
  const { message } = await frappeRequest("/api/method/cellphones_c360.api.employee_administration." + action, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  return message;
}

export const listEmployees = (filters, signal) => adminAction("list_employees", filters, signal);
export const changeEmployeeRole = (name, role) => adminAction("set_employee_role", { name, role });
export const changeEmployeeStatus = (name, enabled) => adminAction("set_employee_enabled", { name, enabled });
export const getPermissionMatrix = (signal) => adminAction("permission_matrix", {}, signal);
export const listRoles = (filters, signal) => adminAction("list_roles", filters, signal);
