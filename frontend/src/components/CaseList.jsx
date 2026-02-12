import { memo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { formatDate, statusBadgeClass, statusLabel, priorityBadgeClass } from './utils';

/**
 * CS Case 목록 테이블.
 * @param {Object[]} cases - 케이스 배열
 * @param {boolean}  [clickable=true] - 행 클릭 시 상세 이동 여부
 */
export default memo(function CaseList({ cases, clickable = true }) {
  const navigate = useNavigate();

  if (!cases || cases.length === 0) {
    return <div className="empty-state">No cases found.</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Requester</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr
              key={c.id}
              className={clickable ? 'clickable-row' : ''}
              onClick={clickable ? () => navigate(`/cases/${c.id}`) : undefined}
            >
              <td>
                <Link to={`/cases/${c.id}`}>#{c.id}</Link>
              </td>
              <td>
                <Link to={`/cases/${c.id}`}>{c.title}</Link>
              </td>
              <td>
                <span className={`badge ${statusBadgeClass(c.status)}`}>
                  {statusLabel(c.status)}
                </span>
              </td>
              <td>
                <span className={`badge ${priorityBadgeClass(c.priority)}`}>
                  {c.priority}
                </span>
              </td>
              <td>{c.requester}</td>
              <td>{formatDate(c.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
});
