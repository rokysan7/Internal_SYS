import { useState, useCallback } from 'react';
import { getProductLicenses, deleteProduct } from '../api/products';
import { getProductMemos, getLicenseMemos } from '../api/memos';
import { useAuth } from '../contexts/AuthContext';
import ProductSearch from '../components/ProductSearch';
import ProductCreateForm from '../components/ProductCreateForm';
import BulkUploadForm from '../components/BulkUploadForm';
import ProductDetailCard from '../components/ProductDetailCard';
import LicenseListCard from '../components/LicenseListCard';
import MemoList from '../components/MemoList';
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
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [licenseMemos, setLicenseMemos] = useState([]);

  const handleSelect = useCallback(async (product) => {
    setSelected(product);
    setSelectedLicense(null);
    setLicenseMemos([]);
    try {
      const [licRes, memoRes] = await Promise.all([
        getProductLicenses(product.id),
        getProductMemos(product.id),
      ]);
      setLicenses(licRes.data);
      setMemos(memoRes.data);
    } catch (err) {
      console.error('Product detail fetch failed:', err);
      alert(err.response?.data?.detail || 'Failed to load product details');
    }
  }, []);

  const handleSelectLicense = useCallback(async (lic) => {
    let deselecting = false;
    setSelectedLicense((prev) => {
      if (prev?.id === lic.id) {
        deselecting = true;
        return null;
      }
      return lic;
    });
    if (deselecting) {
      setLicenseMemos([]);
      return;
    }
    try {
      const res = await getLicenseMemos(lic.id);
      setLicenseMemos(res.data);
    } catch (err) {
      console.error('License memo fetch failed:', err);
      alert(err.response?.data?.detail || 'Failed to load license memos');
    }
  }, []);

  const handleProductUpdated = useCallback((updatedProduct) => {
    setSelected(updatedProduct);
    setRefreshKey((k) => k + 1);
  }, []);

  const handleDelete = useCallback(async (product) => {
    if (!product) return;
    if (!window.confirm(`Delete "${product.name}"? This will also delete all licenses and memos.`)) return;
    setDeleting(true);
    try {
      await deleteProduct(product.id);
      setSelected(null);
      setLicenses([]);
      setMemos([]);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed');
    } finally {
      setDeleting(false);
    }
  }, []);

  const handleLicenseDeleted = useCallback((licenseId) => {
    setLicenses((prev) => prev.filter((l) => l.id !== licenseId));
    setSelectedLicense((prev) => {
      if (prev?.id === licenseId) {
        setLicenseMemos([]);
        return null;
      }
      return prev;
    });
  }, []);

  const handleMemoAdded = useCallback((newMemo) => {
    setMemos((prev) => [...prev, newMemo]);
  }, []);

  const handleMemoDeleted = useCallback((memoId) => {
    setMemos((prev) => prev.filter((m) => m.id !== memoId));
  }, []);

  const handleLicenseMemoAdded = useCallback((newMemo) => {
    setLicenseMemos((prev) => [...prev, newMemo]);
  }, []);

  const handleLicenseMemoDeleted = useCallback((memoId) => {
    setLicenseMemos((prev) => prev.filter((m) => m.id !== memoId));
  }, []);

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
          onUploaded={() => { setShowBulkUpload(false); setRefreshKey((k) => k + 1); }}
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
        <ProductSearch onSelect={handleSelect} selectedId={selected?.id ?? null} refreshKey={refreshKey} />

        <div>
          {!selected ? (
            <div className="card">
              <div className="empty-state">Select a product to view details.</div>
            </div>
          ) : (
            <>
              <ProductDetailCard
                product={selected}
                user={user}
                onUpdated={handleProductUpdated}
                deleting={deleting}
                onDelete={() => handleDelete(selected)}
              />

              <MemoList
                title="Product Memos"
                memos={memos}
                entityType="product"
                entityId={selected.id}
                currentUser={user}
                onMemoAdded={handleMemoAdded}
                onMemoDeleted={handleMemoDeleted}
              />

              <LicenseListCard
                licenses={licenses}
                user={user}
                selectedLicense={selectedLicense}
                onSelect={handleSelectLicense}
                onDeleted={handleLicenseDeleted}
              />

              {selectedLicense && (
                <MemoList
                  title={`${selectedLicense.name} Memos`}
                  memos={licenseMemos}
                  entityType="license"
                  entityId={selectedLicense.id}
                  currentUser={user}
                  onMemoAdded={handleLicenseMemoAdded}
                  onMemoDeleted={handleLicenseMemoDeleted}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
