import { memo, useState } from 'react';
import { deleteLicense } from '../api/licenses';
import { ROLES } from '../constants/roles';
import { formatDate } from './utils';

/**
 * License table with selection and delete.
 * @param {Object} props
 * @param {Array} props.licenses - List of license objects
 * @param {Object} props.user - Current user
 * @param {Object|null} props.selectedLicense - Currently selected license
 * @param {Function} props.onSelect - Called with license object on click
 * @param {Function} props.onDeleted - Called with license id after delete
 */
export default memo(function LicenseListCard({ licenses, user, selectedLicense, onSelect, onDeleted }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (lic) => {
    if (!window.confirm(`Delete license "${lic.name}"? This will also delete all memos.`)) return;
    setDeletingId(lic.id);
    try {
      await deleteLicense(lic.id);
      onDeleted(lic.id);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Delete failed';
      alert(msg);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="card" style={{ marginTop: '1.25rem', marginBottom: '1.25rem' }}>
      <div className="section-title">Licenses ({licenses.length})</div>
      {licenses.length === 0 ? (
        <div className="empty-state">No licenses registered.</div>
      ) : (
        <div className="table-wrap" style={{ border: 'none' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Created</th>
                {user?.role === ROLES.ADMIN && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {licenses.map((lic) => (
                <tr
                  key={lic.id}
                  onClick={() => onSelect(lic)}
                  className={`license-row${selectedLicense?.id === lic.id ? ' selected' : ''}`}
                >
                  <td>#{lic.id}</td>
                  <td>{lic.name}</td>
                  <td>{lic.description || '-'}</td>
                  <td>{formatDate(lic.created_at)}</td>
                  {user?.role === ROLES.ADMIN && (
                    <td>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={(e) => { e.stopPropagation(); handleDelete(lic); }}
                        disabled={deletingId === lic.id}
                        style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                      >
                        {deletingId === lic.id ? '...' : 'Delete'}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
});
