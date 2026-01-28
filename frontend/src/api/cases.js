import client from './client';

/** CS Case 목록 조회 (필터 지원: status, assignee_id, product_id) */
export const getCases = (params = {}) =>
  client.get('/cases', { params });

/** CS Case 단건 조회 */
export const getCase = (id) =>
  client.get(`/cases/${id}`);

/** CS Case 생성 */
export const createCase = (data) =>
  client.post('/cases', data);

/** CS Case 수정 (PUT) */
export const updateCase = (id, data) =>
  client.put(`/cases/${id}`, data);

/** CS Case 상태 변경 (PATCH) */
export const updateCaseStatus = (id, status) =>
  client.patch(`/cases/${id}/status`, { status });

/** 유사 문의 검색 */
export const getSimilarCases = (query) =>
  client.get('/cases/similar', { params: { query } });

/** 댓글 목록 조회 */
export const getComments = (caseId) =>
  client.get(`/cases/${caseId}/comments`);

/** 댓글 작성 */
export const createComment = (caseId, data) =>
  client.post(`/cases/${caseId}/comments`, data);

/** 체크리스트 목록 조회 */
export const getChecklists = (caseId) =>
  client.get(`/cases/${caseId}/checklists`);

/** 체크리스트 항목 추가 */
export const createChecklist = (caseId, data) =>
  client.post(`/cases/${caseId}/checklists`, data);

/** 체크리스트 항목 토글 */
export const updateChecklist = (checklistId, is_done) =>
  client.patch(`/checklists/${checklistId}`, { is_done });

/** 통계 조회 (by: assignee | status | time) */
export const getStatistics = (by) =>
  client.get('/cases/statistics', { params: { by } });
