import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getCase,
  updateCaseStatus,
  getComments,
  createComment,
  getChecklists,
  createChecklist,
  updateChecklist,
} from '../api/cases';
import {
  formatDate,
  statusBadgeClass,
  statusLabel,
  priorityBadgeClass,
} from './utils';

/**
 * CS Case 상세 뷰 (댓글 + 체크리스트 포함).
 * @param {string|number} caseId
 */
export default function CaseDetail({ caseId }) {
  const [caseData, setCaseData] = useState(null);
  const [comments, setComments] = useState([]);
  const [checklists, setChecklists] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [newCheckItem, setNewCheckItem] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAll() {
      try {
        const [caseRes, commentsRes, checkRes] = await Promise.all([
          getCase(caseId),
          getComments(caseId),
          getChecklists(caseId),
        ]);
        setCaseData(caseRes.data);
        setComments(commentsRes.data);
        setChecklists(checkRes.data);
      } catch (err) {
        console.error('Failed to load case:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, [caseId]);

  const handleStatusChange = async (newStatus) => {
    try {
      await updateCaseStatus(caseId, newStatus);
      setCaseData((prev) => ({ ...prev, status: newStatus }));
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    try {
      const res = await createComment(caseId, { content: newComment, is_internal: false });
      setComments((prev) => [...prev, res.data]);
      setNewComment('');
    } catch (err) {
      console.error('Comment creation failed:', err);
    }
  };

  const handleAddCheckItem = async () => {
    if (!newCheckItem.trim()) return;
    try {
      const res = await createChecklist(caseId, { content: newCheckItem });
      setChecklists((prev) => [...prev, res.data]);
      setNewCheckItem('');
    } catch (err) {
      console.error('Checklist creation failed:', err);
    }
  };

  const handleToggleCheck = async (item) => {
    try {
      await updateChecklist(item.id, !item.is_done);
      setChecklists((prev) =>
        prev.map((c) => (c.id === item.id ? { ...c, is_done: !c.is_done } : c)),
      );
    } catch (err) {
      console.error('Checklist toggle failed:', err);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!caseData) return <div className="empty-state">Case not found.</div>;

  return (
    <div>
      <Link to="/cases" className="back-link">← Back to Cases</Link>

      <div className="page-header">
        <h1>{caseData.title}</h1>
        <span className={`badge ${statusBadgeClass(caseData.status)}`}>
          {statusLabel(caseData.status)}
        </span>
      </div>

      <div className="detail-grid">
        {/* Main Column */}
        <div className="detail-main">
          <DescriptionCard content={caseData.content} />
          <CommentsCard
            comments={comments}
            value={newComment}
            onChange={setNewComment}
            onAdd={handleAddComment}
          />
        </div>

        {/* Side Column */}
        <div className="detail-side">
          <InfoCard caseData={caseData} onStatusChange={handleStatusChange} />
          <ChecklistCard
            checklists={checklists}
            value={newCheckItem}
            onChange={setNewCheckItem}
            onAdd={handleAddCheckItem}
            onToggle={handleToggleCheck}
          />
        </div>
      </div>
    </div>
  );
}

/* ---- Sub-components ---- */

function DescriptionCard({ content }) {
  return (
    <div className="card">
      <div className="section-title">Description</div>
      <p style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.6 }}>{content}</p>
    </div>
  );
}

function CommentsCard({ comments, value, onChange, onAdd }) {
  return (
    <div className="card">
      <div className="section-title">Comments ({comments.length})</div>
      {comments.length === 0 ? (
        <div className="empty-state">No comments yet.</div>
      ) : (
        comments.map((cm) => (
          <div key={cm.id} className="memo-item">
            <div className="memo-meta">
              #{cm.author_id} &middot; {formatDate(cm.created_at)}
              {cm.is_internal && (
                <span className="badge badge-low" style={{ marginLeft: 6 }}>Internal</span>
              )}
            </div>
            <div className="memo-content">{cm.content}</div>
          </div>
        ))
      )}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <input
          type="text"
          placeholder="Add a comment..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onAdd()}
          style={{
            flex: 1, padding: '0.5rem 0.75rem', border: '1px solid #cbd5e1',
            borderRadius: 6, fontSize: '0.85rem', fontFamily: 'inherit',
          }}
        />
        <button className="btn btn-primary btn-sm" onClick={onAdd}>Send</button>
      </div>
    </div>
  );
}

function InfoCard({ caseData, onStatusChange }) {
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
        <span className="detail-label">Assignee</span>
        <span className="detail-value">{caseData.assignee_id ?? 'Unassigned'}</span>
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
            <Link to={`/licenses/${caseData.license_id}`}>#{caseData.license_id}</Link>
          ) : '-'}
        </span>
      </div>
      <div className="detail-field">
        <span className="detail-label">Created</span>
        <span className="detail-value">{formatDate(caseData.created_at)}</span>
      </div>
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

function ChecklistCard({ checklists, value, onChange, onAdd, onToggle }) {
  return (
    <div className="card">
      <div className="section-title">Checklist</div>
      {checklists.length === 0 && (
        <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
          No items yet.
        </div>
      )}
      {checklists.map((item) => (
        <label
          key={item.id}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.35rem 0', fontSize: '0.85rem', cursor: 'pointer',
            color: item.is_done ? '#94a3b8' : '#334155',
            textDecoration: item.is_done ? 'line-through' : 'none',
          }}
        >
          <input
            type="checkbox"
            checked={item.is_done}
            onChange={() => onToggle(item)}
          />
          {item.content}
        </label>
      ))}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <input
          type="text"
          placeholder="Add checklist item..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onAdd()}
          style={{
            flex: 1, padding: '0.4rem 0.6rem', border: '1px solid #cbd5e1',
            borderRadius: 4, fontSize: '0.82rem', fontFamily: 'inherit',
          }}
        />
        <button className="btn btn-secondary btn-sm" onClick={onAdd}>+</button>
      </div>
    </div>
  );
}
