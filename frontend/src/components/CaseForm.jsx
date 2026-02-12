import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createCase, getAssignees } from '../api/cases';
import { getProductLicenses } from '../api/products';
import { useAuth } from '../contexts/AuthContext';
import ProductSearchDropdown from './ProductSearchDropdown';
import SimilarCasesWidget from './SimilarCasesWidget';
import TagInput from './TagInput';

/**
 * CS Case creation form with searchable product dropdown.
 */
export default function CaseForm() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [form, setForm] = useState({
    title: '', content: '', requester: '', priority: 'MEDIUM',
    product_id: '', license_id: '', assignee_ids: [], tags: [],
    organization: '', org_phone: '', org_contact: '',
  });
  const [licenses, setLicenses] = useState([]);
  const [assignees, setAssignees] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user?.name) {
      setForm((prev) => ({ ...prev, requester: user.name }));
    }
    getAssignees().then((res) => setAssignees(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (form.product_id) {
      getProductLicenses(form.product_id)
        .then((res) => setLicenses(res.data))
        .catch(() => setLicenses([]));
    } else {
      setLicenses([]);
      setForm((prev) => ({ ...prev, license_id: '' }));
    }
  }, [form.product_id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim() || !form.requester.trim()) return;
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        product_id: form.product_id ? Number(form.product_id) : null,
        license_id: form.license_id ? Number(form.license_id) : null,
        assignee_ids: form.assignee_ids,
        tags: form.tags,
        organization: form.organization || null,
        org_phone: form.org_phone || null,
        org_contact: form.org_contact || null,
      };
      const res = await createCase(payload);
      navigate(`/cases/${res.data.id}`);
    } catch (err) {
      console.error('Case creation failed:', err);
      alert(err.response?.data?.detail || 'Failed to create case');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Link to="/cases" className="back-link">← Back to Cases</Link>
      <div className="page-header">
        <h1>New CS Case</h1>
      </div>

      <div className="card" style={{ maxWidth: 640 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Title *</label>
            <input name="title" value={form.title} onChange={handleChange} required />
          </div>

          <SimilarCasesWidget title={form.title} content={form.content} tags={form.tags} />

          <div className="form-group">
            <label>Content *</label>
            <textarea name="content" value={form.content} onChange={handleChange} required />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Requester</label>
              <input name="requester" value={form.requester} readOnly style={{ backgroundColor: '#f1f5f9', cursor: 'default' }} />
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select name="priority" value={form.priority} onChange={handleChange}>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Organization</label>
              <input name="organization" value={form.organization} onChange={handleChange} placeholder="Requesting organization" />
            </div>
            <div className="form-group">
              <label>Org Phone</label>
              <input name="org_phone" value={form.org_phone} onChange={handleChange} placeholder="Organization phone" />
            </div>
            <div className="form-group">
              <label>Org Contact</label>
              <input name="org_contact" value={form.org_contact} onChange={handleChange} placeholder="Contact person" />
            </div>
          </div>

          <div className="form-group">
            <label>Assignees</label>
            <div className="multi-select-wrap">
              {form.assignee_ids.length > 0 && (
                <div className="selected-tags">
                  {form.assignee_ids.map((id) => {
                    const u = assignees.find((a) => a.id === id);
                    return (
                      <span key={id} className="selected-tag">
                        {u?.name || `#${id}`}
                        <button type="button" onClick={() => setForm((prev) => ({
                          ...prev, assignee_ids: prev.assignee_ids.filter((aid) => aid !== id),
                        }))}>×</button>
                      </span>
                    );
                  })}
                </div>
              )}
              <select
                value=""
                onChange={(e) => {
                  const id = Number(e.target.value);
                  if (id && !form.assignee_ids.includes(id)) {
                    setForm((prev) => ({ ...prev, assignee_ids: [...prev.assignee_ids, id] }));
                  }
                }}
              >
                <option value="">-- Add assignee --</option>
                {assignees.filter((u) => !form.assignee_ids.includes(u.id)).map((u) => (
                  <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <ProductSearchDropdown
              value={form.product_id}
              onChange={(productId) => setForm((prev) => ({ ...prev, product_id: productId, license_id: '' }))}
            />

            <div className="form-group">
              <label>License</label>
              <select
                name="license_id"
                value={form.license_id}
                onChange={handleChange}
                disabled={!form.product_id}
              >
                <option value="">-- Select --</option>
                {licenses.map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Tags</label>
            <TagInput
              value={form.tags}
              onChange={(tags) => setForm((prev) => ({ ...prev, tags }))}
              title={form.title}
              content={form.content}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Case'}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/cases')}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
