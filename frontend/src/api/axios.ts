// 인수인계용: 공통 Axios 인스턴스(인증 토큰/에러 처리)
import axios from 'axios';

// 백엔드 URL
// Vite 프록시를 활용하기 위해 상대 경로를 사용합니다.
const baseURL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 토큰 추가를 위한 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 에러 처리를 위한 응답 인터셉터
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    if (status === 401 || (status === 403 && detail === 'Could not validate credentials')) {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('role');
    }
    return Promise.reject(error);
  }
);

export default api;
