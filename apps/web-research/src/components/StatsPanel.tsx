// apps/web-research/src/components/StatsPanel.tsx
import { useEffect, useState } from "react";
import { fetchStats } from "../api/client";
import type { StatsResponse } from "../api/client";

export default function StatsPanel() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [error, setError] = useState(false);

  async function load() {
    try {
      const s = await fetchStats();
      setStats(s);
      setError(false);
    } catch {
      setError(true);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000); // 30초마다 갱신
    return () => clearInterval(id);
  }, []);

  return (
    <section className="card stats-card">
      <h2>📊 Stats</h2>
      {error && <p className="muted">/admin/stats 엔드포인트 준비 중…</p>}
      {stats && (
        <table className="stats-table">
          <tbody>
            <tr><td>오늘 피드백</td><td><strong>{stats.today_feedbacks}</strong></td></tr>
            <tr><td>전체 피드백</td><td><strong>{stats.total_feedbacks}</strong></td></tr>
            <tr><td>Rule 서빙</td><td><strong>{stats.rule_served}</strong></td></tr>
            <tr><td>LTR 서빙</td><td><strong>{stats.ltr_served}</strong></td></tr>
          </tbody>
        </table>
      )}
      <button className="refresh-btn" onClick={load}>↻ 갱신</button>
    </section>
  );
}
