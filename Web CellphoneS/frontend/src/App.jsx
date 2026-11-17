
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard/Dashboard";

function Placeholder({ title }) {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
      <p className="mt-2 text-slate-500">
        Chức năng đang được phát triển.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/leads" element={<Placeholder title="Leads" />} />
          <Route path="/deals" element={<Placeholder title="Deals" />} />
          <Route path="/customers" element={<Placeholder title="Customers" />} />
          <Route path="/after-sales" element={<Placeholder title="After-sales" />} />
          <Route path="/analytics" element={<Placeholder title="Analytics" />} />
        </Route>

        <Route path="*" element={<Placeholder title="404 - Không tìm thấy trang" />} />
      </Routes>
    </BrowserRouter>
  );
}
