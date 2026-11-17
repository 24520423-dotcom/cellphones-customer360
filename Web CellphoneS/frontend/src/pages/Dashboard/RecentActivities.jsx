
import {
  Phone,
  MessageSquare,
  Handshake,
  Headphones,
} from "lucide-react";

const activityIcons = {
  Call: Phone,
  Consultation: MessageSquare,
  Deal: Handshake,
  Support: Headphones,
};

const activities = [
  {
    id: 1,
    customer: "Nguyễn Văn A",
    type: "Call",
    description: "Gọi điện tư vấn iPhone 16",
    employee: "Nhân viên A",
    date: "2026-11-17",
    status: "Completed",
  },
  {
    id: 2,
    customer: "Trần Thị B",
    type: "Consultation",
    description: "Tư vấn Samsung Galaxy",
    employee: "Nhân viên B",
    date: "2026-11-16",
    status: "Completed",
  },
  {
    id: 3,
    customer: "Lê Văn C",
    type: "Deal",
    description: "Theo dõi cơ hội bán hàng",
    employee: "Nhân viên A",
    date: "2026-11-15",
    status: "Pending",
  },
  {
    id: 4,
    customer: "Phạm Thị D",
    type: "Support",
    description: "Tiếp nhận yêu cầu bảo hành",
    employee: "Nhân viên C",
    date: "2026-11-14",
    status: "In Progress",
  },
];

export default function RecentActivities({ period }) {
  const now = new Date("2026-11-17T23:59:59");

  const filteredActivities = activities.filter((activity) => {
    if (period === "all") return true;

    const days = Number.parseInt(period, 10);
    const activityDate = new Date(activity.date + "T00:00:00");
    const startDate = new Date(now);
    startDate.setDate(startDate.getDate() - days + 1);
    startDate.setHours(0, 0, 0, 0);

    return activityDate >= startDate && activityDate <= now;
  });

  return (
    <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-5 text-lg font-semibold text-slate-800">
        Recent Activities
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-slate-600">
            <tr>
              <th className="p-3">Khách hàng</th>
              <th className="p-3">Hoạt động</th>
              <th className="p-3">Nhân viên</th>
              <th className="p-3">Ngày</th>
              <th className="p-3">Trạng thái</th>
            </tr>
          </thead>

          <tbody>
            {filteredActivities.map((activity) => {
              const Icon = activityIcons[activity.type];

              return (
                <tr
                  key={activity.id}
                  className="border-b border-slate-100"
                >
                  <td className="p-3 font-medium">
                    {activity.customer}
                  </td>

                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Icon size={17} className="text-red-600" />
                      {activity.description}
                    </div>
                  </td>

                  <td className="p-3">{activity.employee}</td>
                  <td className="p-3">{activity.date}</td>

                  <td className="p-3">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs">
                      {activity.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredActivities.length === 0 && (
          <p className="py-8 text-center text-slate-500">
            Không có hoạt động trong khoảng thời gian này.
          </p>
        )}
      </div>
    </div>
  );
}
