import client from './client';

/** License 단건 조회 */
export const getLicense = (id) =>
  client.get(`/licenses/${id}`);

/** License 생성 */
export const createLicense = (data) =>
  client.post('/licenses', data);

/** License 메모 목록 조회 */
export const getLicenseMemos = (licenseId) =>
  client.get(`/licenses/${licenseId}/memos`);
