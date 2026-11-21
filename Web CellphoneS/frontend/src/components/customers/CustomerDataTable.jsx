import { ChevronRight } from "lucide-react";

// Compact L01 table, visually matches Customer 360 panels and does not mutate shared Table.jsx.
export default function CustomerDataTable({ columns, data, loading, emptyMessage, getRowKey }) {
  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[860px] border-collapse text-left text-sm">
        <caption className="sr-only">Danh sách hồ sơ khách hàng Customer 360</caption>
        <thead className="border-b border-gray-200 bg-[#f9fafb] text-[11px] font-semibold uppercase tracking-[0.08em] text-gray-500">
          <tr>
            {columns.map((column) => <th key={column.key} scope="col" className="px-5 py-3.5">{column.label}</th>)}
            <th scope="col" className="w-8 pr-5"><span className="sr-only">Mở hồ sơ</span></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#edf0f2]">
          {loading ? (
            <tr><td colSpan={columns.length + 1} className="px-5 py-10 text-center text-gray-500">Đang tải dữ liệu…</td></tr>
          ) : data.length === 0 ? (
            <tr><td colSpan={columns.length + 1}>{emptyMessage}</td></tr>
          ) : data.map((row, index) => (
            <tr key={getRowKey ? getRowKey(row) : row.id ?? index} className="group transition-colors hover:bg-[#fcf7f7]">
              {columns.map((column) => (
                <td key={column.key} className="px-5 py-3.5 align-middle text-gray-800">
                  {column.render ? column.render(row[column.key], row) : row[column.key] ?? "—"}
                </td>
              ))}
              <td className="pr-5 text-gray-300 group-hover:text-primary"><ChevronRight size={16} aria-hidden="true" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
