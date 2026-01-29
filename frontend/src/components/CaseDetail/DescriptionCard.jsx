/**
 * Case description card component.
 * @param {Object} props
 * @param {string} props.content - Case description content
 */
export default function DescriptionCard({ content }) {
  return (
    <div className="card">
      <div className="section-title">Description</div>
      <p style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.6 }}>{content}</p>
    </div>
  );
}
