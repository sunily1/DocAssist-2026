// 인수인계용: 인증 상태/프로필 상태 관리 스토어
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api/axios';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  profile_settings?: any;
  created_at?: string;
  last_login_at?: string;
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token') || sessionStorage.getItem('token'));
  const user = ref<User | null>(null);
  const isAuthenticated = computed(() => !!token.value);

  function clearAuthStorage() {
    for (const storage of [localStorage, sessionStorage]) {
      storage.removeItem('token');
      storage.removeItem('role');
    }
  }

  function currentAuthStorage() {
    return localStorage.getItem('token') ? localStorage : sessionStorage;
  }

  async function login(email: string, password: string, remember = false): Promise<boolean> {
    try {
      // OAuth2PasswordRequestForm은 폼 데이터를 기대합니다
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      
      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      token.value = response.data.access_token;
      if (token.value) {
        clearAuthStorage();
        const storage = remember ? localStorage : sessionStorage;
        storage.setItem('token', token.value);
        await fetchUser();
      }
      return true;
    } catch (error) {
      console.error('Login failed', error);
      throw error;
    }
  }

  async function signup(userData: { email: string; password: string; name: string }) {
    try {
      await api.post('/auth/signup', userData);
      return true;
    } catch (error) {
      console.error('Signup failed', error);
      throw error;
    }
  }

  async function fetchUser() {
    if (!token.value) return;
    try {
      const response = await api.get('/users/me');
      user.value = response.data;
      // role 저장 (Router 가드용)
      if (user.value?.role) {
        currentAuthStorage().setItem('role', user.value.role);
      }
    } catch (error: any) {
      console.error('Fetch user failed', error);
      const status = error?.response?.status;
      if (status === 401 || status === 403) {
        logout();
      }
    }
  }

  async function updateUser(data: Partial<User> & { profile_settings?: any }) {
    try {
      const response = await api.patch('/users/me', data);
      user.value = response.data;
      if (user.value?.profile_settings) {
        localStorage.setItem('profile_settings', JSON.stringify(user.value.profile_settings));
      }
      if (user.value?.profile_settings?.ui?.theme) {
        localStorage.setItem('theme', user.value.profile_settings.ui.theme);
      }
      if (user.value?.profile_settings?.ui?.fontSize) {
        localStorage.setItem('font_size', user.value.profile_settings.ui.fontSize);
      }
      if (user.value?.profile_settings?.ui?.customFontSize) {
        localStorage.setItem('custom_font_size', String(user.value.profile_settings.ui.customFontSize));
      }
      return true;
    } catch (error) {
      console.error('Update user failed', error);
      throw error;
    }
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    try {
      await api.put('/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      return true;
    } catch (error) {
      console.error('Change password failed', error);
      throw error;
    }
  }

  function logout() {
    token.value = null;
    user.value = null;
    clearAuthStorage();
  }

  return { token, user, isAuthenticated, login, signup, fetchUser, updateUser, changePassword, logout };
});
