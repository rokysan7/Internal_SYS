import { useState } from 'react';
import { Link } from 'react-router-dom';
import { getProductLicenses, createProduct } from '../api/products';
import { getProductMemos } from '../api/memos';
import ProductSearch from '../components/ProductSearch';
import MemoList from '../components/MemoList';
import { formatDate } from '../components/utils';
import './pages.css';

export default function ProductPage() {
  const [selected, setSelected] = useState(null);
  const [licenses, setLicenses] = useState([]);
  const [memos, setMemos] = useState([]);
  const [showCreate, setShowCreate] = useState(false);

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

  return (
    <div>
      <div className="page-header">
        <h1>Products</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          + New Product
        </button>
      </div>

      {showCreate && (
        <ProductCreateForm
          onCreated={() => setShowCreate(false)}
          onCancel={() => setShowCreate(false)}
        />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.25rem' }}>
        {/* Product Search Panel */}
        <ProductSearch onSelect={handleSelect} selectedId={selected?.id ?? null} />

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

/* ========== Product Create Form ========== */
function ProductCreateForm({ onCreated, onCancel }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await createProduct({ name, description: description || null });
      onCreated();
    } catch (err) {
      console.error('Product creation failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 480, marginBottom: '1.25rem' }}>
      <div className="section-title">Create Product</div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Name *</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Description</label>
          <input value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="submit" className="btn btn-primary btn-sm" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create'}
          </button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
