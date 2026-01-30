import { useEffect, useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createCase, getSimilarCases, getAssignees } from '../api/cases';
import { getAllProducts, getProductLicenses } from '../api/products';
import useDebounce from '../hooks/useDebounce';

/**
 * CS Case creation form with searchable product dropdown.
 */
export default function CaseForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: '', content: '', requester: '', priority: 'MEDIUM',
    product_id: '', license_id: '', assignee_id: '', tags: '',
  });
  const [products, setProducts] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [assignees, setAssignees] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  // Product search state
  const [productSearch, setProductSearch] = useState('');
  const [showProductDropdown, setShowProductDropdown] = useState(false);
  const productDropdownRef = useRef(null);

  // Similar cases state
  const [similarCases, setSimilarCases] = useState([]);
  const [similarLoading, setSimilarLoading] = useState(false);
  const debouncedTitle = useDebounce(form.title, 500);

  useEffect(() => {
    // Fetch all products (no pagination)
    getAllProducts().then((res) => setProducts(res.data)).catch(() => {});
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

  // Similar cases search (debounced)
  useEffect(() => {
    if (debouncedTitle.trim().length <= 3) {
      setSimilarCases([]);
      return;
    }
    setSimilarLoading(true);
    getSimilarCases(debouncedTitle.trim())
      .then((res) => setSimilarCases(res.data))
      .catch(() => setSimilarCases([]))
      .finally(() => setSimilarLoading(false));
  }, [debouncedTitle]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (productDropdownRef.current && !productDropdownRef.current.contains(e.target)) {
        setShowProductDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleProductSelect = (product) => {
    setForm((prev) => ({ ...prev, product_id: product.id }));
    setProductSearch(product.name);
    setShowProductDropdown(false);
  };

  const handleProductClear = () => {
    setForm((prev) => ({ ...prev, product_id: '', license_id: '' }));
    setProductSearch('');
  };

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(productSearch.toLowerCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim() || !form.requester.trim()) return;
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        product_id: form.product_id ? Number(form.product_id) : null,
        license_id: form.license_id ? Number(form.license_id) : null,
        assignee_id: form.assignee_id ? Number(form.assignee_id) : null,
        tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      };
      const res = await createCase(payload);
      navigate(`/cases/${res.data.id}`);
    } catch (err) {
      console.error('Case creation failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const statusLabel = (status) => {
    switch (status) {
      case 'OPEN': return 'Open';
      case 'IN_PROGRESS': return 'In Progress';
      case 'DONE': return 'Done';
      default: return status;
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

          {/* Similar cases */}
          {(similarCases.length > 0 || similarLoading) && (
            <div className="similar-cases">
              <div className="similar-cases-header">
                💡 {similarLoading ? 'Searching...' : `${similarCases.length} similar cases`}
              </div>
              {similarCases.map((sc) => (
                <Link key={sc.id} to={`/cases/${sc.id}`} className="similar-case-item">
                  <span className="similar-case-id">#{sc.id}</span>
                  <span className="similar-case-title">{sc.title}</span>
                  <span className={`badge badge-${sc.status.toLowerCase().replace('_', '-')}`}>
                    {statusLabel(sc.status)}
                  </span>
                </Link>
              ))}
            </div>
          )}

          <div className="form-group">
            <label>Content *</label>
            <textarea name="content" value={form.content} onChange={handleChange} required />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Requester *</label>
              <input name="requester" value={form.requester} onChange={handleChange} required />
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

          <div className="form-group">
            <label>Assignee</label>
            <select name="assignee_id" value={form.assignee_id} onChange={handleChange}>
              <option value="">-- Not assigned --</option>
              {assignees.map((u) => (
                <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            {/* Searchable Product Dropdown */}
            <div className="form-group" ref={productDropdownRef} style={{ position: 'relative' }}>
              <label>Product</label>
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                <input
                  type="text"
                  placeholder="Search product..."
                  value={productSearch}
                  onChange={(e) => {
                    setProductSearch(e.target.value);
                    setShowProductDropdown(true);
                    if (!e.target.value) handleProductClear();
                  }}
                  onFocus={() => setShowProductDropdown(true)}
                  style={{ flex: 1 }}
                />
                {form.product_id && (
                  <button type="button" className="btn btn-secondary" onClick={handleProductClear}>
                    ✕
                  </button>
                )}
              </div>
              {showProductDropdown && (
                <div className="dropdown-list" style={{
                  position: 'absolute', top: '100%', left: 0, right: 0,
                  background: 'var(--bg-secondary, #fff)', border: '1px solid var(--border-color, #ddd)',
                  borderRadius: 4, maxHeight: 200, overflowY: 'auto', zIndex: 10,
                }}>
                  {filteredProducts.length === 0 ? (
                    <div style={{ padding: '0.5rem', color: '#888' }}>No results</div>
                  ) : (
                    filteredProducts.map((p) => (
                      <div
                        key={p.id}
                        onClick={() => handleProductSelect(p)}
                        style={{
                          padding: '0.5rem', cursor: 'pointer',
                          background: form.product_id === p.id ? 'var(--accent-light, #e3f2fd)' : 'transparent',
                        }}
                        onMouseEnter={(e) => e.target.style.background = 'var(--hover-bg, #f5f5f5)'}
                        onMouseLeave={(e) => e.target.style.background = form.product_id === p.id ? 'var(--accent-light, #e3f2fd)' : 'transparent'}
                      >
                        {p.name}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

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
            <label>Tags (comma separated)</label>
            <input
              name="tags"
              value={form.tags}
              onChange={handleChange}
              placeholder="e.g. login, error, urgent"
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
