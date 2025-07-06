import { apiMethods } from './api';
import { User, LoginCredentials, RegisterData, ApiResponse } from '../types';

interface LoginResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresIn: number;
}

interface RefreshTokenResponse {
  token: string;
  expiresIn: number;
}

export const authService = {
  // 用户登录
  login: async (credentials: LoginCredentials): Promise<ApiResponse<LoginResponse>> => {
    const data = await apiMethods.post<LoginResponse>('/auth/login', credentials);
    return {
      success: true,
      data: {
        user: data.user,
        token: data.token,
        refreshToken: data.refreshToken,
        expiresIn: data.expiresIn
      },
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 用户注册
  register: async (registerData: RegisterData): Promise<ApiResponse<User>> => {
    const data = await apiMethods.post<User>('/auth/register', registerData);
    return {
      success: true,
      data,
      message: 'Registration successful'
    };
  },

  // 用户登出
  logout: async (): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>('/auth/logout');
    return {
      success: true,
      data: undefined,
      message: 'Logout successful'
    };
  },

  // 刷新 token
  refreshToken: async (refreshToken: string): Promise<ApiResponse<RefreshTokenResponse>> => {
    const data = await apiMethods.post<RefreshTokenResponse>('/auth/refresh', {
      refreshToken,
    });
    return {
      success: true,
      data,
      message: 'Token refreshed successfully'
    };
  },

  // 获取当前用户信息
  getCurrentUser: async (): Promise<ApiResponse<User>> => {
    const data = await apiMethods.get<User>('/auth/me');
    return {
      success: true,
      data,
      message: 'Current user retrieved successfully'
    };
  },

  // 检查用户名是否可用
  checkUsername: async (username: string): Promise<ApiResponse<{ available: boolean }>> => {
    const data = await apiMethods.get<{ available: boolean }>(`/auth/check-username?username=${username}`);
    return {
      success: true,
      data,
      message: 'Username availability checked successfully'
    };
  },

  // 检查邮箱是否可用
  checkEmail: async (email: string): Promise<ApiResponse<{ available: boolean }>> => {
    const data = await apiMethods.get<{ available: boolean }>(`/auth/check-email?email=${email}`);
    return {
      success: true,
      data,
      message: 'Email availability checked successfully'
    };
  },

  // 发送密码重置邮件
  forgotPassword: async (email: string): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>('/auth/forgot-password', { email });
    return {
      success: true,
      data: undefined,
      message: 'Password reset email sent successfully'
    };
  },

  // 重置密码
  resetPassword: async (token: string, newPassword: string): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>('/auth/reset-password', {
      token,
      newPassword,
    });
    return {
      success: true,
      data: undefined,
      message: 'Password reset successfully'
    };
  },

  // 修改密码
  changePassword: async (currentPassword: string, newPassword: string): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>('/auth/change-password', {
      currentPassword,
      newPassword,
    });
    return {
      success: true,
      data: undefined,
      message: 'Password changed successfully'
    };
  },

  // 验证 token 有效性
  validateToken: async (): Promise<ApiResponse<{ valid: boolean; user?: User }>> => {
    const data = await apiMethods.get<{ valid: boolean; user?: User }>('/auth/validate');
    return {
      success: true,
      data,
      message: 'Token validated successfully'
    };
  },

  // 启用两步验证
  enableTwoFactor: async (): Promise<ApiResponse<{ qrCode: string; secret: string }>> => {
    const data = await apiMethods.post<{ qrCode: string; secret: string }>('/auth/2fa/enable');
    return {
      success: true,
      data,
      message: 'Two-factor authentication enabled successfully'
    };
  },

  // 确认两步验证
  confirmTwoFactor: async (token: string): Promise<ApiResponse<{ backupCodes: string[] }>> => {
    const data = await apiMethods.post<{ backupCodes: string[] }>('/auth/2fa/confirm', { token });
    return {
      success: true,
      data,
      message: 'Two-factor authentication confirmed successfully'
    };
  },

  // 禁用两步验证
  disableTwoFactor: async (password: string): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>('/auth/2fa/disable', { password });
    return {
      success: true,
      data: undefined,
      message: 'Two-factor authentication disabled successfully'
    };
  },

  // 验证两步验证码
  verifyTwoFactor: async (token: string): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>('/auth/2fa/verify', { token });
    return {
      success: true,
      data: undefined,
      message: 'Two-factor authentication verified successfully'
    };
  },
} as const;
