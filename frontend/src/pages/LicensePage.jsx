import { useParams, Link } from 'react-router-dom';
import LicenseDetail from '../components/LicenseDetail';
import './pages.css';

export default function LicensePage() {
  const { id } = useParams();

  return (
    <div>
      <Link to="/products" className="back-link">← Back to Products</Link>
      <div className="page-header">
        <h1>License Detail</h1>
      </div>
      <LicenseDetail licenseId={id} />
    </div>
  );
}
