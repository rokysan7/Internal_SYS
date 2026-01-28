/**
 * 공통 유틸리티 - 날짜 포맷, 상태/우선순위 뱃지
 */

export function formatDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

export function statusBadgeClass(status) {
  if (status === 'OPEN') return 'badge-open';
  if (status === 'IN_PROGRESS') return 'badge-in-progress';
  return 'badge-done';
}

export function statusLabel(status) {
  if (status === 'IN_PROGRESS') return 'In Progress';
  if (status === 'OPEN') return 'Open';
  return 'Done';
}

export function priorityBadgeClass(priority) {
  if (priority === 'HIGH') return 'badge-high';
  if (priority === 'MEDIUM') return 'badge-medium';
  return 'badge-low';
}
