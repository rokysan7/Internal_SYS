import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getCase,
  updateCaseStatus,
  getComments,
  createComment,
  getChecklists,
  createChecklist,
  updateChecklist,
} from '../../api/cases';
import { statusBadgeClass, statusLabel } from '../utils';

import DescriptionCard from './DescriptionCard';
import CommentsCard from './CommentsCard';
import InfoCard from './InfoCard';
import ChecklistCard from './ChecklistCard';

/**
 * CS Case detail view (with comments + checklists).
 * @param {Object} props
 * @param {string|number} props.caseId - Case ID
 */
export default function CaseDetail({ caseId }) {
  const [caseData, setCaseData] = useState(null);
  const [comments, setComments] = useState([]);
  const [checklists, setChecklists] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [newCheckItem, setNewCheckItem] = useState('');
  const [loading, setLoading] = useState(true);

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
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, [caseId]);

  const handleStatusChange = async (newStatus) => {
    try {
      await updateCaseStatus(caseId, newStatus);
      setCaseData((prev) => ({ ...prev, status: newStatus }));
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    try {
      const res = await createComment(caseId, { content: newComment, is_internal: false });
      setComments((prev) => [...prev, res.data]);
      setNewComment('');
    } catch (err) {
      console.error('Comment creation failed:', err);
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
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!caseData) return <div className="empty-state">Case not found.</div>;

  return (
    <div>
      <Link to="/cases" className="back-link">← Back to Cases</Link>

      <div className="page-header">
        <h1>{caseData.title}</h1>
        <span className={`badge ${statusBadgeClass(caseData.status)}`}>
          {statusLabel(caseData.status)}
        </span>
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
        </div>
      </div>
    </div>
  );
}
