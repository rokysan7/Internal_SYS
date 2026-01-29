import client from './client';

/** Get users list with pagination */
export const getUsers = (page = 1, pageSize = 20, search = '', role = '') => {
  const params = { page, page_size: pageSize };
  if (search) params.search = search;
  if (role) params.role = role;
  return client.get('/admin/users', { params });
};

/** Create a new user */
export const createUser = (data) =>
  client.post('/admin/users', data);

/** Get a specific user */
export const getUser = (id) =>
  client.get(`/admin/users/${id}`);

/** Update a user */
export const updateUser = (id, data) =>
  client.put(`/admin/users/${id}`, data);

/** Delete (deactivate) a user */
export const deleteUser = (id) =>
  client.delete(`/admin/users/${id}`);

/** Reset user password (admin only) */
export const resetPassword = (id, newPassword) =>
  client.post(`/admin/users/${id}/reset-password`, { new_password: newPassword });
