import axios from 'axios';

// HTTPS 환경에서는 Vite 프록시를 통해 같은 출처로 API 호출 (Mixed Content 방지)
// HTTP 환경에서는 직접 백엔드 호출
const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (window.location.protocol === 'https:' ? '' : 'http://localhost:8002');

const client = axios.create({
  baseURL: API_BASE,
});

/**
 * Decode JWT payload without external library.
 * Returns null if the token is malformed.
 */
function decodeJwtPayload(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

/**
 * Check if a JWT token is expired (with 30-second buffer).
 */
function isTokenExpired(token) {
  const payload = decodeJwtPayload(token);
  if (!payload || !payload.exp) return false;
  return payload.exp * 1000 < Date.now() - 30_000;
}

// JWT token auto-attach with client-side expiry check
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    if (isTokenExpired(token)) {
      localStorage.removeItem('access_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(new axios.Cancel('Token expired'));
    }
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 응답 시 자동 로그아웃
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');

      // Redirect to login page (avoid redirect loop if already on login)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default client;
