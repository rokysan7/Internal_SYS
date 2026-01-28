import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// JWT 토큰 자동 첨부
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
