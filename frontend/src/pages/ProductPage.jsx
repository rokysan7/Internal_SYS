import { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { getProductLicenses, createProduct, bulkUploadProducts } from '../api/products';
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

/* ========== CSV Bulk Upload Form ========== */
function BulkUploadForm({ onUploaded, onCancel }) {
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await bulkUploadProducts(file);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 560, marginBottom: '1.25rem' }}>
      <div className="section-title">CSV Bulk Import</div>
      <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
        CSV 형식: <code>product,license</code> (헤더 필수)
      </p>

      <div className="form-group">
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          style={{ fontSize: '0.9rem' }}
        />
      </div>

      {file && !result && (
        <div style={{ marginBottom: '1rem', fontSize: '0.85rem', color: '#475569' }}>
          선택된 파일: <strong>{file.name}</strong>
        </div>
      )}

      {error && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#fef2f2', color: '#dc2626', borderRadius: 6, fontSize: '0.85rem' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#f0fdf4', borderRadius: 6, fontSize: '0.85rem' }}>
          <div><strong>Products:</strong> {result.products_created} created, {result.products_existing} existing</div>
          <div><strong>Licenses:</strong> {result.licenses_created} created, {result.licenses_existing} existing</div>
          {result.errors?.length > 0 && (
            <div style={{ marginTop: '0.5rem', color: '#dc2626' }}>
              Errors: {result.errors.join(', ')}
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        {!result ? (
          <>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={onCancel}>
              Cancel
            </button>
          </>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={onUploaded}>
            Done
          </button>
        )}
      </div>
    </div>
  );
}
