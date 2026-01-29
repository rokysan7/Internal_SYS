/**
 * Checklist management card.
 * @param {Object} props
 * @param {Array} props.checklists - List of checklist items
 * @param {string} props.value - Current input value
 * @param {Function} props.onChange - Input change handler
 * @param {Function} props.onAdd - Add item handler
 * @param {Function} props.onToggle - Toggle item handler
 */
export default function ChecklistCard({ checklists, value, onChange, onAdd, onToggle }) {
  return (
    <div className="card">
      <div className="section-title">Checklist</div>
      {checklists.length === 0 && (
        <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
          No items yet.
        </div>
      )}
      {checklists.map((item) => (
        <label
          key={item.id}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.35rem 0', fontSize: '0.85rem', cursor: 'pointer',
            color: item.is_done ? '#94a3b8' : '#334155',
            textDecoration: item.is_done ? 'line-through' : 'none',
          }}
        >
          <input
            type="checkbox"
            checked={item.is_done}
            onChange={() => onToggle(item)}
          />
          {item.content}
        </label>
      ))}
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <input
          type="text"
          placeholder="Add checklist item..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onAdd()}
          style={{
            flex: 1, padding: '0.4rem 0.6rem', border: '1px solid #cbd5e1',
            borderRadius: 4, fontSize: '0.82rem', fontFamily: 'inherit',
          }}
        />
        <button className="btn btn-secondary btn-sm" onClick={onAdd}>+</button>
      </div>
    </div>
  );
}
