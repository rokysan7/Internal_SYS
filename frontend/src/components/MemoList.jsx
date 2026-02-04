import { memo, useState } from 'react';
import {
  createProductMemo,
  createLicenseMemo,
  deleteProductMemo,
  deleteLicenseMemo,
} from '../api/memos';
import { ROLES } from '../constants/roles';
import { formatDate } from './utils';

/**
 * 범용 메모 목록 + 작성 폼.
 * @param {string} title - 섹션 제목
 * @param {Object[]} memos - 메모 배열
 * @param {'product'|'license'} entityType - 메모 대상 엔티티 타입
 * @param {number} entityId - 엔티티 ID
 * @param {Object} currentUser - 현재 로그인 사용자 { id, role }
 * @param {function} onMemoAdded - 메모 추가 성공 콜백 (newMemo)
 * @param {function} onMemoDeleted - 메모 삭제 성공 콜백 (memoId)
 */
export default memo(function MemoList({
  title,
  memos,
  entityType,
  entityId,
  currentUser,
  onMemoAdded,
  onMemoDeleted,
}) {
  const [newMemo, setNewMemo] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const handleAdd = async () => {
    if (!newMemo.trim() || submitting) return;
    setSubmitting(true);
    try {
      const createFn = entityType === 'product' ? createProductMemo : createLicenseMemo;
      const res = await createFn(entityId, { content: newMemo });
      onMemoAdded?.(res.data);
      setNewMemo('');
    } catch (err) {
      console.error('Memo creation failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (memoId) => {
    if (!window.confirm('Delete this memo?')) return;
    setDeletingId(memoId);
    try {
      const deleteFn = entityType === 'product' ? deleteProductMemo : deleteLicenseMemo;
      await deleteFn(memoId);
      onMemoDeleted?.(memoId);
    } catch (err) {
      console.error('Memo deletion failed:', err);
      alert('Failed to delete memo');
    } finally {
      setDeletingId(null);
    }
  };

  const canDelete = (memo) => {
    if (!currentUser) return false;
    return memo.author_id === currentUser.id || currentUser.role === ROLES.ADMIN;
  };

  return (
    <div className="card">
      <div className="section-title">{title} ({memos.length})</div>

      {memos.length === 0 ? (
        <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
          No memos yet. Add one below.
        </div>
      ) : (
        memos.map((m) => (
          <div key={m.id} className="memo-item">
            <div
              className="memo-meta"
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <span>
                {m.author_name || 'Unknown'} &middot; {formatDate(m.created_at)}
              </span>
              {canDelete(m) && (
                <button
                  onClick={() => handleDelete(m.id)}
                  disabled={deletingId === m.id}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#ef4444',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    padding: '2px 6px',
                  }}
                >
                  {deletingId === m.id ? '...' : 'Delete'}
                </button>
              )}
            </div>
            <div className="memo-content">{m.content}</div>
          </div>
        ))
      )}

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
        <input
          type="text"
          placeholder="Add a memo..."
          value={newMemo}
          onChange={(e) => setNewMemo(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          style={{
            flex: 1, padding: '0.5rem 0.75rem', border: '1px solid #cbd5e1',
            borderRadius: 6, fontSize: '0.85rem', fontFamily: 'inherit',
          }}
        />
        <button
          className="btn btn-primary btn-sm"
          onClick={handleAdd}
          disabled={submitting}
        >
          {submitting ? '...' : 'Add'}
        </button>
      </div>
    </div>
  );
});
