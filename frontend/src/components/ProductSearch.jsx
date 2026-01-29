import { useEffect, useState } from 'react';
import { getProducts } from '../api/products';
import Pagination from './Pagination';
import SortButtons from './SortButtons';
import usePagination from '../hooks/usePagination';

const SORT_OPTIONS = [
  { key: 'name', label: '이름' },
  { key: 'created_at', label: '날짜' },
];

const PAGE_SIZE = 25;

/**
 * Product 검색 + 선택 리스트 (페이지네이션 & 정렬 지원).
 * @param {function} onSelect - 선택 콜백 (product object)
 * @param {number|null} selectedId - 현재 선택된 product id
 * @param {number} refreshKey - 변경 시 목록 재조회 트리거
 */
export default function ProductSearch({ onSelect, selectedId, refreshKey = 0 }) {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // 페이지네이션 상태 (커스텀 훅 사용)
  const { page, totalPages, total, setPage, updateFromResponse, resetPage } = usePagination();

  // 정렬 상태
  const [sort, setSort] = useState('name');
  const [order, setOrder] = useState('asc');

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      getProducts({ search: search || undefined, page, pageSize: PAGE_SIZE, sort, order })
        .then((res) => {
          setProducts(res.data.items);
          updateFromResponse(res.data);
        })
        .catch((err) => console.error('Product fetch failed:', err))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [search, page, sort, order, refreshKey, updateFromResponse]);

  // 검색어/정렬 변경 시 페이지 초기화
  useEffect(() => {
    resetPage();
  }, [search, sort, order, resetPage]);

  const handleSortChange = (newSort, newOrder) => {
    setSort(newSort);
    setOrder(newOrder);
  };

  return (
    <div>
      {/* 검색창 */}
      <div className="search-box">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* 정렬 & 총 개수 */}
      <div className="list-header">
        <span className="total-count">Total: {total}</span>
        <SortButtons
          options={SORT_OPTIONS}
          currentSort={sort}
          currentOrder={order}
          onSortChange={handleSortChange}
        />
      </div>

      {/* 제품 리스트 */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div className="loading">Loading...</div>
        ) : products.length === 0 ? (
          <div className="empty-state">No products found.</div>
        ) : (
          products.map((p) => (
            <div
              key={p.id}
              className="list-item"
              onClick={() => onSelect(p)}
              style={{
                background: selectedId === p.id ? '#f0f9ff' : 'transparent',
                borderLeft: selectedId === p.id
                  ? '3px solid #38bdf8'
                  : '3px solid transparent',
              }}
            >
              <div>
                <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{p.name}</div>
                {p.description && (
                  <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 2 }}>
                    {p.description.length > 60
                      ? p.description.slice(0, 60) + '...'
                      : p.description}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* 페이지네이션 */}
      <Pagination
        page={page}
        totalPages={totalPages}
        onPageChange={setPage}
        disabled={loading}
      />
    </div>
  );
}
