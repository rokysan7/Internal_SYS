import { useState } from 'react';
import { createProductMemo, createLicenseMemo } from '../api/memos';
import { formatDate } from './utils';

/**
 * 범용 메모 목록 + 작성 폼.
 * @param {string} title - 섹션 제목
 * @param {Object[]} memos - 메모 배열
 * @param {'product'|'license'} entityType - 메모 대상 엔티티 타입
 * @param {number} entityId - 엔티티 ID
 * @param {function} onMemoAdded - 메모 추가 성공 콜백 (newMemo)
 */
export default function MemoList({ title, memos, entityType, entityId, onMemoAdded }) {
  const [newMemo, setNewMemo] = useState('');
  const [submitting, setSubmitting] = useState(false);

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
            <div className="memo-meta">
              Author #{m.author_id} &middot; {formatDate(m.created_at)}
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
}
