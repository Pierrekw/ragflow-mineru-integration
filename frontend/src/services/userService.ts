import { apiMethods } from './api';
import { User, UserRole, UserStatus, PaginatedResponse, ApiResponse } from '../types';

interface GetUsersParams {
  page?: number;
  pageSize?: number;
  filters?: {
    role?: UserRole;
    status?: UserStatus;
    search?: string;
  };
}

interface CreateUserData {
  username: string;
  email: string;
  password: string;
  role: UserRole;
  profile?: {
    firstName?: string;
    lastName?: string;
    avatar?: string;
  };
}

interface UpdateUserData {
  username?: string;
  email?: string;
  role?: UserRole;
  status?: UserStatus;
  profile?: {
    firstName?: string;
    lastName?: string;
    avatar?: string;
  };
}

export const userService = {
  // 获取用户列表
  getUsers: async (params: GetUsersParams): Promise<ApiResponse<PaginatedResponse<User>>> => {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.pageSize) queryParams.append('pageSize', params.pageSize.toString());
    if (params.filters?.role) queryParams.append('role', params.filters.role);
    if (params.filters?.status) queryParams.append('status', params.filters.status);
    if (params.filters?.search) queryParams.append('search', params.filters.search);

    const data = await apiMethods.get<PaginatedResponse<User>>(`/users?${queryParams.toString()}`);
    return {
      success: true,
      data,
      message: 'Users retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 获取单个用户
  getUser: async (id: string): Promise<ApiResponse<User>> => {
    const data = await apiMethods.get<User>(`/users/${id}`);
    return {
      success: true,
      data,
      message: 'User retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 创建用户
  createUser: async (userData: CreateUserData): Promise<ApiResponse<User>> => {
    const data = await apiMethods.post<User>('/users', userData);
    return {
      success: true,
      data,
      message: 'User created successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 更新用户
  updateUser: async (id: string, userData: UpdateUserData): Promise<ApiResponse<User>> => {
    const data = await apiMethods.put<User>(`/users/${id}`, userData);
    return {
      success: true,
      data,
      message: 'User updated successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 删除用户
  deleteUser: async (id: string): Promise<ApiResponse<void>> => {
    await apiMethods.delete<void>(`/users/${id}`);
    return {
      success: true,
      data: undefined,
      message: 'User deleted successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 批量删除用户
  deleteUsers: async (ids: string[]): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>('/users/batch-delete', { ids });
    return {
      success: true,
      data: undefined,
      message: 'Users deleted successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 更新用户状态
  updateUserStatus: async (id: string, status: UserStatus): Promise<ApiResponse<User>> => {
    const data = await apiMethods.patch<User>(`/users/${id}/status`, { status });
    return {
      success: true,
      data,
      message: 'User status updated successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 重置用户密码
  resetUserPassword: async (id: string, newPassword: string): Promise<ApiResponse<void>> => {
    await apiMethods.post<void>(`/users/${id}/reset-password`, { newPassword });
    return {
      success: true,
      data: undefined,
      message: 'User password reset successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 更新用户头像
  updateUserAvatar: async (id: string, file: File): Promise<ApiResponse<{ avatarUrl: string }>> => {
    const formData = new FormData();
    formData.append('avatar', file);
    
    const data = await apiMethods.upload<{ avatarUrl: string }>(`/users/${id}/avatar`, formData);
    return {
      success: true,
      data: {
        avatarUrl: data.avatarUrl
      },
      message: 'User avatar updated successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 获取用户权限
  getUserPermissions: async (id: string): Promise<ApiResponse<string[]>> => {
    const data = await apiMethods.get<string[]>(`/users/${id}/permissions`);
    return {
      success: true,
      data,
      message: 'User permissions retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 更新用户权限
  updateUserPermissions: async (id: string, permissions: string[]): Promise<ApiResponse<void>> => {
    await apiMethods.put<void>(`/users/${id}/permissions`, { permissions });
    return {
      success: true,
      data: undefined,
      message: 'User permissions updated successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 获取用户活动日志
  getUserActivityLog: async (id: string, params?: { page?: number; pageSize?: number }): Promise<ApiResponse<PaginatedResponse<any>>> => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.pageSize) queryParams.append('pageSize', params.pageSize.toString());

    const data = await apiMethods.get<PaginatedResponse<any>>(`/users/${id}/activity?${queryParams.toString()}`);
    return {
      success: true,
      data,
      message: 'User activity log retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 导出用户数据
  exportUsers: async (filters?: GetUsersParams['filters']): Promise<Blob> => {
    const queryParams = new URLSearchParams();
    if (filters?.role) queryParams.append('role', filters.role);
    if (filters?.status) queryParams.append('status', filters.status);
    if (filters?.search) queryParams.append('search', filters.search);

    const response = await apiMethods.get(`/users/export?${queryParams.toString()}`, {
      responseType: 'blob',
    });
    
    return response;
  },

  // 导入用户数据
  importUsers: async (file: File): Promise<ApiResponse<{ success: number; failed: number; errors: string[] }>> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const data = await apiMethods.upload<{ success: number; failed: number; errors: string[] }>('/users/import', formData);
    return {
      success: true,
      data: {
        success: data.success,
        failed: data.failed,
        errors: data.errors
      },
      message: 'Users imported successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },

  // 获取用户统计信息
  getUserStats: async (): Promise<ApiResponse<{
    total: number;
    active: number;
    inactive: number;
    byRole: Record<UserRole, number>;
    recentRegistrations: number;
  }>> => {
    const data = await apiMethods.get<{
      total: number;
      active: number;
      inactive: number;
      byRole: Record<UserRole, number>;
      recentRegistrations: number;
    }>('/users/stats');
    return {
      success: true,
      data: {
        total: data.total,
        active: data.active,
        inactive: data.inactive,
        byRole: data.byRole,
        recentRegistrations: data.recentRegistrations
      },
      message: 'User stats retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  },
};