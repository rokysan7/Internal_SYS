import { useState } from 'react';
import { ROLES } from '../../constants/roles';
import { formatDate } from '../utils';

/**
 * Single comment with nested replies support.
 */
function CommentItem({ comment, depth = 0, onReply, onDelete, currentUser }) {
  const [showReplyInput, setShowReplyInput] = useState(false);
  const [replyText, setReplyText] = useState('');

  const handleReply = () => {
    if (!replyText.trim()) return;
    onReply(comment.id, replyText);
    setReplyText('');
    setShowReplyInput(false);
  };

  const handleDelete = () => {
    if (!window.confirm('Delete this comment?')) return;
    onDelete(comment.id);
  };

  const authorName = comment.author?.name || `User #${comment.author_id}`;
  const canDelete = currentUser && (
    currentUser.id === comment.author_id || currentUser.role === ROLES.ADMIN
  );

  return (
    <div style={{ marginLeft: depth > 0 ? depth * 24 : 0 }}>
      <div className="memo-item" style={{
        borderLeft: depth > 0 ? '2px solid #e2e8f0' : 'none',
        paddingLeft: depth > 0 ? 12 : 0,
        marginBottom: 8,
      }}>
        <div className="memo-meta">
          <strong>{authorName}</strong> &middot; {formatDate(comment.created_at)}
          {comment.is_internal && (
            <span className="badge badge-low" style={{ marginLeft: 6 }}>Internal</span>
          )}
        </div>
        <div className="memo-content">{comment.content}</div>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: 4 }}>
          <button
            className="btn btn-ghost btn-sm"
            style={{ padding: '2px 8px', fontSize: '0.75rem' }}
            onClick={() => setShowReplyInput(!showReplyInput)}
          >
            {showReplyInput ? 'Cancel' : 'Reply'}
          </button>
          {canDelete && (
            <button
              className="btn btn-ghost btn-sm"
              style={{ padding: '2px 8px', fontSize: '0.75rem', color: '#dc2626' }}
              onClick={handleDelete}
            >
              Delete
            </button>
          )}
        </div>

        {showReplyInput && (
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: 8 }}>
            <input
              type="text"
              placeholder="Write a reply..."
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.nativeEvent.isComposing && handleReply()}
              style={{
                flex: 1, padding: '0.4rem 0.6rem', border: '1px solid #cbd5e1',
                borderRadius: 4, fontSize: '0.8rem', fontFamily: 'inherit',
              }}
              autoFocus
            />
            <button className="btn btn-primary btn-sm" onClick={handleReply}>Send</button>
          </div>
        )}
      </div>

      {/* Nested replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div>
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              depth={depth + 1}
              onReply={onReply}
              onDelete={onDelete}
              currentUser={currentUser}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Comments list with input form and nested replies.
 * @param {Object} props
 * @param {Array} props.comments - List of comment objects (tree structure)
 * @param {string} props.value - Current input value
 * @param {Function} props.onChange - Input change handler
 * @param {Function} props.onAdd - Add comment handler (content, parentId?)
 * @param {Function} props.onDelete - Delete comment handler (commentId)
 * @param {Object} props.currentUser - Current logged-in user
 */
export default function CommentsCard({ comments, value, onChange, onAdd, onDelete, currentUser }) {
  const handleAddComment = () => {
    if (!value.trim()) return;
    onAdd(value, null);
  };

  const handleReply = (parentId, content) => {
    onAdd(content, parentId);
  };

  // Count total comments including replies
  const countComments = (items) => {
    return items.reduce((sum, c) => {
      return sum + 1 + (c.replies ? countComments(c.replies) : 0);
    }, 0);
  };
  const totalCount = countComments(comments);

  return (
    <div className="card">
      <div className="section-title">Comments ({totalCount})</div>
      {comments.length === 0 ? (
        <div className="empty-state">No comments yet.</div>
      ) : (
        comments.map((cm) => (
          <CommentItem
            key={cm.id}
            comment={cm}
            onReply={handleReply}
            onDelete={onDelete}
            currentUser={currentUser}
          />
        ))
      )}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <input
          type="text"
          placeholder="Add a comment..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.nativeEvent.isComposing && handleAddComment()}
          style={{
            flex: 1, padding: '0.5rem 0.75rem', border: '1px solid #cbd5e1',
            borderRadius: 6, fontSize: '0.85rem', fontFamily: 'inherit',
          }}
        />
        <button className="btn btn-primary btn-sm" onClick={handleAddComment}>Send</button>
      </div>
    </div>
  );
}
