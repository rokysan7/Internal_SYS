import client from './client';

/** Product 목록 조회 (검색, 페이지네이션, 정렬 지원) */
export const getProducts = ({ search, page = 1, pageSize = 25, sort = 'name', order = 'asc' } = {}) =>
  client.get('/products', {
    params: {
      ...(search && { search }),
      page,
      page_size: pageSize,
      sort,
      order,
    },
  });

/** Product 단건 조회 */
export const getProduct = (id) =>
  client.get(`/products/${id}`);

/** Product 생성 */
export const createProduct = (data) =>
  client.post('/products', data);

/** Product에 속한 License 목록 조회 */
export const getProductLicenses = (productId) =>
  client.get(`/products/${productId}/licenses`);

/** Get all products without pagination (for dropdowns) */
export const getAllProducts = () =>
  client.get('/products/all');

/** CSV 파일로 Product + License 일괄 등록 */
export const bulkUploadProducts = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return client.post('/products/bulk', formData);
};

/** Product 수정 (ADMIN only) */
export const updateProduct = (id, data) =>
  client.put(`/products/${id}`, data);

/** Product 삭제 (ADMIN only) */
export const deleteProduct = (id) =>
  client.delete(`/products/${id}`);
