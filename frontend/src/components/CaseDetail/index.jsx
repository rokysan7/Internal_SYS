import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ROLES } from '../../constants/roles';
import {
  getCase,
  deleteCase,
  updateCaseStatus,
  getComments,
  createComment,
  deleteComment,
  getChecklists,
  createChecklist,
  updateChecklist,
} from '../../api/cases';
import { useAuth } from '../../contexts/AuthContext';
import Spinner from '../Spinner';
import { statusBadgeClass, statusLabel } from '../utils';

import DescriptionCard from './DescriptionCard';
import CommentsCard from './CommentsCard';
import InfoCard from './InfoCard';
import ChecklistCard from './ChecklistCard';
import SimilarCasesPanel from './SimilarCasesPanel';

/**
 * CS Case detail view (with comments + checklists).
 * @param {Object} props
 * @param {string|number} props.caseId - Case ID
 */
export default function CaseDetail({ caseId }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [caseData, setCaseData] = useState(null);
  const [comments, setComments] = useState([]);
  const [checklists, setChecklists] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [newCheckItem, setNewCheckItem] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function fetchAll() {
      try {
        const [caseRes, commentsRes, checkRes] = await Promise.all([
          getCase(caseId),
          getComments(caseId),
          getChecklists(caseId),
        ]);
        setCaseData(caseRes.data);
        setComments(commentsRes.data);
        setChecklists(checkRes.data);
      } catch (err) {
        console.error('Failed to load case:', err);
        alert(err.response?.data?.detail || 'Failed to load case');
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, [caseId]);

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this case?')) return;
    setDeleting(true);
    try {
      await deleteCase(caseId);
      navigate('/cases');
    } catch (err) {
      console.error('Delete failed:', err);
      alert(err.response?.data?.detail || 'Delete failed');
    } finally {
      setDeleting(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      const res = await updateCaseStatus(caseId, newStatus);
      setCaseData((prev) => ({ ...prev, ...res.data }));
    } catch (err) {
      console.error('Status update failed:', err);
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleAddComment = async (content, parentId = null) => {
    if (!content.trim()) return;
    try {
      await createComment(caseId, {
        content,
        is_internal: false,
        parent_id: parentId,
      });
      // Refresh comments to get updated tree structure
      const commentsRes = await getComments(caseId);
      setComments(commentsRes.data);
      setNewComment('');
    } catch (err) {
      console.error('Comment creation failed:', err);
      alert(err.response?.data?.detail || 'Failed to add comment');
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await deleteComment(caseId, commentId);
      // Refresh comments
      const commentsRes = await getComments(caseId);
      setComments(commentsRes.data);
    } catch (err) {
      console.error('Comment deletion failed:', err);
      alert(err.response?.data?.detail || 'Delete failed');
    }
  };

  const handleAddCheckItem = async () => {
    if (!newCheckItem.trim()) return;
    try {
      const res = await createChecklist(caseId, { content: newCheckItem });
      setChecklists((prev) => [...prev, res.data]);
      setNewCheckItem('');
    } catch (err) {
      console.error('Checklist creation failed:', err);
      alert(err.response?.data?.detail || 'Failed to add checklist item');
    }
  };

  const handleToggleCheck = async (item) => {
    try {
      await updateChecklist(item.id, !item.is_done);
      setChecklists((prev) =>
        prev.map((c) => (c.id === item.id ? { ...c, is_done: !c.is_done } : c)),
      );
    } catch (err) {
      console.error('Checklist toggle failed:', err);
      alert(err.response?.data?.detail || 'Failed to update checklist');
    }
  };

  if (loading) return <Spinner />;
  if (!caseData) return <div className="empty-state">Case not found.</div>;

  return (
    <div>
      <Link to="/cases" className="back-link">← Back to Cases</Link>

      <div className="page-header">
        <div>
          <h1>{caseData.title}</h1>
          <span className={`badge ${statusBadgeClass(caseData.status)}`}>
            {statusLabel(caseData.status)}
          </span>
        </div>
        {(user?.role === ROLES.ADMIN || user?.id === caseData.assignee_id) && (
          <button
            className="btn btn-danger"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete Case'}
          </button>
        )}
      </div>

      <div className="detail-grid">
        {/* Main Column */}
        <div className="detail-main">
          <DescriptionCard content={caseData.content} />
          <CommentsCard
            comments={comments}
            value={newComment}
            onChange={setNewComment}
            onAdd={handleAddComment}
            onDelete={handleDeleteComment}
            currentUser={user}
          />
        </div>

        {/* Side Column */}
        <div className="detail-side">
          <InfoCard caseData={caseData} onStatusChange={handleStatusChange} />
          <ChecklistCard
            checklists={checklists}
            value={newCheckItem}
            onChange={setNewCheckItem}
            onAdd={handleAddCheckItem}
            onToggle={handleToggleCheck}
          />
          <SimilarCasesPanel caseId={caseId} />
        </div>
      </div>
    </div>
  );
}
