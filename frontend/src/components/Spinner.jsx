/**
 * Reusable loading spinner component.
 * @param {Object} props
 * @param {string} [props.text] - Optional loading text (default: 'Loading...')
 */
export default function Spinner({ text = 'Loading...' }) {
  return (
    <div className="loading">
      <div className="loading-spinner" />
      {text && <span>{text}</span>}
    </div>
  );
}
