import { useEffect, useState } from 'react';
import { getProducts } from '../api/products';

/**
 * Product 검색 + 선택 리스트.
 * @param {function} onSelect - 선택 콜백 (product object)
 * @param {number|null} selectedId - 현재 선택된 product id
 */
export default function ProductSearch({ onSelect, selectedId }) {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      getProducts(search || undefined)
        .then((res) => setProducts(res.data))
        .catch((err) => console.error('Product fetch failed:', err))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <div>
      <div className="search-box">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

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
    </div>
  );
}
