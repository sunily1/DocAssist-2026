// 인수인계용: 관리자 대시보드 API 호출 모듈
import api from './axios';

export interface MetricSlice {
  label: string;
  value: number;
  color?: string;
}

export interface ApiStatusItem {
  status: "ok" | "warn" | "bad" | string;
  label: string;
  message: string;
}

export interface AdminMetrics {
  users: number;
  docs: number;
  queue: number;
  qaToday: number;
  signups: number;
  loginsToday: number;
  activeUsers: number;
  uploadsToday: number;
  glossaryTerms: number;
  glossaryTermsToday: number;
  glossaryPinned: number;
  serviceUsage: MetricSlice[];
  satisfaction: MetricSlice[];
  devices: MetricSlice[];
  apiStatus: Record<string, ApiStatusItem>;
}

export interface UserItem {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface DocItem {
  id: string;
  title: string;
  file_type: string;
  status: string;
  created_at: string;
  user_id: string;
}

export default {
  async getMetrics(): Promise<{ data: AdminMetrics }> {
    return api.get('/admin/metrics');
  },
  
  async getUsers(params?: { skip?: number; limit?: number }) {
      return api.get<UserItem[]>('/admin/users', { params });
  },
  
  async getDocuments(params?: { skip?: number; limit?: number }) {
      return api.get<DocItem[]>('/admin/documents', { params });
  }
};
