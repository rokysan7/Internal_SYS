import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';
import AdminRoute from './components/AdminRoute';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import CasePage from './pages/CasePage';
import ProductPage from './pages/ProductPage';

import UserListPage from './pages/admin/UserListPage';
import UserCreatePage from './pages/admin/UserCreatePage';
import UserEditPage from './pages/admin/UserEditPage';

export default function App() {
  return (
    <Routes>
      {/* Public route */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes */}
      <Route
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="cases" element={<CasePage />} />
        <Route path="cases/new" element={<CasePage />} />
        <Route path="cases/:id" element={<CasePage />} />
        <Route path="products" element={<ProductPage />} />

        {/* Admin routes */}
        <Route path="admin/users" element={<AdminRoute><UserListPage /></AdminRoute>} />
        <Route path="admin/users/new" element={<AdminRoute><UserCreatePage /></AdminRoute>} />
        <Route path="admin/users/:id" element={<AdminRoute><UserEditPage /></AdminRoute>} />
      </Route>
    </Routes>
  );
}
