import client from './client';

/** Quote Request 목록 조회 (pagination + filters: status, search) */
export const getQuoteRequests = (params = {}) => {
  const { page = 1, page_size = 20, ...filters } = params;
  return client.get('/quote-requests/', { params: { page, page_size, ...filters } });
};

/** Quote Request 단건 조회 */
export const getQuoteRequest = (id) =>
  client.get(`/quote-requests/${id}`);

/** Quote Request 상태 변경 (PATCH) */
export const updateQuoteRequestStatus = (id, status) =>
  client.patch(`/quote-requests/${id}/status`, { status });

/** Quote Request 담당자 설정 (PUT) */
export const updateQuoteRequestAssignees = (id, assigneeIds) =>
  client.put(`/quote-requests/${id}/assignees`, { assignee_ids: assigneeIds });

/** Quote Request 삭제 */
export const deleteQuoteRequest = (id) =>
  client.delete(`/quote-requests/${id}`);

/** 기본 담당자 조회 */
export const getDefaultAssignees = () =>
  client.get('/quote-requests/settings/default-assignees');

/** 기본 담당자 일괄 설정 */
export const setDefaultAssignees = (assigneeIds) =>
  client.put('/quote-requests/settings/default-assignees', { assignee_ids: assigneeIds });

/** 댓글 목록 조회 */
export const getQuoteRequestComments = (qrId) =>
  client.get(`/quote-requests/${qrId}/comments`);

/** 댓글 작성 */
export const createQuoteRequestComment = (qrId, data) =>
  client.post(`/quote-requests/${qrId}/comments`, data);

/** 댓글 삭제 */
export const deleteQuoteRequestComment = (qrId, commentId) =>
  client.delete(`/quote-requests/${qrId}/comments/${commentId}`);
