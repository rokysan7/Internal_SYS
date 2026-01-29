import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUsers, deleteUser } from '../../api/admin';
import './AdminPages.css';

const ROLES = ['', 'CS', 'ENGINEER', 'ADMIN'];

export default function UserListPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getUsers(page, 20, search, roleFilter);
      setUsers(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setIsLoading(false);
    }
  }, [page, search, roleFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleDeactivate = async (user) => {
    if (!window.confirm(`Deactivate user "${user.name}"?`)) return;
    try {
      await deleteUser(user.id);
      fetchUsers();
    } catch (err) {
      alert('Failed to deactivate user');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('ko-KR');
  };

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1>User Management</h1>
        <button className="btn btn-primary" onClick={() => navigate('/admin/users/new')}>
          + New User
        </button>
      </div>

      <div className="admin-filters">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="btn btn-secondary">Search</button>
        </form>
        <select value={roleFilter} onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}>
          <option value="">All Roles</option>
          {ROLES.filter(r => r).map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Last Login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr><td colSpan={7} className="empty">No users found</td></tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id} className={!user.is_active ? 'inactive' : ''}>
                      <td>{user.name}</td>
                      <td>{user.email}</td>
                      <td><span className={`role-badge ${user.role.toLowerCase()}`}>{user.role}</span></td>
                      <td>
                        <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>{formatDate(user.created_at)}</td>
                      <td>{formatDate(user.last_login)}</td>
                      <td className="actions">
                        <button className="btn btn-sm" onClick={() => navigate(`/admin/users/${user.id}`)}>
                          Edit
                        </button>
                        {user.is_active && (
                          <button className="btn btn-sm btn-danger" onClick={() => handleDeactivate(user)}>
                            Deactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span>Total: {total} users</span>
            <div className="pagination-controls">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
              <span>Page {page} of {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
