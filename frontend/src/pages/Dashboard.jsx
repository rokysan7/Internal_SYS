import { useEffect, useState } from 'react';
import { getCases, getStatistics } from '../api/cases';
import CaseList from '../components/CaseList';
import './shared.css';
import './Dashboard.css';

export default function Dashboard() {
  const [cases, setCases] = useState([]);
  const [statusStats, setStatusStats] = useState([]);
  const [timeStats, setTimeStats] = useState(null);
  const [assigneeStats, setAssigneeStats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [casesRes, statusRes, timeRes, assigneeRes] = await Promise.all([
          getCases(),
          getStatistics('status'),
          getStatistics('time'),
          getStatistics('assignee'),
        ]);
        setCases(casesRes.data);
        setStatusStats(statusRes.data);
        setTimeStats(timeRes.data);
        setAssigneeStats(assigneeRes.data);
      } catch (err) {
        console.error('Dashboard data fetch failed:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <div className="loading">Loading...</div>;

  const totalCases = cases.length;
  const countByStatus = (status) => {
    const found = statusStats.find((s) => s.status === status);
    return found ? found.count : 0;
  };

  const recentCases = [...cases]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 10);

  const avgHours = timeStats?.avg_hours;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      {/* Status Summary Cards */}
      <div className="card-grid">
        <div className="stat-card accent-blue">
          <span className="stat-label">Total Cases</span>
          <span className="stat-value">{totalCases}</span>
        </div>
        <div className="stat-card accent-yellow">
          <span className="stat-label">Open</span>
          <span className="stat-value">{countByStatus('OPEN')}</span>
        </div>
        <div className="stat-card accent-orange">
          <span className="stat-label">In Progress</span>
          <span className="stat-value">{countByStatus('IN_PROGRESS')}</span>
        </div>
        <div className="stat-card accent-green">
          <span className="stat-label">Done</span>
          <span className="stat-value">{countByStatus('DONE')}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Avg. Resolution</span>
          <span className="stat-value">
            {avgHours != null ? `${avgHours.toFixed(1)}h` : '-'}
          </span>
        </div>
      </div>

      {/* Assignee Statistics */}
      {assigneeStats.length > 0 && (
        <div className="section">
          <div className="section-title">담당자별 업무 현황</div>
          <div className="card">
            <table className="assignee-stats-table">
              <thead>
                <tr>
                  <th>담당자</th>
                  <th style={{ textAlign: 'center' }}>Open</th>
                  <th style={{ textAlign: 'center' }}>In Progress</th>
                  <th style={{ textAlign: 'center' }}>Done</th>
                  <th style={{ textAlign: 'center' }}>합계</th>
                </tr>
              </thead>
              <tbody>
                {assigneeStats.map((a) => (
                  <tr key={a.assignee_id}>
                    <td>{a.assignee_name || `User #${a.assignee_id}`}</td>
                    <td className="count-cell count-open">{a.open_count}</td>
                    <td className="count-cell count-progress">{a.in_progress_count}</td>
                    <td className="count-cell count-done">{a.done_count}</td>
                    <td className="count-cell">
                      {a.open_count + a.in_progress_count + a.done_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recent Cases Table */}
      <div className="section">
        <div className="section-title">Recent Cases</div>
        <CaseList cases={recentCases} />
      </div>
    </div>
  );
}
