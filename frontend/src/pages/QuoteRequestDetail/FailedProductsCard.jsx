/**
 * Failed products table card.
 * Displays the list of products that failed parsing.
 */
export default function FailedProductsCard({ products }) {
  if (!products || products.length === 0) return null;

  // Extract column headers from the first product's keys
  const headers = Object.keys(products[0]);

  return (
    <div className="card">
      <div className="section-title">Failed Products ({products.length})</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {headers.map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {products.map((p, idx) => (
              <tr key={idx}>
                {headers.map((h) => (
                  <td key={h} style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem' }}>
                    {p[h] ?? '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
