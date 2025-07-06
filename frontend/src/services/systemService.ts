import { apiMethods } from './api';
import { SystemInfo, SystemSettings, SystemStats, Notification, PaginatedResponse, ApiResponse } from '../types';

class SystemService {
  private baseURL = '/system';

  // 获取系统信息
  async getSystemInfo(): Promise<ApiResponse<SystemInfo>> {
    const data = await apiMethods.get<SystemInfo>(`${this.baseURL}/info`);
    return {
      success: true,
      data,
      message: 'System info retrieved successfully'
    };
  }

  // 获取系统设置
  async getSystemSettings(): Promise<ApiResponse<SystemSettings>> {
    const data = await apiMethods.get<SystemSettings>(`${this.baseURL}/settings`);
    return {
      success: true,
      data,
      message: 'System settings retrieved successfully'
    };
  }

  // 更新系统设置
  async updateSystemSettings(settings: Partial<SystemSettings>): Promise<ApiResponse<SystemSettings>> {
    const data = await apiMethods.put<SystemSettings>(`${this.baseURL}/settings`, settings);
    return {
      success: true,
      data,
      message: 'System settings updated successfully'
    };
  }

  // 获取系统统计
  async getSystemStats(): Promise<ApiResponse<SystemStats>> {
    const data = await apiMethods.get<SystemStats>(`${this.baseURL}/stats`);
    return {
      success: true,
      data,
      message: 'System stats retrieved successfully'
    };
  }

  // 检查系统健康状态
  async checkHealth(): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/health`);
    return {
      success: true,
      data,
      message: 'Health check completed successfully'
    };
  }

  // 获取系统日志
  async getSystemLogs(params: {
    page?: number;
    pageSize?: number;
    level?: 'debug' | 'info' | 'warn' | 'error';
    service?: string;
    dateRange?: [string, string];
  } = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    const data = await apiMethods.get<PaginatedResponse<any>>(`${this.baseURL}/logs`, {
      params: {
        page: params.page || 1,
        pageSize: params.pageSize || 50,
        level: params.level,
        service: params.service,
        startDate: params.dateRange?.[0],
        endDate: params.dateRange?.[1],
      },
    });
    return {
      success: true,
      data,
      message: 'System logs retrieved successfully'
    };
  }

  // 获取通知列表
  async getNotifications(params: {
    page?: number;
    pageSize?: number;
    unreadOnly?: boolean;
  } = {}): Promise<ApiResponse<PaginatedResponse<Notification>>> {
    const data = await apiMethods.get<PaginatedResponse<Notification>>(
      `${this.baseURL}/notifications`,
      {
        params: {
          page: params.page || 1,
          pageSize: params.pageSize || 20,
          unreadOnly: params.unreadOnly || false,
        },
      }
    );
    return {
      success: true,
      data,
      message: 'Notifications retrieved successfully'
    };
  }

  // 标记通知为已读
  async markNotificationAsRead(notificationId: string): Promise<ApiResponse<void>> {
    await apiMethods.put<void>(
      `${this.baseURL}/notifications/${notificationId}/read`
    );
    return {
      success: true,
      data: undefined,
      message: 'Notification marked as read successfully'
    };
  }

  // 标记所有通知为已读
  async markAllNotificationsAsRead(): Promise<ApiResponse<void>> {
    await apiMethods.put<void>(`${this.baseURL}/notifications/read-all`);
    return {
      success: true,
      data: undefined,
      message: 'All notifications marked as read successfully'
    };
  }

  // 删除通知
  async deleteNotification(notificationId: string): Promise<ApiResponse<void>> {
    await apiMethods.delete<void>(
      `${this.baseURL}/notifications/${notificationId}`
    );
    return {
      success: true,
      data: undefined,
      message: 'Notification deleted successfully'
    };
  }

  // 创建通知
  async createNotification(notification: {
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message: string;
    userId?: string;
    data?: Record<string, any>;
  }): Promise<ApiResponse<Notification>> {
    const data = await apiMethods.post<Notification>(
      `${this.baseURL}/notifications`,
      notification
    );
    return {
      success: true,
      data,
      message: 'Notification created successfully'
    };
  }

  // 重启服务
  async restartService(serviceName: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/services/${serviceName}/restart`);
    return {
      success: true,
      data,
      message: `Service ${serviceName} restarted successfully`
    };
  }

  // 停止服务
  async stopService(serviceName: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/services/${serviceName}/stop`);
    return {
      success: true,
      data,
      message: `Service ${serviceName} stopped successfully`
    };
  }

  // 启动服务
  async startService(serviceName: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/services/${serviceName}/start`);
    return {
      success: true,
      data,
      message: `Service ${serviceName} started successfully`
    };
  }

  // 获取服务状态
  async getServiceStatus(serviceName?: string): Promise<ApiResponse<any>> {
    const url = serviceName
      ? `${this.baseURL}/services/${serviceName}/status`
      : `${this.baseURL}/services/status`;
    const data = await apiMethods.get<any>(url);
    return {
      success: true,
      data,
      message: 'Service status retrieved successfully'
    };
  }

  // 备份系统
  async createBackup(options: {
    includeDatabase?: boolean;
    includeFiles?: boolean;
    includeSettings?: boolean;
    description?: string;
  } = {}): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/backup`, options);
    return {
      success: true,
      data,
      message: 'Backup created successfully'
    };
  }

  // 获取备份列表
  async getBackups(params: {
    page?: number;
    pageSize?: number;
  } = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    const data = await apiMethods.get<PaginatedResponse<any>>(`${this.baseURL}/backups`, {
      params: {
        page: params.page || 1,
        pageSize: params.pageSize || 10,
      },
    });
    return {
      success: true,
      data,
      message: 'Backups retrieved successfully'
    };
  }

  // 恢复备份
  async restoreBackup(backupId: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/backups/${backupId}/restore`);
    return {
      success: true,
      data,
      message: 'Backup restored successfully'
    };
  }

  // 删除备份
  async deleteBackup(backupId: string): Promise<ApiResponse<void>> {
    await apiMethods.delete<void>(`${this.baseURL}/backups/${backupId}`);
    return {
      success: true,
      data: undefined,
      message: 'Backup deleted successfully'
    };
  }

  // 下载备份
  async downloadBackup(backupId: string): Promise<Blob> {
    const response = await apiMethods.get(`${this.baseURL}/backups/${backupId}/download`, {
      responseType: 'blob',
    });
    return response;
  }

  // 清理系统
  async cleanupSystem(options: {
    cleanLogs?: boolean;
    cleanTempFiles?: boolean;
    cleanOldBackups?: boolean;
    daysToKeep?: number;
  } = {}): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/cleanup`, options);
    return {
      success: true,
      data,
      message: 'System cleanup completed successfully'
    };
  }

  // 获取系统配置
  async getSystemConfig(): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/config`);
    return {
      success: true,
      data,
      message: 'System config retrieved successfully'
    };
  }

  // 更新系统配置
  async updateSystemConfig(config: Record<string, any>): Promise<ApiResponse<any>> {
    const data = await apiMethods.put<any>(`${this.baseURL}/config`, config);
    return {
      success: true,
      data,
      message: 'System config updated successfully'
    };
  }

  // 获取系统监控数据
  async getMonitoringData(params: {
    metric: 'cpu' | 'memory' | 'disk' | 'network';
    timeRange: '1h' | '6h' | '24h' | '7d' | '30d';
    interval?: '1m' | '5m' | '15m' | '1h';
  }): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/monitoring`, {
      params,
    });
    return {
      success: true,
      data,
      message: 'Monitoring data retrieved successfully'
    };
  }

  // 设置系统维护模式
  async setMaintenanceMode(enabled: boolean, message?: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/maintenance`, {
      enabled,
      message,
    });
    return {
      success: true,
      data,
      message: `Maintenance mode ${enabled ? 'enabled' : 'disabled'} successfully`
    };
  }

  // 获取维护模式状态
  async getMaintenanceStatus(): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/maintenance/status`);
    return {
      success: true,
      data,
      message: 'Maintenance status retrieved successfully'
    };
  }

  // 发送测试邮件
  async sendTestEmail(email: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/test-email`, { email });
    return {
      success: true,
      data,
      message: 'Test email sent successfully'
    };
  }

  // 测试存储连接
  async testStorageConnection(): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/test-storage`);
    return {
      success: true,
      data,
      message: 'Storage connection test completed successfully'
    };
  }

  // 测试数据库连接
  async testDatabaseConnection(): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/test-database`);
    return {
      success: true,
      data,
      message: 'Database connection test completed successfully'
    };
  }

  // 获取系统版本信息
  async getVersionInfo(): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/version`);
    return {
      success: true,
      data,
      message: 'Version info retrieved successfully'
    };
  }

  // 检查更新
  async checkForUpdates(): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/check-updates`);
    return {
      success: true,
      data,
      message: 'Update check completed successfully'
    };
  }
}

export const systemService = new SystemService();
export default systemService;