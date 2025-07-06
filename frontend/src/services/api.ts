import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { store } from '@/store';
import { logout } from '@/store/slices/authSlice';
import { addNotification } from '@/store/slices/uiSlice';

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: ((import.meta as any).env?.VITE_API_BASE_URL as string) || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加认证 token
    const state = store.getState();
    const token = state.auth.token;
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加请求 ID 用于追踪
    if (config.headers) {
      config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    return config;
  },
  (error: Error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    const { response, config } = error;
    
    // 处理网络错误
    if (!response) {
      store.dispatch(addNotification({
        type: 'error',
        title: '网络错误',
        message: '请检查网络连接',
      }));
      return Promise.reject(error);
    }

    const { status, data } = response;
    
    // 处理认证错误
    if (status === 401) {
      store.dispatch(logout());
      store.dispatch(addNotification({
        type: 'warning',
        title: '登录已过期',
        message: '请重新登录',
      }));
      return Promise.reject(error);
    }

    // 处理权限错误
    if (status === 403) {
      store.dispatch(addNotification({
        type: 'error',
        title: '权限不足',
        message: data?.message || '您没有权限执行此操作',
      }));
      return Promise.reject(error);
    }

    // 处理服务器错误
    if (status >= 500) {
      store.dispatch(addNotification({
        type: 'error',
        title: '服务器错误',
        message: data?.message || '服务器内部错误，请稍后重试',
      }));
      return Promise.reject(error);
    }

    // 处理其他错误
    if (status >= 400) {
      const message = data?.message || `请求失败 (${status})`;
      
      // 对于某些静默请求，不显示错误通知
      const silentUrls = ['/auth/refresh', '/auth/check'];
      const isSilentRequest = silentUrls.some(url => config?.url?.includes(url));
      
      if (!isSilentRequest) {
        store.dispatch(addNotification({
          type: 'error',
          title: '请求失败',
          message,
        }));
      }
    }

    return Promise.reject(error);
  }
);

// 文件上传专用实例
export const uploadApi: AxiosInstance = axios.create({
  baseURL: ((import.meta as any).env?.VITE_API_BASE_URL as string) || '/api',
  timeout: 300000, // 5分钟超时
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// 为上传实例添加认证拦截器
uploadApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const state = store.getState();
    const token = state.auth.token;
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 通用 API 方法
export const apiMethods = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.get(url, config);
  },
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.post(url, data, config);
  },
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.put(url, data, config);
  },
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.patch(url, data, config);
  },
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return api.delete(url, config);
  },
  
  upload: <T = any>(url: string, formData: FormData, onProgress?: (progress: number) => void): Promise<AxiosResponse<T>> => {
    return uploadApi.post(url, formData, {
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  },
};

export default api;