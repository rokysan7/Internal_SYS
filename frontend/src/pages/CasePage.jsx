import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { getCases } from '../api/cases';
import CaseList from '../components/CaseList';
import CaseDetail from '../components/CaseDetail';
import CaseForm from '../components/CaseForm';
import './pages.css';

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
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchCases() {
      try {
        const params = {};
        if (statusFilter) params.status = statusFilter;
        const res = await getCases(params);
        setCases(res.data);
      } catch (err) {
        console.error('Failed to load cases:', err);
      } finally {
        setLoading(false);
      }
    }
    setLoading(true);
    fetchCases();
  }, [statusFilter]);

  const filtered = cases.filter((c) => {
    if (priorityFilter && c.priority !== priorityFilter) return false;
    if (searchTerm && !c.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  if (loading) return <div className="loading">Loading...</div>;

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
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Status</option>
          <option value="OPEN">Open</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="DONE">Done</option>
        </select>
        <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
          <option value="">All Priority</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <CaseList cases={filtered} />
    </div>
  );
}
