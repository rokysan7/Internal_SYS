import client from './client';

/** CS Case 목록 조회 (pagination + filters: status, assignee_id, product_id) */
export const getCases = (params = {}) => {
  const { page = 1, page_size = 20, ...filters } = params;
  return client.get('/cases', { params: { page, page_size, ...filters } });
};

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

/** CS Case 삭제 */
export const deleteCase = (id) =>
  client.delete(`/cases/${id}`);

/** 유사 문의 검색 (TF-IDF + tag similarity) */
export const getSimilarCases = ({ title, content = '', tags = [] }) =>
  client.get('/cases/similar', { params: { title, content, tags } });

/** 특정 케이스의 유사 케이스 조회 */
export const getSimilarCasesById = (caseId) =>
  client.get(`/cases/${caseId}/similar`);

/** 댓글 목록 조회 */
export const getComments = (caseId) =>
  client.get(`/cases/${caseId}/comments/`);

/** 댓글 작성 */
export const createComment = (caseId, data) =>
  client.post(`/cases/${caseId}/comments/`, data);

/** 댓글 삭제 */
export const deleteComment = (caseId, commentId) =>
  client.delete(`/cases/${caseId}/comments/${commentId}`);

/** 체크리스트 목록 조회 */
export const getChecklists = (caseId) =>
  client.get(`/cases/${caseId}/checklists`);

/** 체크리스트 항목 추가 */
export const createChecklist = (caseId, data) =>
  client.post(`/cases/${caseId}/checklists`, data);

/** 체크리스트 항목 토글 */
export const updateChecklist = (checklistId, is_done) =>
  client.patch(`/checklists/${checklistId}`, { is_done });

/** 통계 조회 (by: assignee | status | time, optional period, date, assignee) */
export const getStatistics = (by, { period, targetDate, assigneeId } = {}) =>
  client.get('/cases/statistics', { params: { by, period: period || undefined, target_date: targetDate || undefined, assignee_id: assigneeId || undefined } });

/** 현재 사용자의 상태별 케이스 수 조회 (날짜별) */
export const getMyProgress = (targetDate) =>
  client.get('/cases/my-progress', { params: { target_date: targetDate || undefined } });

/** 담당자로 배정 가능한 사용자 목록 */
export const getAssignees = () =>
  client.get('/auth/users/assignees');
