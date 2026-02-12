import { memo, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyProgress } from '../../api/cases';
import { CASE_STATUS } from '../../constants/caseStatus';

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * My Progress: current user's case counts.
 * Open/In Progress = all-time, Done/Cancel = date-filtered.
 */
function MyProgress() {
  const navigate = useNavigate();
  const [progressDate, setProgressDate] = useState(todayStr());
  const [progressAll, setProgressAll] = useState(null);
  const [progressDaily, setProgressDaily] = useState(null);

  // All-time (once)
  useEffect(() => {
    getMyProgress()
      .then((res) => setProgressAll(res.data))
      .catch(() => {});
  }, []);

  // Date-filtered
  useEffect(() => {
    getMyProgress(progressDate)
      .then((res) => setProgressDaily(res.data))
      .catch(() => {});
  }, [progressDate]);

  if (!progressAll) return null;

  return (
    <div className="section">
      <div className="section-header-row">
        <div className="section-title">My Progress</div>
        <div className="period-controls">
          <input
            type="date"
            className="period-date"
            value={progressDate}
            onChange={(e) => setProgressDate(e.target.value)}
          />
        </div>
      </div>
      <div className="card-grid">
        <div className="stat-card accent-yellow clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.OPEN}`)}>
          <span className="stat-label">Open</span>
          <span className="stat-value">{progressAll.open_count}</span>
        </div>
        <div className="stat-card accent-orange clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.IN_PROGRESS}`)}>
          <span className="stat-label">In Progress</span>
          <span className="stat-value">{progressAll.in_progress_count}</span>
        </div>
        <div className="stat-card accent-green clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.DONE}`)}>
          <span className="stat-label">Done</span>
          <span className="stat-value">{progressDaily?.done_count ?? 0}</span>
        </div>
        <div className="stat-card accent-red clickable" onClick={() => navigate(`/cases?status=${CASE_STATUS.CANCEL}`)}>
          <span className="stat-label">Cancel</span>
          <span className="stat-value">{progressDaily?.cancel_count ?? 0}</span>
        </div>
      </div>
    </div>
  );
}

export default memo(MyProgress);
