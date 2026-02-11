import fs from 'fs';
import path from 'path';
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// HTTPS: mkcert로 생성한 인증서가 있으면 자동 적용
const keyPath = path.resolve(__dirname, '..', 'certs', 'key.pem');
const certPath = path.resolve(__dirname, '..', 'certs', 'cert.pem');
const httpsConfig =
  fs.existsSync(keyPath) && fs.existsSync(certPath)
    ? { key: fs.readFileSync(keyPath), cert: fs.readFileSync(certPath) }
    : undefined;

// API 경로 목록 (Vite proxy → FastAPI backend)
const apiPaths = [
  '/auth', '/admin', '/products', '/licenses', '/memos',
  '/cases', '/comments', '/checklists', '/notifications', '/push',
  '/product-memos', '/license-memos', '/tags',
];

// Proxy 설정:
// 1. HTML 요청(브라우저 새로고침)은 SPA로 전달
// 2. FastAPI 307 redirect의 Location 헤더를 상대 경로로 변환 (Mixed Content 방지)
function buildProxy(paths, target) {
  const proxy = {};
  for (const p of paths) {
    proxy[p] = {
      target,
      changeOrigin: true,
      bypass(req) {
        if (req.headers.accept?.includes('text/html')) {
          return '/index.html';
        }
      },
      configure(proxyServer) {
        proxyServer.on('proxyRes', (proxyRes) => {
          const location = proxyRes.headers['location'];
          if (location) {
            try {
              const url = new URL(location);
              proxyRes.headers['location'] = url.pathname + url.search;
            } catch { /* relative URL — keep as-is */ }
          }
        });
      },
    };
  }
  return proxy;
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    https: httpsConfig,
    host: '0.0.0.0',
    proxy: httpsConfig ? buildProxy(apiPaths, 'http://localhost:8002') : undefined,
  },
})
