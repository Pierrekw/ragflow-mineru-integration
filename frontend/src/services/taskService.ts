import { apiMethods } from './api';
import { Task, CreateTaskForm, UpdateTaskForm, PaginatedResponse, ApiResponse } from '../types';

class TaskService {
  private baseURL = '/tasks';

  // 获取任务列表
  async getTasks(params: {
    page?: number;
    pageSize?: number;
    status?: string;
    type?: string;
    userId?: string;
    dateRange?: [string, string];
  } = {}): Promise<ApiResponse<PaginatedResponse<Task>>> {
    const response = await apiMethods.get<PaginatedResponse<Task>>(this.baseURL, {
      params: {
        page: params.page || 1,
        pageSize: params.pageSize || 10,
        status: params.status,
        type: params.type,
        userId: params.userId,
        startDate: params.dateRange?.[0],
        endDate: params.dateRange?.[1],
      },
    });
    return {
      success: true,
      data: response.data,
      message: 'Tasks retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()     
    };
  }

  // 根据ID获取任务详情
  async getTaskById(id: string): Promise<ApiResponse<Task>> {
    const response = await apiMethods.get<Task>(`${this.baseURL}/${id}`);
    return {
      success: true,
      data: response.data,
      message: 'Task retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 创建任务
  async createTask(data: CreateTaskForm): Promise<ApiResponse<Task>> {
    const response = await apiMethods.post<Task>(this.baseURL, data);
    return {
      success: true,
      data: response.data,
      message: 'Task created successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
      
    };
  }

  // 更新任务
  async updateTask(id: string, data: UpdateTaskForm): Promise<ApiResponse<Task>> {
    const response = await apiMethods.put<Task>(`${this.baseURL}/${id}`, data);
    return {
      success: true,
      data: response.data,
      message: 'Task updated successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
     };
  }

  // 删除任务
  async deleteTask(id: string): Promise<ApiResponse<void>> {
    const response = await apiMethods.delete<void>(`${this.baseURL}/${id}`);
    return {
      success: true,
      data: response.data,
      message: 'Task deleted successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 取消任务
  async cancelTask(id: string): Promise<ApiResponse<Task>> {
    const response = await apiMethods.post<Task>(`${this.baseURL}/${id}/cancel`);
    return {
      success: true,
      data: response.data,
      message: 'Task cancelled successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 重试任务
  async retryTask(id: string): Promise<ApiResponse<Task>> {
    const response = await apiMethods.post<Task>(`${this.baseURL}/${id}/retry`);
    return {
      success: true,
      data: response.data,
      message: 'Task retry initiated successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 获取任务日志
  async getTaskLogs(id: string, params: {
    page?: number;
    pageSize?: number;
    level?: 'debug' | 'info' | 'warn' | 'error';
  } = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    const response = await apiMethods.get<PaginatedResponse<any>>(
      `${this.baseURL}/${id}/logs`,
      {
        params: {
          page: params.page || 1,
          pageSize: params.pageSize || 50,
          level: params.level,
        },
      }
    );
    return {
      success: true,
      data: response.data,
      message: 'Task logs retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 获取任务统计
  async getTaskStats(params: {
    dateRange?: [string, string];
    groupBy?: 'day' | 'week' | 'month';
  } = {}): Promise<ApiResponse<any>> {
    const response = await apiMethods.get<any>(`${this.baseURL}/stats`, {
      params: {
        startDate: params.dateRange?.[0],
        endDate: params.dateRange?.[1],
        groupBy: params.groupBy || 'day',
      },
    });
    return {
      success: true,
      data: response.data,
      message: 'Task statistics retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 批量操作任务
  async batchOperation(operation: 'cancel' | 'retry' | 'delete', taskIds: string[]): Promise<ApiResponse<any>> {
    const response = await apiMethods.post<any>(`${this.baseURL}/batch`, {
      operation,
      taskIds,
    });
    return {
      success: true,
      data: response.data,
      message: `Batch ${operation} operation completed successfully`,
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 获取任务队列状态
  async getQueueStatus(): Promise<ApiResponse<any>> {
    const response = await apiMethods.get<any>(`${this.baseURL}/queue/status`);
    return {
      success: true,
      data: response.data,
      message: 'Queue status retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 清空任务队列
  async clearQueue(status?: string): Promise<ApiResponse<void>> {
    const response = await apiMethods.post<void>(`${this.baseURL}/queue/clear`, {
      status,
    });
    return {
      success: true,
      data: response.data,
      message: 'Queue cleared successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 暂停/恢复任务队列
  async toggleQueue(action: 'pause' | 'resume'): Promise<ApiResponse<void>> {
    const response = await apiMethods.post<void>(`${this.baseURL}/queue/${action}`);
    return {
      success: true,
      data: response.data,
      message: `Queue ${action}d successfully`,
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 获取任务类型配置
  async getTaskTypeConfig(): Promise<ApiResponse<any>> {
    const response = await apiMethods.get<any>(`${this.baseURL}/types/config`);
    return {
      success: true,
      data: response.data,
      message: 'Task type configuration retrieved successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }

  // 更新任务类型配置
  async updateTaskTypeConfig(type: string, config: any): Promise<ApiResponse<any>> {
    const response = await apiMethods.put<any>(`${this.baseURL}/types/${type}/config`, config);
    return {
      success: true,
      data: response.data,
      message: 'Task type configuration updated successfully',
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID()
    };
  }
}

export const taskService = new TaskService();
export default taskService;