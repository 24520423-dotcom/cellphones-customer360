import { useEffect, useState } from "react";
import { getAnalyticsOverview } from "../services/analyticsService";

export default function useAnalytics(activities = false) {
  const [period, setPeriod] = useState("all");
  const [revision, setRevision] = useState(0);
  const [result, setResult] = useState(null);
  const key = `${period}:${revision}`;
  const current = result?.key === key ? result : null;

  useEffect(() => {
    const controller = new AbortController();
    getAnalyticsOverview(period, { signal: controller.signal, activities }).then(
      (data) => { if (!controller.signal.aborted) setResult({ key, data }); },
      (error) => { if (!controller.signal.aborted) setResult({ key, error: error.message }); },
    );
    return () => controller.abort();
  }, [activities, key, period]);

  return {
    period,
    setPeriod,
    reload: () => setRevision((value) => value + 1),
    loading: !current,
    result: current?.data,
    error: current?.error,
  };
}
