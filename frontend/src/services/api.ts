import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { ApiResponse, PaginatedResponse } from '@/types';

// Create axios instance with default configuration
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Generic API methods
export const apiClient = {
  get: <T>(url: string): Promise<ApiResponse<T>> =>
    api.get(url).then((response) => response.data),
  
  post: <T>(url: string, data?: any): Promise<ApiResponse<T>> =>
    api.post(url, data).then((response) => response.data),
  
  put: <T>(url: string, data?: any): Promise<ApiResponse<T>> =>
    api.put(url, data).then((response) => response.data),
  
  patch: <T>(url: string, data?: any): Promise<ApiResponse<T>> =>
    api.patch(url, data).then((response) => response.data),
  
  delete: <T>(url: string): Promise<ApiResponse<T>> =>
    api.delete(url).then((response) => response.data),
  
  getPaginated: <T>(url: string, params?: Record<string, any>): Promise<PaginatedResponse<T>> =>
    api.get(url, { params }).then((response) => response.data),
};

export default api;