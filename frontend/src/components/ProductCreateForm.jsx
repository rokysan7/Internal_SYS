import { useState } from 'react';
import { createProduct } from '../api/products';

/**
 * Product creation form.
 * @param {Object} props
 * @param {Function} props.onCreated - Callback after successful creation
 * @param {Function} props.onCancel - Cancel handler
 */
export default function ProductCreateForm({ onCreated, onCancel }) {
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
