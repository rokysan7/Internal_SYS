/**
 * Quote request content card.
 * Displays the main quote request text (multi-line).
 */
export default function QuoteRequestCard({ content, otherRequest }) {
  return (
    <div className="card">
      <div className="section-title">Quote Request</div>
      <pre style={{
        fontSize: '0.9rem', color: '#334155', lineHeight: 1.6,
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
        margin: 0, fontFamily: 'inherit',
      }}>
        {content}
      </pre>
    </div>
  );
}
