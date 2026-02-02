import client from './client';

/** Product 메모 목록 조회 */
export const getProductMemos = (productId) =>
  client.get(`/products/${productId}/memos`);

/** Product 메모 작성 */
export const createProductMemo = (productId, data) =>
  client.post(`/products/${productId}/memos`, data);

/** Product 메모 삭제 */
export const deleteProductMemo = (memoId) =>
  client.delete(`/product-memos/${memoId}`);

/** License 메모 목록 조회 */
export const getLicenseMemos = (licenseId) =>
  client.get(`/licenses/${licenseId}/memos`);

/** License 메모 작성 */
export const createLicenseMemo = (licenseId, data) =>
  client.post(`/licenses/${licenseId}/memos`, data);

/** License 메모 삭제 */
export const deleteLicenseMemo = (memoId) =>
  client.delete(`/license-memos/${memoId}`);
