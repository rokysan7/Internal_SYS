import { formatDate } from '../utils';

/**
 * Comments list with input form.
 * @param {Object} props
 * @param {Array} props.comments - List of comment objects
 * @param {string} props.value - Current input value
 * @param {Function} props.onChange - Input change handler
 * @param {Function} props.onAdd - Add comment handler
 */
export default function CommentsCard({ comments, value, onChange, onAdd }) {
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
