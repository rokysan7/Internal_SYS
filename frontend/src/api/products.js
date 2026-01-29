import client from './client';

/** Product 목록 조회 (검색 지원) */
export const getProducts = (search) =>
  client.get('/products', { params: search ? { search } : {} });

/** Product 단건 조회 */
export const getProduct = (id) =>
  client.get(`/products/${id}`);

/** Product 생성 */
export const createProduct = (data) =>
  client.post('/products', data);

/** Product에 속한 License 목록 조회 */
export const getProductLicenses = (productId) =>
  client.get(`/products/${productId}/licenses`);

/** CSV 파일로 Product + License 일괄 등록 */
export const bulkUploadProducts = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return client.post('/products/bulk', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
