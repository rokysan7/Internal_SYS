import { formatDate } from '../../components/utils';

export default function InfoCard({ data, onStatusChange }) {
  return (
    <div className="card">
      <div className="section-title">Details</div>

      <div className="detail-field">
        <span className="detail-label">Status</span>
        <select
          value={data.status}
          onChange={(e) => onStatusChange(e.target.value)}
          style={{
            padding: '0.35rem 0.5rem', border: '1px solid #cbd5e1',
            borderRadius: 4, fontSize: '0.85rem', fontFamily: 'inherit',
          }}
        >
          <option value="OPEN">Open</option>
          <option value="DONE">Done</option>
        </select>
      </div>

      <div className="detail-field">
        <span className="detail-label">Assignees</span>
        <span className="detail-value">
          {data.assignee_names?.length > 0 ? data.assignee_names.join(', ') : 'Unassigned'}
        </span>
      </div>

      <div className="detail-field">
        <span className="detail-label">Delivery Date</span>
        <span className="detail-value">{data.delivery_date || '-'}</span>
      </div>

      <div className="detail-field">
        <span className="detail-label">Email</span>
        <span className="detail-value">{data.email || '-'}</span>
      </div>

      <div className="detail-field">
        <span className="detail-label">Organization</span>
        <span className="detail-value">{data.organization || '-'}</span>
      </div>

      {data.other_request && (
        <div className="detail-field">
          <span className="detail-label">Other Request</span>
          <span className="detail-value" style={{ whiteSpace: 'pre-wrap' }}>{data.other_request}</span>
        </div>
      )}

      <div className="detail-field">
        <span className="detail-label">Received</span>
        <span className="detail-value">{formatDate(data.received_at)}</span>
      </div>

      <div className="detail-field">
        <span className="detail-label">Created</span>
        <span className="detail-value">{formatDate(data.created_at)}</span>
      </div>

      {data.status === 'DONE' && data.completed_at && (
        <div className="detail-field">
          <span className="detail-label">Completed</span>
          <span className="detail-value">{formatDate(data.completed_at)}</span>
        </div>
      )}
    </div>
  );
}
