import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getSimilarCases } from '../api/cases';
import useDebounce from '../hooks/useDebounce';

/**
 * Shows similar cases based on title input (debounced).
 * @param {Object} props
 * @param {string} props.title - Current case title input
 */
export default function SimilarCasesWidget({ title }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const debouncedTitle = useDebounce(title, 500);

  useEffect(() => {
    if (debouncedTitle.trim().length <= 3) {
      setCases([]);
      return;
    }
    setLoading(true);
    getSimilarCases(debouncedTitle.trim())
      .then((res) => setCases(res.data))
      .catch(() => setCases([]))
      .finally(() => setLoading(false));
  }, [debouncedTitle]);

  const statusLabel = (status) => {
    switch (status) {
      case 'OPEN': return 'Open';
      case 'IN_PROGRESS': return 'In Progress';
      case 'DONE': return 'Done';
      default: return status;
    }
  };

  if (!loading && cases.length === 0) return null;

  return (
    <div className="similar-cases">
      <div className="similar-cases-header">
        {loading ? 'Searching...' : `${cases.length} similar cases`}
      </div>
      {cases.map((sc) => (
        <Link key={sc.id} to={`/cases/${sc.id}`} className="similar-case-item">
          <span className="similar-case-id">#{sc.id}</span>
          <span className="similar-case-title">{sc.title}</span>
          <span className={`badge badge-${sc.status.toLowerCase().replace('_', '-')}`}>
            {statusLabel(sc.status)}
          </span>
        </Link>
      ))}
    </div>
  );
}
