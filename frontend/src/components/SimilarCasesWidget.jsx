import { memo, useEffect, useState } from 'react';
import { getSimilarCases } from '../api/cases';
import useDebounce from '../hooks/useDebounce';

/**
 * Shows similar cases based on title, content, and tags (debounced).
 * Displays similarity score, matched tags, comment count, and resolution status.
 * @param {Object} props
 * @param {string} props.title - Current case title input
 * @param {string} props.content - Current case content input
 * @param {string[]} props.tags - Current case tags
 */
function SimilarCasesWidget({ title = '', content = '', tags = [] }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const debouncedTitle = useDebounce(title, 500);
  const debouncedContent = useDebounce(content, 500);
  const debouncedTags = useDebounce(tags, 500);

  useEffect(() => {
    const trimmedTitle = debouncedTitle.trim();
    const trimmedContent = debouncedContent.trim();

    if (trimmedTitle.length < 3 && !trimmedContent) {
      setCases([]);
      return;
    }
    setLoading(true);
    getSimilarCases({ title: trimmedTitle, content: trimmedContent, tags: debouncedTags })
      .then((res) => setCases(res.data))
      .catch(() => setCases([]))
      .finally(() => setLoading(false));
  }, [debouncedTitle, debouncedContent, debouncedTags]);

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

  if (!loading && cases.length === 0) return null;

  return (
    <div className="similar-cases">
      <div className="similar-cases-header">
        {loading ? 'Searching...' : `${cases.length} similar cases`}
      </div>
      {cases.map((sc) => {
        const status = statusConfig[sc.status] || { label: sc.status, className: '' };
        const pct = Math.round((sc.similarity_score || 0) * 100);
        return (
          <a
            key={sc.id}
            href={`/cases/${sc.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="similar-case-item"
          >
            <div className="similar-case-main">
              <div className="similar-case-top">
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
                  <span className="similar-case-comments">
                    💬 {sc.comment_count}
                  </span>
                )}
              </div>
            </div>
          </a>
        );
      })}
    </div>
  );
}

export default memo(SimilarCasesWidget);
