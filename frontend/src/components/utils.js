/**
 * 공통 유틸리티 - 날짜 포맷, 상태/우선순위 뱃지
 */

export function formatDate(iso) {
  if (!iso) return '-';
  // 서버에서 UTC로 저장되므로 'Z' 붙여서 UTC로 파싱
  const utcIso = iso.endsWith('Z') ? iso : iso + 'Z';
  const d = new Date(utcIso);
  return d.toLocaleString('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
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
