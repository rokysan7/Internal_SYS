import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { getQuoteRequests, getDefaultAssignees, setDefaultAssignees } from '../api/quoteRequests';
import { getAssignees } from '../api/cases';
import { useAuth } from '../contexts/AuthContext';
import { ROLES } from '../constants/roles';
import Pagination from '../components/Pagination';
import Spinner from '../components/Spinner';
import QuoteRequestDetail from './QuoteRequestDetail';
import { formatDate } from '../components/utils';
import './shared.css';

export default function QuoteRequestPage() {
  const { id } = useParams();

  if (id) return <QuoteRequestDetail qrId={id} />;
  return <QuoteRequestListView />;
}

function QuoteRequestListView() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [showSettings, setShowSettings] = useState(false);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const statusFilter = searchParams.get('status') ?? 'OPEN';
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchList() {
      try {
        const params = { page, page_size: 20 };
        if (statusFilter && statusFilter !== 'ALL') params.status = statusFilter;
        if (searchTerm) params.search = searchTerm;
        const res = await getQuoteRequests(params);
        setItems(res.data?.items || []);
        setTotalPages(res.data?.total_pages || 1);
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to load quote requests');
      } finally {
        setLoading(false);
      }
    }
    setLoading(true);
    fetchList();
  }, [page, statusFilter, searchTerm]);

  const updateParams = (updates) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value) newParams.set(key, value);
      else newParams.delete(key);
    });
    setSearchParams(newParams);
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1>Quote Requests</h1>
        {user?.role === ROLES.ADMIN && (
          <button className="btn btn-secondary" onClick={() => setShowSettings(true)}>
            Default Assignees
          </button>
        )}
      </div>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="Search organization / quote..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          value={statusFilter}
          onChange={(e) => updateParams({ status: e.target.value, page: '1' })}
        >
          <option value="ALL">All Status</option>
          <option value="OPEN">Open</option>
          <option value="DONE">Done</option>
        </select>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">No quote requests found.</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Quote Request</th>
                <th>Status</th>
                <th>Organization</th>
                <th>Received</th>
              </tr>
            </thead>
            <tbody>
              {items.map((qr) => (
                <tr
                  key={qr.id}
                  className="clickable-row"
                  onClick={() => navigate(`/quote-requests/${qr.id}`)}
                >
                  <td>#{qr.id}</td>
                  <td style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {qr.quote_request}
                  </td>
                  <td>
                    <span className={`badge ${qr.status === 'DONE' ? 'badge-done' : 'badge-open'}`}>
                      {qr.status}
                    </span>
                  </td>
                  <td>{qr.organization || '-'}</td>
                  <td>{formatDate(qr.received_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination
        page={page}
        totalPages={totalPages}
        onPageChange={(p) => updateParams({ page: p.toString() })}
        disabled={loading}
      />

      {showSettings && (
        <DefaultAssigneesModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}

function DefaultAssigneesModal({ onClose }) {
  const [allUsers, setAllUsers] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [usersRes, defaultRes] = await Promise.all([
          getAssignees(),
          getDefaultAssignees(),
        ]);
        setAllUsers(usersRes.data);
        setSelectedIds(new Set(defaultRes.data.map((u) => u.id)));
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to load settings');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const toggle = (userId) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await setDefaultAssignees([...selectedIds]);
      onClose();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 440 }}>
        <h2 style={{ marginBottom: 4 }}>Default Assignees</h2>
        <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: 16 }}>
          Selected users will be auto-assigned to new quote requests.
        </p>

        {loading ? (
          <Spinner />
        ) : (
          <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            {allUsers.map((u) => (
              <label
                key={u.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 4px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f1f5f9',
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(u.id)}
                  onChange={() => toggle(u.id)}
                />
                <span>{u.name}</span>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{u.email}</span>
              </label>
            ))}
          </div>
        )}

        <div className="modal-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving || loading}>
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
