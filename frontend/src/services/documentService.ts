import { apiMethods } from './api';
import { Document, DocumentStatus, ParseResult, PaginatedResponse, ApiResponse } from '../types';

interface GetDocumentsParams {
  page?: number;
  pageSize?: number;
  filters?: {
    status?: DocumentStatus;
    search?: string;
    dateRange?: [string, string];
    userId?: string;
  };
}

interface ParseOptions {
  extractImages?: boolean;
  extractTables?: boolean;
  ocrLanguage?: string;
  outputFormat?: 'markdown' | 'json' | 'text';
}

export const documentService = {
  // 获取文档列表
  getDocuments: async (params: GetDocumentsParams): Promise<ApiResponse<PaginatedResponse<Document>>> => {
    const queryParams = new URLSearchParams();
    
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.pageSize) queryParams.append('pageSize', params.pageSize.toString());
    if (params.filters?.status) queryParams.append('status', params.filters.status);
    if (params.filters?.search) queryParams.append('search', params.filters.search);
    if (params.filters?.userId) queryParams.append('userId', params.filters.userId);
    if (params.filters?.dateRange) {
      queryParams.append('startDate', params.filters.dateRange[0]);
      queryParams.append('endDate', params.filters.dateRange[1]);
    }

    const response = await apiMethods.get<ApiResponse<PaginatedResponse<Document>>>(`/documents?${queryParams.toString()}`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 获取单个文档
  getDocument: async (id: string): Promise<ApiResponse<Document>> => {
    const response = await apiMethods.get<ApiResponse<Document>>(`/documents/${id}`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 上传文档
  uploadDocument: async (file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<Document>> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiMethods.upload<ApiResponse<Document>>('/documents/upload', formData, onProgress);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 批量上传文档
  uploadDocuments: async (files: File[], onProgress?: (progress: number) => void): Promise<ApiResponse<Document[]>> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await apiMethods.upload<ApiResponse<Document[]>>('/documents/batch-upload', formData, onProgress);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 解析文档
  parseDocument: async (id: string, options?: ParseOptions): Promise<ApiResponse<{ taskId: string }>> => {
    const response = await apiMethods.post<ApiResponse<{ taskId: string }>>(`/documents/${id}/parse`, options);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 获取解析结果
  getParseResult: async (id: string): Promise<ApiResponse<ParseResult>> => {
    const response = await apiMethods.get<ApiResponse<ParseResult>>(`/documents/${id}/parse-result`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 获取解析状态
  getParseStatus: async (id: string): Promise<ApiResponse<{ status: DocumentStatus; progress: number; error?: string }>> => {
    const response = await apiMethods.get<ApiResponse<{ status: DocumentStatus; progress: number; error?: string }>>(`/documents/${id}/parse-status`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 重新解析文档
  reparseDocument: async (id: string, options?: ParseOptions): Promise<ApiResponse<{ taskId: string }>> => {
    const response = await apiMethods.post<ApiResponse<{ taskId: string }>>(`/documents/${id}/reparse`, options);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 下载文档
  downloadDocument: async (id: string, format: 'original' | 'markdown' | 'json' | 'text' = 'original'): Promise<Blob> => {
    const response = await apiMethods.get(`/documents/${id}/download?format=${format}`, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  // 预览文档
  previewDocument: async (id: string): Promise<ApiResponse<{ previewUrl: string; contentType: string }>> => {
    const response = await apiMethods.get<ApiResponse<{ previewUrl: string; contentType: string }>>(`/documents/${id}/preview`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 删除文档
  deleteDocument: async (id: string): Promise<ApiResponse<void>> => {
    const response = await apiMethods.delete<ApiResponse<void>>(`/documents/${id}`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 批量删除文档
  deleteDocuments: async (ids: string[]): Promise<ApiResponse<void>> => {
    const response = await apiMethods.post<ApiResponse<void>>('/documents/batch-delete', { ids });
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 更新文档信息
  updateDocument: async (id: string, data: { name?: string; description?: string; tags?: string[] }): Promise<ApiResponse<Document>> => {
    const response = await apiMethods.put<ApiResponse<Document>>(`/documents/${id}`, data);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 获取文档统计信息
  getDocumentStats: async (): Promise<ApiResponse<{
    total: number;
    byStatus: Record<DocumentStatus, number>;
    totalSize: number;
    recentUploads: number;
    parseSuccessRate: number;
  }>> => {
    const response = await apiMethods.get<ApiResponse<{
      total: number;
      byStatus: Record<DocumentStatus, number>;
      totalSize: number;
      recentUploads: number;
      parseSuccessRate: number;
    }>>('/documents/stats');
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 搜索文档内容
  searchDocuments: async (query: string, filters?: {
    status?: DocumentStatus;
    dateRange?: [string, string];
    userId?: string;
  }): Promise<ApiResponse<{
    documents: Document[];
    highlights: Record<string, string[]>;
    total: number;
  }>> => {
    const queryParams = new URLSearchParams();
    queryParams.append('q', query);
    
    if (filters?.status) queryParams.append('status', filters.status);
    if (filters?.userId) queryParams.append('userId', filters.userId);
    if (filters?.dateRange) {
      queryParams.append('startDate', filters.dateRange[0]);
      queryParams.append('endDate', filters.dateRange[1]);
    }

    const response = await apiMethods.get<ApiResponse<{
      documents: Document[];
      highlights: Record<string, string[]>;
      total: number;
    }>>(`/documents/search?${queryParams.toString()}`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 获取支持的文件类型
  getSupportedFileTypes: async (): Promise<ApiResponse<{
    types: string[];
    maxSize: number;
    description: Record<string, string>;
  }>> => {
    const response = await apiMethods.get<ApiResponse<{
      types: string[];
      maxSize: number;
      description: Record<string, string>;
    }>>('/documents/supported-types');
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 验证文件
  validateFile: async (file: File): Promise<ApiResponse<{ valid: boolean; error?: string }>> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiMethods.upload<ApiResponse<{ valid: boolean; error?: string }>>('/documents/validate', formData);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 获取文档版本历史
  getDocumentVersions: async (id: string): Promise<ApiResponse<{
    versions: Array<{
      id: string;
      version: number;
      createdAt: string;
      size: number;
      changes: string;
    }>;
  }>> => {
    const response = await apiMethods.get<ApiResponse<{
      versions: Array<{
        id: string;
        version: number;
        createdAt: string;
        size: number;
        changes: string;
      }>;
    }>>(`/documents/${id}/versions`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },

  // 恢复文档版本
  restoreDocumentVersion: async (id: string, versionId: string): Promise<ApiResponse<Document>> => {
    const response = await apiMethods.post<ApiResponse<Document>>(`/documents/${id}/restore/${versionId}`);
    return {
      success: response.data.success,
      data: response.data.data,
      timestamp: response.data.timestamp,
      requestId: response.data.requestId
    };
  },
};