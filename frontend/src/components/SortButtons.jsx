/**
 * 재사용 가능한 정렬 버튼 컴포넌트.
 * @param {Array} options - 정렬 옵션 배열 [{ key: 'name', label: '이름' }, ...]
 * @param {string} currentSort - 현재 정렬 기준
 * @param {string} currentOrder - 현재 정렬 순서 ('asc' | 'desc')
 * @param {function} onSortChange - 정렬 변경 콜백 (sort, order)
 */
export default function SortButtons({ options, currentSort, currentOrder, onSortChange }) {
  const handleClick = (key) => {
    if (currentSort === key) {
      onSortChange(key, currentOrder === 'asc' ? 'desc' : 'asc');
    } else {
      onSortChange(key, 'asc');
    }
  };

  return (
    <div className="sort-buttons">
      {options.map((opt) => (
        <button
          key={opt.key}
          className={`sort-btn ${currentSort === opt.key ? 'active' : ''}`}
          onClick={() => handleClick(opt.key)}
        >
          {opt.label}
          {currentSort === opt.key && (
            <span className="sort-arrow">{currentOrder === 'asc' ? '↑' : '↓'}</span>
          )}
        </button>
      ))}
    </div>
  );
}
