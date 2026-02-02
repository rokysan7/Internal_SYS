import client from './client';

/** License 단건 조회 */
export const getLicense = (id) =>
  client.get(`/licenses/${id}`);

/** License 생성 */
export const createLicense = (data) =>
  client.post('/licenses', data);

/** License 수정 (ADMIN only) */
export const updateLicense = (id, data) =>
  client.put(`/licenses/${id}`, data);

/** License 삭제 (ADMIN only) */
export const deleteLicense = (id) =>
  client.delete(`/licenses/${id}`);

/** License 메모 목록 조회 */
export const getLicenseMemos = (licenseId) =>
  client.get(`/licenses/${licenseId}/memos`);
