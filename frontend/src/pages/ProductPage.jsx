import { useState } from 'react';
import { Link } from 'react-router-dom';
import { getProductLicenses } from '../api/products';
import { getProductMemos } from '../api/memos';
import ProductSearch from '../components/ProductSearch';
import ProductCreateForm from '../components/ProductCreateForm';
import BulkUploadForm from '../components/BulkUploadForm';
import MemoList from '../components/MemoList';
import { formatDate } from '../components/utils';
import './shared.css';
import './ProductPage.css';

export default function ProductPage() {
  const [selected, setSelected] = useState(null);
  const [licenses, setLicenses] = useState([]);
  const [memos, setMemos] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleSelect = async (product) => {
    setSelected(product);
    try {
      const [licRes, memoRes] = await Promise.all([
        getProductLicenses(product.id),
        getProductMemos(product.id),
      ]);
      setLicenses(licRes.data);
      setMemos(memoRes.data);
    } catch (err) {
      console.error('Product detail fetch failed:', err);
    }
  };

  const handleMemoAdded = (newMemo) => {
    setMemos((prev) => [...prev, newMemo]);
  };

  const handleBulkUploaded = () => {
    setShowBulkUpload(false);
    setRefreshKey((k) => k + 1);
  };

  return (
    <div>
      <div className="page-header">
        <h1>Products</h1>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={() => setShowBulkUpload(true)}>
            CSV Import
          </button>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + New Product
          </button>
        </div>
      </div>

      {showBulkUpload && (
        <BulkUploadForm
          onUploaded={handleBulkUploaded}
          onCancel={() => setShowBulkUpload(false)}
        />
      )}

      {showCreate && (
        <ProductCreateForm
          onCreated={() => { setShowCreate(false); setRefreshKey((k) => k + 1); }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.25rem' }}>
        {/* Product Search Panel */}
        <ProductSearch onSelect={handleSelect} selectedId={selected?.id ?? null} refreshKey={refreshKey} />

        {/* Product Detail Panel */}
        <div>
          {!selected ? (
            <div className="card">
              <div className="empty-state">Select a product to view details.</div>
            </div>
          ) : (
            <>
              {/* Product Info */}
              <div className="card" style={{ marginBottom: '1.25rem' }}>
                <div className="section-title">{selected.name}</div>
                {selected.description && (
                  <p style={{ fontSize: '0.9rem', color: '#475569', marginBottom: '0.75rem' }}>
                    {selected.description}
                  </p>
                )}
                <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                  Created: {formatDate(selected.created_at)}
                </div>
              </div>

              {/* Licenses */}
              <div className="card" style={{ marginBottom: '1.25rem' }}>
                <div className="section-title">Licenses ({licenses.length})</div>
                {licenses.length === 0 ? (
                  <div className="empty-state">No licenses registered.</div>
                ) : (
                  <div className="table-wrap" style={{ border: 'none' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Name</th>
                          <th>Description</th>
                          <th>Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        {licenses.map((lic) => (
                          <tr key={lic.id}>
                            <td><Link to={`/licenses/${lic.id}`}>#{lic.id}</Link></td>
                            <td><Link to={`/licenses/${lic.id}`}>{lic.name}</Link></td>
                            <td>{lic.description || '-'}</td>
                            <td>{formatDate(lic.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Product Memos */}
              <MemoList
                title="Product Memos"
                memos={memos}
                entityType="product"
                entityId={selected.id}
                onMemoAdded={handleMemoAdded}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
