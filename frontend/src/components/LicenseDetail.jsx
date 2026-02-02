import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getLicense } from '../api/licenses';
import { getLicenseMemos } from '../api/memos';
import { useAuth } from '../contexts/AuthContext';
import MemoList from './MemoList';
import { formatDate } from './utils';

/**
 * License 상세 정보 + 메모 표시.
 * @param {number} licenseId - 라이선스 ID
 * @param {function} [onMemoAdded] - 메모 추가 후 콜백 (선택)
 */
export default function LicenseDetail({ licenseId, onMemoAdded }) {
  const { user } = useAuth();
  const [license, setLicense] = useState(null);
  const [memos, setMemos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [licRes, memoRes] = await Promise.all([
          getLicense(licenseId),
          getLicenseMemos(licenseId),
        ]);
        setLicense(licRes.data);
        setMemos(memoRes.data);
      } catch (err) {
        console.error('License fetch failed:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [licenseId]);

  const handleMemoAdded = (newMemo) => {
    setMemos((prev) => [...prev, newMemo]);
    onMemoAdded?.(newMemo);
  };

  const handleMemoDeleted = (memoId) => {
    setMemos((prev) => prev.filter((m) => m.id !== memoId));
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!license) return <div className="empty-state">License not found.</div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
      {/* License Info */}
      <div className="card">
        <div className="section-title">License Details</div>
        <div className="detail-field">
          <span className="detail-label">ID</span>
          <span className="detail-value">#{license.id}</span>
        </div>
        <div className="detail-field">
          <span className="detail-label">Name</span>
          <span className="detail-value">{license.name}</span>
        </div>
        <div className="detail-field">
          <span className="detail-label">Description</span>
          <span className="detail-value">{license.description || '-'}</span>
        </div>
        <div className="detail-field">
          <span className="detail-label">Product</span>
          <span className="detail-value">
            <Link to="/products">Product #{license.product_id}</Link>
          </span>
        </div>
        <div className="detail-field">
          <span className="detail-label">Created</span>
          <span className="detail-value">{formatDate(license.created_at)}</span>
        </div>
      </div>

      {/* Memos */}
      <MemoList
        title="License Memos"
        memos={memos}
        entityType="license"
        entityId={licenseId}
        currentUser={user}
        onMemoAdded={handleMemoAdded}
        onMemoDeleted={handleMemoDeleted}
      />
    </div>
  );
}
