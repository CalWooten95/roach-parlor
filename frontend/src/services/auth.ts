import axios from 'axios';
import { LoginCredentials, LoginResponse, User } from '../types/auth';
import { AUTH_STORAGE_KEYS, isTokenExpired } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
export const tokenStorage = {
  getToken: (): string | null => {
    return localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN);
  },
  
  setToken: (token: string): void => {
    localStorage.setItem(AUTH_STORAGE_KEYS.TOKEN, token);
  },
  
  getRefreshToken: (): string | null => {
    return localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN);
  },
  
  setRefreshToken: (token: string): void => {
    localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, token);
  },
  
  getUser: (): User | null => {
    const userStr = localStorage.getItem(AUTH_STORAGE_KEYS.USER);
    return userStr ? JSON.parse(userStr) : null;
  },
  
  setUser: (user: User): void => {
    localStorage.setItem(AUTH_STORAGE_KEYS.USER, JSON.stringify(user));
  },
  
  clearAll: (): void => {
    localStorage.removeItem(AUTH_STORAGE_KEYS.TOKEN);
    localStorage.removeItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(AUTH_STORAGE_KEYS.USER);
  },
};

// Add request interceptor to include auth token
authApi.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token refresh
authApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = tokenStorage.getRefreshToken();
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token } = response.data;
          tokenStorage.setToken(access_token);
          
          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return authApi(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        tokenStorage.clearAll();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export const authService = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await authApi.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    return response.data;
  },
  
  async logout(): Promise<void> {
    try {
      await authApi.post('/auth/logout');
    } catch (error) {
      // Even if logout fails on server, clear local storage
      console.warn('Logout request failed:', error);
    } finally {
      tokenStorage.clearAll();
    }
  },
  
  async refreshToken(): Promise<string> {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    
    return response.data.access_token;
  },
  
  async getCurrentUser(): Promise<User> {
    const response = await authApi.get<User>('/auth/me');
    return response.data;
  },
  
  isTokenExpired(token: string): boolean {
    return isTokenExpired(token);
  },
};

export default authApi;