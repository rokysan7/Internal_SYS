import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';
import AdminRoute from './components/AdminRoute';
import Spinner from './components/Spinner';

// Lazy-loaded page components for code splitting
const LoginPage = lazy(() => import('./pages/LoginPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const CasePage = lazy(() => import('./pages/CasePage'));
const ProductPage = lazy(() => import('./pages/ProductPage'));
const UserListPage = lazy(() => import('./pages/admin/UserListPage'));
const UserCreatePage = lazy(() => import('./pages/admin/UserCreatePage'));
const UserEditPage = lazy(() => import('./pages/admin/UserEditPage'));
const QuoteRequestPage = lazy(() => import('./pages/QuoteRequestPage'));

export default function App() {
  return (
    <Suspense fallback={<Spinner />}>
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
          <Route path="quote-requests" element={<QuoteRequestPage />} />
          <Route path="quote-requests/:id" element={<QuoteRequestPage />} />

          {/* Admin routes */}
          <Route path="admin/users" element={<AdminRoute><UserListPage /></AdminRoute>} />
          <Route path="admin/users/new" element={<AdminRoute><UserCreatePage /></AdminRoute>} />
          <Route path="admin/users/:id" element={<AdminRoute><UserEditPage /></AdminRoute>} />
        </Route>
      </Routes>
    </Suspense>
  );
}
