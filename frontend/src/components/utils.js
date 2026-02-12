/**
 * 공통 유틸리티 - 날짜 포맷, 상태/우선순위 뱃지
 */
import { CASE_STATUS, CASE_STATUS_LABEL } from '../constants/caseStatus';
import { PRIORITY } from '../constants/priority';

export function formatDate(iso) {
  if (!iso) return '-';
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

export function formatDateShort(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  });
}

export function statusBadgeClass(status) {
  if (status === CASE_STATUS.OPEN) return 'badge-open';
  if (status === CASE_STATUS.IN_PROGRESS) return 'badge-in-progress';
  if (status === CASE_STATUS.CANCEL) return 'badge-cancel';
  return 'badge-done';
}

export function statusLabel(status) {
  return CASE_STATUS_LABEL[status] || status;
}

export function priorityBadgeClass(priority) {
  if (priority === PRIORITY.HIGH) return 'badge-high';
  if (priority === PRIORITY.MEDIUM) return 'badge-medium';
  return 'badge-low';
}
