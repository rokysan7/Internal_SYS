import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8002';

const client = axios.create({
  baseURL: API_BASE,
});

// JWT 토큰 자동 첨부
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
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
