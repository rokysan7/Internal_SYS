import { memo, useEffect, useState } from 'react';
import { getSimilarCasesById } from '../../api/cases';

/**
 * Panel showing similar cases for a given case ID.
 * Loads independently — errors don't affect the parent detail page.
 * @param {Object} props
 * @param {number|string} props.caseId - Case ID to find similar cases for
 */
function SimilarCasesPanel({ caseId }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSimilarCasesById(caseId)
      .then((res) => setCases(res.data))
      .catch(() => setCases([]))
      .finally(() => setLoading(false));
  }, [caseId]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric', month: '2-digit', day: '2-digit',
    });
  };

  const statusConfig = {
    DONE: { label: '해결됨', className: 'status-resolved' },
    IN_PROGRESS: { label: '진행중', className: 'status-progress' },
    OPEN: { label: '미처리', className: 'status-open' },
  };

  const scoreBadgeClass = (score) => {
    const pct = Math.round(score * 100);
    if (pct >= 80) return 'badge-score-high';
    if (pct >= 60) return 'badge-score-mid';
    return 'badge-score-low';
  };

  if (loading) return null;
  if (cases.length === 0) return null;

  return (
    <div className="card similar-panel">
      <div className="card-header">
        <h3>Similar Cases ({cases.length})</h3>
      </div>
      <div className="similar-panel-list">
        {cases.map((sc) => {
          const status = statusConfig[sc.status] || { label: sc.status, className: '' };
          const pct = Math.round((sc.similarity_score || 0) * 100);
          return (
            <a
              key={sc.id}
              href={`/cases/${sc.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="similar-panel-item"
            >
              <div className="similar-panel-top">
                <span className="similar-case-id">#{sc.id}</span>
                <span className="similar-case-title">{sc.title}</span>
                <span className={`badge-score ${scoreBadgeClass(sc.similarity_score)}`}>
                  {pct}%
                </span>
              </div>
              <div className="similar-case-meta">
                {sc.matched_tags && sc.matched_tags.length > 0 && (
                  <span className="similar-case-tags">
                    {sc.matched_tags.map((tag) => (
                      <span key={tag} className="similar-case-tag">#{tag}</span>
                    ))}
                  </span>
                )}
                <span className={`similar-case-status ${status.className}`}>
                  {status.label}
                  {sc.status === 'DONE' && sc.resolved_at && ` (${formatDate(sc.resolved_at)})`}
                </span>
                {sc.comment_count > 0 && (
                  <span className="similar-case-comments">💬 {sc.comment_count}</span>
                )}
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

export default memo(SimilarCasesPanel);
