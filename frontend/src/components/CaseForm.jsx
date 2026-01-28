import { useEffect, useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createCase, getSimilarCases } from '../api/cases';
import { getProducts, getProductLicenses } from '../api/products';

/**
 * CS Case 생성 폼.
 * Product 선택 시 해당 License 목록을 자동 로드한다.
 * 제목 입력 시 (>3글자) 유사 케이스를 추천한다.
 */
export default function CaseForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: '', content: '', requester: '', priority: 'MEDIUM',
    product_id: '', license_id: '', tags: '',
  });
  const [products, setProducts] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  // AI 추천 상태
  const [similarCases, setSimilarCases] = useState([]);
  const [similarLoading, setSimilarLoading] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    getProducts().then((res) => setProducts(res.data)).catch(() => {});
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

  // 제목 변경 시 유사 케이스 검색 (debounce 500ms)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (form.title.trim().length <= 3) {
      setSimilarCases([]);
      return;
    }

    setSimilarLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await getSimilarCases(form.title.trim());
        setSimilarCases(res.data);
      } catch {
        setSimilarCases([]);
      } finally {
        setSimilarLoading(false);
      }
    }, 500);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [form.title]);

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

          {/* 유사 케이스 추천 */}
          {(similarCases.length > 0 || similarLoading) && (
            <div className="similar-cases">
              <div className="similar-cases-header">
                💡 {similarLoading ? '검색 중...' : `유사 케이스 ${similarCases.length}건`}
              </div>
              {similarCases.map((sc) => (
                <Link
                  key={sc.id}
                  to={`/cases/${sc.id}`}
                  className="similar-case-item"
                >
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

          <div className="form-row">
            <div className="form-group">
              <label>Product</label>
              <select name="product_id" value={form.product_id} onChange={handleChange}>
                <option value="">-- Select --</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
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
