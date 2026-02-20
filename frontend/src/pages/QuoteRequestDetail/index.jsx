import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ROLES } from '../../constants/roles';
import {
  getQuoteRequest,
  deleteQuoteRequest,
  updateQuoteRequestStatus,
  getQuoteRequestComments,
  createQuoteRequestComment,
  deleteQuoteRequestComment,
} from '../../api/quoteRequests';
import { useAuth } from '../../contexts/AuthContext';
import Spinner from '../../components/Spinner';
import CommentsCard from '../../components/CaseDetail/CommentsCard';
import InfoCard from './InfoCard';
import QuoteRequestCard from './QuoteRequestCard';
import FailedProductsCard from './FailedProductsCard';

export default function QuoteRequestDetail({ qrId }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function fetchAll() {
      try {
        const [qrRes, commentsRes] = await Promise.all([
          getQuoteRequest(qrId),
          getQuoteRequestComments(qrId),
        ]);
        setData(qrRes.data);
        setComments(commentsRes.data);
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to load quote request');
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, [qrId]);

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this quote request?')) return;
    setDeleting(true);
    try {
      await deleteQuoteRequest(qrId);
      navigate('/quote-requests');
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed');
    } finally {
      setDeleting(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      const res = await updateQuoteRequestStatus(qrId, newStatus);
      setData((prev) => ({ ...prev, ...res.data }));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleAddComment = async (content, parentId = null) => {
    if (!content.trim()) return;
    try {
      await createQuoteRequestComment(qrId, { content, parent_id: parentId });
      const commentsRes = await getQuoteRequestComments(qrId);
      setComments(commentsRes.data);
      setNewComment('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add comment');
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await deleteQuoteRequestComment(qrId, commentId);
      const commentsRes = await getQuoteRequestComments(qrId);
      setComments(commentsRes.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed');
    }
  };

  if (loading) return <Spinner />;
  if (!data) return <div className="empty-state">Quote request not found.</div>;

  return (
    <div>
      <Link to="/quote-requests" className="back-link">&larr; Back to Quote Requests</Link>

      <div className="page-header">
        <div>
          <h1 style={{ fontSize: '1.2rem' }}>Quote Request #{data.id}</h1>
          <span className={`badge ${data.status === 'DONE' ? 'badge-done' : 'badge-open'}`}>
            {data.status}
          </span>
        </div>
        {user?.role === ROLES.ADMIN && (
          <button className="btn btn-danger" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        )}
      </div>

      <div className="detail-grid">
        <div className="detail-main">
          <QuoteRequestCard content={data.quote_request} otherRequest={data.other_request} />
          <FailedProductsCard products={data.failed_products} />
          {data.additional_request && (
            <div className="card">
              <div className="section-title">Additional Request</div>
              <p style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {data.additional_request}
              </p>
            </div>
          )}
          <CommentsCard
            comments={comments}
            value={newComment}
            onChange={setNewComment}
            onAdd={handleAddComment}
            onDelete={handleDeleteComment}
            currentUser={user}
          />
        </div>

        <div className="detail-side">
          <InfoCard data={data} onStatusChange={handleStatusChange} />
        </div>
      </div>
    </div>
  );
}
