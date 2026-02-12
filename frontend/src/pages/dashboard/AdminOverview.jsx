import { memo, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAssignees, getStatistics } from '../../api/cases';
import { CASE_STATUS } from '../../constants/caseStatus';

const PERIOD_OPTIONS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Admin Overview: status cards + assignee stats table.
 * Open/In Progress = all-time, Done/Cancel = period-filtered.
 */
function AdminOverview() {
  const navigate = useNavigate();
  const [statPeriod, setStatPeriod] = useState('daily');
  const [statDate, setStatDate] = useState(todayStr());
  const [statAssigneeId, setStatAssigneeId] = useState('');
  const [assigneeList, setAssigneeList] = useState([]);
  const [statusStatsAll, setStatusStatsAll] = useState([]);
  const [statusStatsPeriod, setStatusStatsPeriod] = useState([]);
  const [assigneeStats, setAssigneeStats] = useState([]);

  // Load assignee list (once)
  useEffect(() => {
    getAssignees()
      .then((res) => setAssigneeList(res.data))
      .catch(() => {});
  }, []);

  // All-time stats (Open/In Progress)
  useEffect(() => {
    const aid = statAssigneeId ? Number(statAssigneeId) : undefined;
    getStatistics('status', { assigneeId: aid })
      .then((res) => setStatusStatsAll(res.data))
      .catch(() => {});
  }, [statAssigneeId]);

  // Period-filtered stats (Done/Cancel + assignee table)
  useEffect(() => {
    const aid = statAssigneeId ? Number(statAssigneeId) : undefined;
    const opts = { period: statPeriod, targetDate: statDate, assigneeId: aid };
    Promise.all([
      getStatistics('status', opts),
      getStatistics('assignee', { period: statPeriod, targetDate: statDate }),
    ])
      .then(([statusRes, assigneeRes]) => {
        setStatusStatsPeriod(statusRes.data);
        setAssigneeStats(assigneeRes.data);
      })
      .catch(() => {});
  }, [statPeriod, statDate, statAssigneeId]);

  const countAll = (status) => {
    const found = statusStatsAll.find((s) => s.status === status);
    return found ? found.count : 0;
  };
  const countPeriod = (status) => {
    const found = statusStatsPeriod.find((s) => s.status === status);
    return found ? found.count : 0;
  };
  const totalCases = statusStatsAll.reduce((sum, s) => sum + s.count, 0);

  return (
    <>
      <div className="section">
        <div className="section-header-row">
          <div className="section-title">Overview</div>
          <div className="period-controls">
            <select
              className="period-select"
              value={statAssigneeId}
              onChange={(e) => setStatAssigneeId(e.target.value)}
            >
              <option value="">All Members</option>
              {assigneeList.map((u) => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
            <div className="period-toggle">
              {PERIOD_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  className={`period-btn${statPeriod === opt.value ? ' active' : ''}`}
                  onClick={() => setStatPeriod(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <input
              type="date"
              className="period-date"
              value={statDate}
              onChange={(e) => setStatDate(e.target.value)}
            />
          </div>
        </div>
        <div className="card-grid">
          <div className="stat-card accent-blue clickable" onClick={() => navigate('/cases')}>
            <span className="stat-label">Total</span>
            <span className="stat-value">{totalCases}</span>
          </div>
          <div className="stat-card accent-yellow clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.OPEN}`)}>
            <span className="stat-label">Open</span>
            <span className="stat-value">{countAll(CASE_STATUS.OPEN)}</span>
          </div>
          <div className="stat-card accent-orange clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.IN_PROGRESS}`)}>
            <span className="stat-label">In Progress</span>
            <span className="stat-value">{countAll(CASE_STATUS.IN_PROGRESS)}</span>
          </div>
          <div className="stat-card accent-green clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.DONE}`)}>
            <span className="stat-label">Done</span>
            <span className="stat-value">{countPeriod(CASE_STATUS.DONE)}</span>
          </div>
          <div className="stat-card accent-red clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.CANCEL}`)}>
            <span className="stat-label">Cancel</span>
            <span className="stat-value">{countPeriod(CASE_STATUS.CANCEL)}</span>
          </div>
        </div>
      </div>

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
                  <th style={{ textAlign: 'center' }}>Cancel</th>
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
                    <td className="count-cell count-cancel">{a.cancel_count}</td>
                    <td className="count-cell">
                      {a.open_count + a.in_progress_count + a.done_count + (a.cancel_count || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

export default memo(AdminOverview);
