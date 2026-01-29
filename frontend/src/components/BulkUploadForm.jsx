import { useState, useRef } from 'react';
import { bulkUploadProducts } from '../api/products';

/**
 * CSV bulk upload form for products.
 * @param {Object} props
 * @param {Function} props.onUploaded - Callback after successful upload
 * @param {Function} props.onCancel - Cancel handler
 */
export default function BulkUploadForm({ onUploaded, onCancel }) {
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
