import { memo, useState } from 'react';
import { updateProduct } from '../api/products';
import { ROLES } from '../constants/roles';
import { formatDate } from './utils';

/**
 * Product detail view with inline edit form.
 * @param {Object} props
 * @param {Object} props.product - Selected product object
 * @param {Object} props.user - Current user
 * @param {Function} props.onUpdated - Called with updated product data
 * @param {Function} props.onDeleted - Called when product is deleted
 * @param {boolean} props.deleting - Whether delete is in progress
 * @param {Function} props.onDelete - Called to trigger delete
 */
export default memo(function ProductDetailCard({ product, user, onUpdated, onDeleted, deleting, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [saving, setSaving] = useState(false);

  const handleStartEdit = () => {
    setEditName(product.name);
    setEditDescription(product.description || '');
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
      const res = await updateProduct(product.id, {
        name: editName.trim(),
        description: editDescription.trim() || null,
      });
      onUpdated(res.data);
      setEditing(false);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Update failed';
      alert(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
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
            <div className="section-title">{product.name}</div>
            {user?.role === ROLES.ADMIN && (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-secondary btn-sm" onClick={handleStartEdit}>
                  Edit
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={onDelete}
                  disabled={deleting}
                >
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            )}
          </div>
          {product.description && (
            <p style={{ fontSize: '0.9rem', color: '#475569', marginBottom: '0.75rem' }}>
              {product.description}
            </p>
          )}
          <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
            Created: {formatDate(product.created_at)}
          </div>
        </>
      )}
    </div>
  );
});
