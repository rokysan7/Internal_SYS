import { memo, useEffect, useState } from 'react';
import { getCases } from '../../api/cases';
import CaseList from '../../components/CaseList';
import Pagination from '../../components/Pagination';

const PAGE_SIZE = 5;

/**
 * Paginated case list section.
 * @param {string} title - Section title
 * @param {Object} params - getCases query params (excluding page/page_size)
 */
function CaseSection({ title, params = {} }) {
  const [cases, setCases] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    getCases({ page, page_size: PAGE_SIZE, ...params })
      .then((res) => {
        setCases(res.data.items || []);
        setTotalPages(res.data.total_pages || 1);
      })
      .catch(() => {});
  }, [page, JSON.stringify(params)]);

  return (
    <div className="section">
      <div className="section-title">{title}</div>
      <CaseList cases={cases} />
      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}

export default memo(CaseSection);
