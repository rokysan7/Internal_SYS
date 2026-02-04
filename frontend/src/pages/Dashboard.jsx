import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCases, getStatistics } from '../api/cases';
import { useAuth } from '../contexts/AuthContext';
import { ROLES } from '../constants/roles';
import Spinner from '../components/Spinner';
import CaseList from '../components/CaseList';
import Pagination from '../components/Pagination';
import './shared.css';
import './Dashboard.css';

const PAGE_SIZE = 5;

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [statusStats, setStatusStats] = useState([]);
  const [timeStats, setTimeStats] = useState(null);
  const [assigneeStats, setAssigneeStats] = useState([]);
  const [loading, setLoading] = useState(true);

  // Recent Cases
  const [recentCases, setRecentCases] = useState([]);
  const [recentPage, setRecentPage] = useState(1);
  const [recentTotalPages, setRecentTotalPages] = useState(1);

  // My Assigned Cases
  const [assignedCases, setAssignedCases] = useState([]);
  const [assignedPage, setAssignedPage] = useState(1);
  const [assignedTotalPages, setAssignedTotalPages] = useState(1);

  // My Created Cases
  const [createdCases, setCreatedCases] = useState([]);
  const [createdPage, setCreatedPage] = useState(1);
  const [createdTotalPages, setCreatedTotalPages] = useState(1);

  // Stats fetch (once)
  useEffect(() => {
    async function fetchStats() {
      try {
        const [statusRes, timeRes, assigneeRes] = await Promise.all([
          getStatistics('status'),
          getStatistics('time'),
          getStatistics('assignee'),
        ]);
        setStatusStats(statusRes.data);
        setTimeStats(timeRes.data);
        setAssigneeStats(assigneeRes.data);
      } catch (err) {
        console.error('Stats fetch failed:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  // Recent Cases (paginated)
  useEffect(() => {
    getCases({ page: recentPage, page_size: PAGE_SIZE })
      .then((res) => {
        setRecentCases(res.data.items || []);
        setRecentTotalPages(res.data.total_pages || 1);
      })
      .catch(() => {});
  }, [recentPage]);

  // My Assigned Cases (paginated)
  useEffect(() => {
    if (!user?.id) return;
    getCases({ page: assignedPage, page_size: PAGE_SIZE, assignee_id: user.id })
      .then((res) => {
        setAssignedCases(res.data.items || []);
        setAssignedTotalPages(res.data.total_pages || 1);
      })
      .catch(() => {});
  }, [assignedPage, user?.id]);

  // My Created Cases (paginated)
  useEffect(() => {
    if (!user?.name) return;
    getCases({ page: createdPage, page_size: PAGE_SIZE, requester: user.name })
      .then((res) => {
        setCreatedCases(res.data.items || []);
        setCreatedTotalPages(res.data.total_pages || 1);
      })
      .catch(() => {});
  }, [createdPage, user?.name]);

  if (loading) return <Spinner />;

  const countByStatus = (status) => {
    const found = statusStats.find((s) => s.status === status);
    return found ? found.count : 0;
  };
  const totalCases = statusStats.reduce((sum, s) => sum + s.count, 0);
  const avgHours = timeStats?.avg_hours;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      {/* Status Summary Cards - Clickable */}
      <div className="card-grid">
        <div className="stat-card accent-blue clickable" onClick={() => navigate('/cases')}>
          <span className="stat-label">Total Cases</span>
          <span className="stat-value">{totalCases}</span>
        </div>
        <div className="stat-card accent-yellow clickable" onClick={() => navigate('/cases?status=OPEN')}>
          <span className="stat-label">Open</span>
          <span className="stat-value">{countByStatus('OPEN')}</span>
        </div>
        <div className="stat-card accent-orange clickable" onClick={() => navigate('/cases?status=IN_PROGRESS')}>
          <span className="stat-label">In Progress</span>
          <span className="stat-value">{countByStatus('IN_PROGRESS')}</span>
        </div>
        <div className="stat-card accent-green clickable" onClick={() => navigate('/cases?status=DONE')}>
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

      {/* Assignee Statistics (ADMIN only) */}
      {user?.role === ROLES.ADMIN && assigneeStats.length > 0 && (
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

      {/* My Assigned Cases */}
      <div className="section">
        <div className="section-title">My Assigned Cases</div>
        <CaseList cases={assignedCases} />
        <Pagination
          page={assignedPage}
          totalPages={assignedTotalPages}
          onPageChange={setAssignedPage}
        />
      </div>

      {/* My Created Cases */}
      <div className="section">
        <div className="section-title">My Created Cases</div>
        <CaseList cases={createdCases} />
        <Pagination
          page={createdPage}
          totalPages={createdTotalPages}
          onPageChange={setCreatedPage}
        />
      </div>

      {/* Recent Cases */}
      <div className="section">
        <div className="section-title">Recent Cases</div>
        <CaseList cases={recentCases} />
        <Pagination
          page={recentPage}
          totalPages={recentTotalPages}
          onPageChange={setRecentPage}
        />
      </div>
    </div>
  );
}
