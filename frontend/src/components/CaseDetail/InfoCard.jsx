import { Link } from 'react-router-dom';
import { formatDate, priorityBadgeClass } from '../utils';

/**
 * Case information sidebar card.
 * @param {Object} props
 * @param {Object} props.caseData - Case data object
 * @param {Function} props.onStatusChange - Status change handler
 */
export default function InfoCard({ caseData, onStatusChange }) {
  return (
    <div className="card">
      <div className="section-title">Details</div>
      <div className="detail-field">
        <span className="detail-label">Status</span>
        <select
          value={caseData.status}
          onChange={(e) => onStatusChange(e.target.value)}
          style={{
            padding: '0.35rem 0.5rem', border: '1px solid #cbd5e1',
            borderRadius: 4, fontSize: '0.85rem', fontFamily: 'inherit',
          }}
        >
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="DONE">Done</option>
          <option value="CANCEL">Cancel</option>
        </select>
      </div>
      <div className="detail-field">
        <span className="detail-label">Priority</span>
        <span className={`badge ${priorityBadgeClass(caseData.priority)}`}>
          {caseData.priority}
        </span>
      </div>
      <div className="detail-field">
        <span className="detail-label">Requester</span>
        <span className="detail-value">{caseData.requester}</span>
      </div>
      <div className="detail-field">
        <span className="detail-label">Assignees</span>
        <span className="detail-value">
          {caseData.assignee_names?.length > 0
            ? caseData.assignee_names.join(', ')
            : 'Unassigned'}
        </span>
      </div>
      <div className="detail-field">
        <span className="detail-label">Product</span>
        <span className="detail-value">
          {caseData.product_id ? <Link to="/products">#{caseData.product_id}</Link> : '-'}
        </span>
      </div>
      <div className="detail-field">
        <span className="detail-label">License</span>
        <span className="detail-value">
          {caseData.license_id ? (
            <Link to="/products">#{caseData.license_id}</Link>
          ) : '-'}
        </span>
      </div>
      {caseData.organization && (
        <div className="detail-field">
          <span className="detail-label">Organization</span>
          <span className="detail-value">{caseData.organization}</span>
        </div>
      )}
      {caseData.org_phone && (
        <div className="detail-field">
          <span className="detail-label">Org Phone</span>
          <span className="detail-value">{caseData.org_phone}</span>
        </div>
      )}
      {caseData.org_contact && (
        <div className="detail-field">
          <span className="detail-label">Org Contact</span>
          <span className="detail-value">{caseData.org_contact}</span>
        </div>
      )}
      <div className="detail-field">
        <span className="detail-label">Created</span>
        <span className="detail-value">{formatDate(caseData.created_at)}</span>
      </div>
      {caseData.status === 'DONE' && caseData.completed_at && (
        <div className="detail-field">
          <span className="detail-label">Completed</span>
          <span className="detail-value">{formatDate(caseData.completed_at)}</span>
        </div>
      )}
      {caseData.status === 'CANCEL' && caseData.canceled_at && (
        <div className="detail-field">
          <span className="detail-label">Canceled</span>
          <span className="detail-value">{formatDate(caseData.canceled_at)}</span>
        </div>
      )}
      {caseData.tags?.length > 0 && (
        <div className="detail-field">
          <span className="detail-label">Tags</span>
          <div className="tag-list">
            {caseData.tags.map((t) => <span key={t} className="tag">{t}</span>)}
          </div>
        </div>
      )}
    </div>
  );
}
