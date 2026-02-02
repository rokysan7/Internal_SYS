import { useState } from 'react';
import { Link } from 'react-router-dom';
import { getProductLicenses, deleteProduct, updateProduct } from '../api/products';
import { deleteLicense } from '../api/licenses';
import { getProductMemos } from '../api/memos';
import { useAuth } from '../contexts/AuthContext';
import ProductSearch from '../components/ProductSearch';
import ProductCreateForm from '../components/ProductCreateForm';
import BulkUploadForm from '../components/BulkUploadForm';
import MemoList from '../components/MemoList';
import { formatDate } from '../components/utils';
import './shared.css';
import './ProductPage.css';

export default function ProductPage() {
  const { user } = useAuth();
  const [selected, setSelected] = useState(null);
  const [licenses, setLicenses] = useState([]);
  const [memos, setMemos] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [deletingLicenseId, setDeletingLicenseId] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [saving, setSaving] = useState(false);

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

  const handleMemoDeleted = (memoId) => {
    setMemos((prev) => prev.filter((m) => m.id !== memoId));
  };

  const handleDeleteLicense = async (lic) => {
    if (!window.confirm(`Delete license "${lic.name}"? This will also delete all memos.`)) return;
    setDeletingLicenseId(lic.id);
    try {
      await deleteLicense(lic.id);
      setLicenses((prev) => prev.filter((l) => l.id !== lic.id));
    } catch (err) {
      const msg = err.response?.data?.detail || 'Delete failed';
      alert(msg);
    } finally {
      setDeletingLicenseId(null);
    }
  };

  const handleBulkUploaded = () => {
    setShowBulkUpload(false);
    setRefreshKey((k) => k + 1);
  };

  const handleStartEdit = () => {
    setEditName(selected.name);
    setEditDescription(selected.description || '');
    setEditing(true);
  };

  const handleCancelEdit = () => {
    setEditing(false);
  };

  const handleSaveEdit = async () => {
    if (!editName.trim()) {
      alert('Name is required');
      return;
    }
    setSaving(true);
    try {
      const res = await updateProduct(selected.id, {
        name: editName.trim(),
        description: editDescription.trim() || null,
      });
      setSelected(res.data);
      setEditing(false);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Update failed';
      alert(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selected) return;
    if (!window.confirm(`Delete "${selected.name}"? This will also delete all licenses and memos.`)) return;
    setDeleting(true);
    try {
      await deleteProduct(selected.id);
      setSelected(null);
      setLicenses([]);
      setMemos([]);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Delete failed';
      alert(msg);
    } finally {
      setDeleting(false);
    }
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
                {editing ? (
                  <>
                    <div style={{ marginBottom: '0.75rem' }}>
                      <label style={{ fontSize: '0.85rem', color: '#64748b', display: 'block', marginBottom: '0.25rem' }}>Name</label>
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #cbd5e1', borderRadius: 6 }}
                      />
                    </div>
                    <div style={{ marginBottom: '0.75rem' }}>
                      <label style={{ fontSize: '0.85rem', color: '#64748b', display: 'block', marginBottom: '0.25rem' }}>Description</label>
                      <textarea
                        value={editDescription}
                        onChange={(e) => setEditDescription(e.target.value)}
                        rows={3}
                        style={{ width: '100%', padding: '0.5rem', border: '1px solid #cbd5e1', borderRadius: 6, resize: 'vertical' }}
                      />
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="btn btn-primary btn-sm" onClick={handleSaveEdit} disabled={saving}>
                        {saving ? 'Saving...' : 'Save'}
                      </button>
                      <button className="btn btn-secondary btn-sm" onClick={handleCancelEdit} disabled={saving}>
                        Cancel
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div className="section-title">{selected.name}</div>
                      {user?.role === 'ADMIN' && (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button className="btn btn-secondary btn-sm" onClick={handleStartEdit}>
                            Edit
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={handleDelete}
                            disabled={deleting}
                          >
                            {deleting ? 'Deleting...' : 'Delete'}
                          </button>
                        </div>
                      )}
                    </div>
                    {selected.description && (
                      <p style={{ fontSize: '0.9rem', color: '#475569', marginBottom: '0.75rem' }}>
                        {selected.description}
                      </p>
                    )}
                    <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                      Created: {formatDate(selected.created_at)}
                    </div>
                  </>
                )}
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
                          {user?.role === 'ADMIN' && <th>Actions</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {licenses.map((lic) => (
                          <tr key={lic.id}>
                            <td><Link to={`/licenses/${lic.id}`}>#{lic.id}</Link></td>
                            <td><Link to={`/licenses/${lic.id}`}>{lic.name}</Link></td>
                            <td>{lic.description || '-'}</td>
                            <td>{formatDate(lic.created_at)}</td>
                            {user?.role === 'ADMIN' && (
                              <td>
                                <button
                                  className="btn btn-danger btn-sm"
                                  onClick={() => handleDeleteLicense(lic)}
                                  disabled={deletingLicenseId === lic.id}
                                  style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                                >
                                  {deletingLicenseId === lic.id ? '...' : 'Delete'}
                                </button>
                              </td>
                            )}
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
                currentUser={user}
                onMemoAdded={handleMemoAdded}
                onMemoDeleted={handleMemoDeleted}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
