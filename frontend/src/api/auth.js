import client from './client';

/** 로그인 (JWT 토큰 반환) */
export const login = (email, password) =>
  client.post('/auth/login', { email, password });

/** 현재 사용자 정보 조회 */
export const getMe = () =>
  client.get('/auth/me');

/** 비밀번호 변경 (본인) */
export const changePassword = (currentPassword, newPassword) =>
  client.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  });
