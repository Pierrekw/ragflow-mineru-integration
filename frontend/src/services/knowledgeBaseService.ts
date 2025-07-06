import { apiMethods } from './api';
import { KnowledgeBase, CreateKnowledgeBaseForm, UpdateKnowledgeBaseForm, PaginatedResponse, ApiResponse } from '../types';

class KnowledgeBaseService {
  private baseURL = '/knowledge-bases';

  // 获取知识库列表
  async getKnowledgeBases(params: {
    page?: number;
    pageSize?: number;
    name?: string;
    status?: string;
    userId?: string;
    dateRange?: [string, string];
  } = {}): Promise<ApiResponse<PaginatedResponse<KnowledgeBase>>> {
    const data = await apiMethods.get<PaginatedResponse<KnowledgeBase>>(this.baseURL, {
      params: {
        page: params.page || 1,
        pageSize: params.pageSize || 10,
        name: params.name,
        status: params.status,
        userId: params.userId,
        startDate: params.dateRange?.[0],
        endDate: params.dateRange?.[1],
      },
    });
    return {
      success: true,
      data,
      message: 'Knowledge bases retrieved successfully'
    };
  }

  // 根据ID获取知识库详情
  async getKnowledgeBaseById(id: string): Promise<ApiResponse<KnowledgeBase>> {
    const data = await apiMethods.get<KnowledgeBase>(`${this.baseURL}/${id}`);
    return {
      success: true,
      data,
      message: 'Knowledge base retrieved successfully'
    };
  }

  // 创建知识库
  async createKnowledgeBase(data: CreateKnowledgeBaseForm): Promise<ApiResponse<KnowledgeBase>> {
    const result = await apiMethods.post<KnowledgeBase>(this.baseURL, data);
    return {
      success: true,
      data: result,
      message: 'Knowledge base created successfully'
    };
  }

  // 更新知识库
  async updateKnowledgeBase(id: string, data: UpdateKnowledgeBaseForm): Promise<ApiResponse<KnowledgeBase>> {
    const result = await apiMethods.put<KnowledgeBase>(`${this.baseURL}/${id}`, data);
    return {
      success: true,
      data: result,
      message: 'Knowledge base updated successfully'
    };
  }

  // 删除知识库
  async deleteKnowledgeBase(id: string): Promise<ApiResponse<void>> {
    await apiMethods.delete<void>(`${this.baseURL}/${id}`);
    return {
      success: true,
      data: undefined,
      message: 'Knowledge base deleted successfully'
    };
  }

  // 添加文档到知识库
  async addDocument(knowledgeBaseId: string, documentId: string): Promise<ApiResponse<KnowledgeBase>> {
    const data = await apiMethods.post<KnowledgeBase>(
      `${this.baseURL}/${knowledgeBaseId}/documents`,
      { documentId }
    );
    return {
      success: true,
      data,
      message: 'Document added to knowledge base successfully'
    };
  }

  // 从知识库移除文档
  async removeDocument(knowledgeBaseId: string, documentId: string): Promise<ApiResponse<void>> {
    await apiMethods.delete<void>(
      `${this.baseURL}/${knowledgeBaseId}/documents/${documentId}`
    );
    return {
      success: true,
      data: undefined,
      message: 'Document removed from knowledge base successfully'
    };
  }

  // 获取知识库文档列表
  async getDocuments(knowledgeBaseId: string, params: {
    page?: number;
    pageSize?: number;
    search?: string;
    status?: string;
  } = {}): Promise<ApiResponse<PaginatedResponse<any>>> {
    const data = await apiMethods.get<PaginatedResponse<any>>(
      `${this.baseURL}/${knowledgeBaseId}/documents`,
      {
        params: {
          page: params.page || 1,
          pageSize: params.pageSize || 10,
          search: params.search,
          status: params.status,
        },
      }
    );
    return {
      success: true,
      data,
      message: 'Knowledge base documents retrieved successfully'
    };
  }

  // 搜索知识库
  async search(id: string, query: string, limit: number = 10): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/${id}/search`, {
      query,
      limit,
    });
    return {
      success: true,
      data,
      message: 'Search completed successfully'
    };
  }

  // 语义搜索
  async semanticSearch(id: string, query: string, params: {
    limit?: number;
    threshold?: number;
    includeMetadata?: boolean;
  } = {}): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/${id}/semantic-search`, {
      query,
      limit: params.limit || 10,
      threshold: params.threshold || 0.7,
      includeMetadata: params.includeMetadata || false,
    });
    return {
      success: true,
      data,
      message: 'Semantic search completed successfully'
    };
  }

  // 获取知识库统计信息
  async getStats(id: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/${id}/stats`);
    return {
      success: true,
      data,
      message: 'Knowledge base stats retrieved successfully'
    };
  }

  // 重建知识库索引
  async rebuildIndex(id: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/${id}/rebuild-index`);
    return {
      success: true,
      data,
      message: 'Knowledge base index rebuild started successfully'
    };
  }

  // 导出知识库
  async exportKnowledgeBase(id: string, format: 'json' | 'csv' | 'xlsx'): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/${id}/export`, {
      format,
    });
    return {
      success: true,
      data,
      message: 'Knowledge base export started successfully'
    };
  }

  // 导入知识库
  async importKnowledgeBase(file: File, options: {
    name: string;
    description?: string;
    mergeStrategy?: 'replace' | 'merge' | 'skip';
  }): Promise<ApiResponse<KnowledgeBase>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('options', JSON.stringify(options));

    const data = await apiMethods.post<KnowledgeBase>(
      `${this.baseURL}/import`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return {
      success: true,
      data,
      message: 'Knowledge base imported successfully'
    };
  }

  // 复制知识库
  async cloneKnowledgeBase(id: string, options: {
    name: string;
    description?: string;
    includeDocuments?: boolean;
  }): Promise<ApiResponse<KnowledgeBase>> {
    const data = await apiMethods.post<KnowledgeBase>(
      `${this.baseURL}/${id}/clone`,
      options
    );
    return {
      success: true,
      data,
      message: 'Knowledge base cloned successfully'
    };
  }

  // 分享知识库
  async shareKnowledgeBase(id: string, options: {
    users: string[];
    permission: 'read' | 'write' | 'admin';
    expiresAt?: string;
  }): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/${id}/share`, options);
    return {
      success: true,
      data,
      message: 'Knowledge base shared successfully'
    };
  }

  // 取消分享
  async unshareKnowledgeBase(id: string, userId: string): Promise<ApiResponse<void>> {
    await apiMethods.delete<void>(
      `${this.baseURL}/${id}/share/${userId}`
    );
    return {
      success: true,
      data: undefined,
      message: 'Knowledge base unshared successfully'
    };
  }

  // 获取分享列表
  async getSharedUsers(id: string): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/${id}/shared-users`);
    return {
      success: true,
      data,
      message: 'Shared users retrieved successfully'
    };
  }

  // 批量操作
  async batchOperation(operation: 'delete' | 'export' | 'rebuild', ids: string[]): Promise<ApiResponse<any>> {
    const data = await apiMethods.post<any>(`${this.baseURL}/batch`, {
      operation,
      ids,
    });
    return {
      success: true,
      data,
      message: `Batch ${operation} operation completed successfully`
    };
  }

  // 获取知识库模板
  async getTemplates(): Promise<ApiResponse<any>> {
    const data = await apiMethods.get<any>(`${this.baseURL}/templates`);
    return {
      success: true,
      data,
      message: 'Knowledge base templates retrieved successfully'
    };
  }

  // 从模板创建知识库
  async createFromTemplate(templateId: string, options: {
    name: string;
    description?: string;
  }): Promise<ApiResponse<KnowledgeBase>> {
    const data = await apiMethods.post<KnowledgeBase>(
      `${this.baseURL}/templates/${templateId}/create`,
      options
    );
    return {
      success: true,
      data,
      message: 'Knowledge base created from template successfully'
    };
  }
}

export const knowledgeBaseService = new KnowledgeBaseService();
export default knowledgeBaseService;