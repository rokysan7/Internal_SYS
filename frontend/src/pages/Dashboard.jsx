import { useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ROLES } from '../constants/roles';
import AdminOverview from './dashboard/AdminOverview';
import MyProgress from './dashboard/MyProgress';
import CaseSection from './dashboard/CaseSection';
import './shared.css';
import './Dashboard.css';

export default function Dashboard() {
  const { user } = useAuth();
  const isAdmin = user?.role === ROLES.ADMIN;

  const assignedParams = useMemo(
    () => (user?.id ? { assignee_id: user.id } : {}),
    [user?.id],
  );
  const createdParams = useMemo(
    () => (user?.name ? { requester: user.name } : {}),
    [user?.name],
  );

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      {isAdmin && <AdminOverview />}
      <MyProgress />

      <CaseSection title="My Assigned Cases" params={assignedParams} />
      <CaseSection title="My Created Cases" params={createdParams} />
      {isAdmin && <CaseSection title="Recent Cases" params={{}} />}
    </div>
  );
}
