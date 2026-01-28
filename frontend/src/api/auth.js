import client from './client';

/** 로그인 (JWT 토큰 반환) */
export const login = (email, password) =>
  client.post('/auth/login', { email, password });

/** 현재 사용자 정보 조회 */
export const getMe = () =>
  client.get('/auth/me');
