import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { getCases } from '../api/cases';
import CaseList from '../components/CaseList';
import CaseDetail from '../components/CaseDetail';
import CaseForm from '../components/CaseForm';
import Pagination from '../components/Pagination';
import Spinner from '../components/Spinner';
import './shared.css';
import './CasePage.css';

export default function CasePage() {
  const { id } = useParams();
  const location = useLocation();
  const isNew = location.pathname === '/cases/new';

  if (isNew) return <CaseForm />;
  if (id) return <CaseDetail caseId={id} />;
  return <CaseListView />;
}

/* ========== Case List View (page-level filter logic) ========== */
function CaseListView() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);

  // URL query params
  const page = parseInt(searchParams.get('page') || '1', 10);
  const statusFilter = searchParams.get('status') || '';
  const priorityFilter = searchParams.get('priority') || '';
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchCases() {
      try {
        const params = { page, page_size: 20 };
        if (statusFilter) params.status = statusFilter;
        const res = await getCases(params);
        setCases(res.data.items);
        setTotalPages(res.data.total_pages);
      } catch (err) {
        console.error('Failed to load cases:', err);
        alert(err.response?.data?.detail || 'Failed to load cases');
      } finally {
        setLoading(false);
      }
    }
    setLoading(true);
    fetchCases();
  }, [page, statusFilter]);

  const updateParams = (updates) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value) newParams.set(key, value);
      else newParams.delete(key);
    });
    setSearchParams(newParams);
  };

  const handlePageChange = (newPage) => {
    updateParams({ page: newPage.toString() });
  };

  const handleStatusChange = (e) => {
    updateParams({ status: e.target.value, page: '1' });
  };

  const handlePriorityChange = (e) => {
    updateParams({ priority: e.target.value, page: '1' });
  };

  // Client-side filtering for priority and search (backend only filters status)
  const filtered = cases.filter((c) => {
    if (priorityFilter && c.priority !== priorityFilter) return false;
    if (searchTerm && !c.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1>CS Cases</h1>
        <button className="btn btn-primary" onClick={() => navigate('/cases/new')}>
          + New Case
        </button>
      </div>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="Search by title..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select value={statusFilter} onChange={handleStatusChange}>
          <option value="">All Status</option>
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="DONE">Done</option>
          <option value="CANCEL">Cancel</option>
        </select>
        <select value={priorityFilter} onChange={handlePriorityChange}>
          <option value="">All Priority</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <CaseList cases={filtered} />

      <Pagination
        page={page}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        disabled={loading}
      />
    </div>
  );
}
