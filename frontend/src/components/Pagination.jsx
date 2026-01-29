/**
 * 재사용 가능한 페이지네이션 컴포넌트.
 * @param {number} page - 현재 페이지 (1부터 시작)
 * @param {number} totalPages - 전체 페이지 수
 * @param {function} onPageChange - 페이지 변경 콜백
 * @param {boolean} disabled - 비활성화 여부
 */
export default function Pagination({ page, totalPages, onPageChange, disabled = false }) {
  if (totalPages <= 1) return null;

  return (
    <div className="pagination">
      <button
        className="pagination-btn"
        onClick={() => onPageChange(1)}
        disabled={disabled || page === 1}
        title="첫 페이지"
      >
        «
      </button>
      <button
        className="pagination-btn"
        onClick={() => onPageChange(page - 1)}
        disabled={disabled || page === 1}
        title="이전 페이지"
      >
        ‹
      </button>
      <span className="pagination-info">
        {page} / {totalPages}
      </span>
      <button
        className="pagination-btn"
        onClick={() => onPageChange(page + 1)}
        disabled={disabled || page === totalPages}
        title="다음 페이지"
      >
        ›
      </button>
      <button
        className="pagination-btn"
        onClick={() => onPageChange(totalPages)}
        disabled={disabled || page === totalPages}
        title="마지막 페이지"
      >
        »
      </button>
    </div>
  );
}
