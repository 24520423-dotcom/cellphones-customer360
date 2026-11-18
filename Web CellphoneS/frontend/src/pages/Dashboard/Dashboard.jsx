
import { useMemo, useState } from "react";
import {
  Users,
  Handshake,
  CircleCheck,
  TrendingUp,
} from "lucide-react";


import RecentActivities from "./RecentActivities";
import KPICard from "./KPICard";
import LeadChart from "./LeadChart";
import DealChart from "./DealChart";
import DashboardFilters from "./DashboardFilters";

// Dữ liệu DEMO theo từng khoảng thời gian.
// Sau này sẽ thay bằng API Frappe.
const demoData = {
  all: {
    leads: [45, 35, 28, 20],
    deals: [18, 14, 10, 8, 4],
  },
  "7d": {
    leads: [12, 9, 6, 3],
    deals: [5, 4, 3, 2, 1],
  },
  "30d": {
    leads: [25, 20, 15, 10],
    deals: [10, 8, 6, 4, 2],
  },
  "90d": {
    leads: [38, 30, 22, 15],
    deals: [15, 12, 9, 7, 3],
  },
};

const leadStatuses = [
  "New",
  "Contacted",
  "Qualified",
  "Unqualified",
];

const dealStages = [
  "New",
  "Qualified",
  "Proposal",
  "Won",
  "Lost",
];

export default function Dashboard() {
  const [period, setPeriod] = useState("all");

  const { leadData, dealData, stats } = useMemo(() => {
    const selected = demoData[period];

    const leadData = leadStatuses.map((status, index) => ({
      status,
      count: selected.leads[index],
    }));

    const dealData = dealStages.map((stage, index) => ({
      stage,
      count: selected.deals[index],
    }));

    const totalLeads = selected.leads.reduce(
      (sum, count) => sum + count, 0
    );

    const totalDeals = selected.deals.reduce(
      (sum, count) => sum + count, 0
    );

    const wonDeals = selected.deals[3];

    // Quy ước DEMO: Won Deals / Total Leads
    const conversionRate = totalLeads
      ? ((wonDeals / totalLeads) * 100).toFixed(1) + "%"
      : "0%";

    return {
      leadData,
      dealData,
      stats: {
        totalLeads,
        totalDeals,
        wonDeals,
        conversionRate,
      },
    };
  }, [period]);

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            Dashboard
          </h1>
          <p className="mt-2 text-slate-500">
            Tổng quan hoạt động CRM của CellphoneS · Dữ liệu minh họa
          </p>
        </div>

        <DashboardFilters
          period={period}
          onPeriodChange={setPeriod}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        <KPICard
          title="Total Leads"
          value={stats.totalLeads}
          icon={Users}
          description="Tổng khách hàng tiềm năng"
        />

        <KPICard
          title="Total Deals"
          value={stats.totalDeals}
          icon={Handshake}
          description="Tổng cơ hội bán hàng"
        />

        <KPICard
          title="Won Deals"
          value={stats.wonDeals}
          icon={CircleCheck}
          description="Cơ hội bán hàng thành công"
        />

        <KPICard
          title="Conversion Rate"
          value={stats.conversionRate}
          icon={TrendingUp}
          description="Tỷ lệ Lead thành giao dịch thành công"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <LeadChart data={leadData} />
        <DealChart data={dealData} />
      </div>

      <RecentActivities period={period} />

    </div>
  );
}
