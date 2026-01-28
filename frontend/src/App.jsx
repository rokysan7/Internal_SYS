import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import CasePage from './pages/CasePage';
import ProductPage from './pages/ProductPage';
import LicensePage from './pages/LicensePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="cases" element={<CasePage />} />
          <Route path="cases/:id" element={<CasePage />} />
          <Route path="cases/new" element={<CasePage />} />
          <Route path="products" element={<ProductPage />} />
          <Route path="licenses/:id" element={<LicensePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
