import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { KnowledgeBase, CreateKnowledgeBaseForm, UpdateKnowledgeBaseForm } from '@/types';
import { knowledgeBaseService } from '@/services/knowledgeBaseService';

interface KnowledgeBaseState {
  knowledgeBases: KnowledgeBase[];
  currentKnowledgeBase: KnowledgeBase | null;
  loading: boolean;
  error: string | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
  filters: {
    name?: string;
    status?: string;
    userId?: string;
    dateRange?: [string, string];
  };
}

const initialState: KnowledgeBaseState = {
  knowledgeBases: [],
  currentKnowledgeBase: null,
  loading: false,
  error: null,
  pagination: {
    current: 1,
    pageSize: 10,
    total: 0,
  },
  filters: {},
};

// 异步 actions
export const fetchKnowledgeBases = createAsyncThunk(
  'knowledgeBase/fetchKnowledgeBases',
  async (params: {
    page?: number;
    pageSize?: number;
    name?: string;
    status?: string;
    userId?: string;
    dateRange?: [string, string];
  }, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseService.getKnowledgeBases(params);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取知识库列表失败');
    }
  }
);

export const fetchKnowledgeBaseById = createAsyncThunk(
  'knowledgeBase/fetchKnowledgeBaseById',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseService.getKnowledgeBaseById(id);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取知识库详情失败');
    }
  }
);

export const createKnowledgeBase = createAsyncThunk(
  'knowledgeBase/createKnowledgeBase',
  async (data: CreateKnowledgeBaseForm, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseService.createKnowledgeBase(data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '创建知识库失败');
    }
  }
);

export const updateKnowledgeBase = createAsyncThunk(
  'knowledgeBase/updateKnowledgeBase',
  async ({ id, data }: { id: string; data: UpdateKnowledgeBaseForm }, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseService.updateKnowledgeBase(id, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '更新知识库失败');
    }
  }
);

export const deleteKnowledgeBase = createAsyncThunk(
  'knowledgeBase/deleteKnowledgeBase',
  async (id: string, { rejectWithValue }) => {
    try {
      await knowledgeBaseService.deleteKnowledgeBase(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '删除知识库失败');
    }
  }
);

export const addDocumentToKnowledgeBase = createAsyncThunk(
  'knowledgeBase/addDocumentToKnowledgeBase',
  async ({ knowledgeBaseId, documentId }: { knowledgeBaseId: string; documentId: string }, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseService.addDocument(knowledgeBaseId, documentId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '添加文档到知识库失败');
    }
  }
);

export const removeDocumentFromKnowledgeBase = createAsyncThunk(
  'knowledgeBase/removeDocumentFromKnowledgeBase',
  async ({ knowledgeBaseId, documentId }: { knowledgeBaseId: string; documentId: string }, { rejectWithValue }) => {
    try {
      await knowledgeBaseService.removeDocument(knowledgeBaseId, documentId);
      return { knowledgeBaseId, documentId };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '从知识库移除文档失败');
    }
  }
);

export const searchKnowledgeBase = createAsyncThunk(
  'knowledgeBase/searchKnowledgeBase',
  async ({ id, query, limit }: { id: string; query: string; limit?: number }, { rejectWithValue }) => {
    try {
      const response = await knowledgeBaseService.search(id, query, limit);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '搜索知识库失败');
    }
  }
);

const knowledgeBaseSlice = createSlice({
  name: 'knowledgeBase',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCurrentKnowledgeBase: (state, action: PayloadAction<KnowledgeBase | null>) => {
      state.currentKnowledgeBase = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<KnowledgeBaseState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setPagination: (state, action: PayloadAction<Partial<KnowledgeBaseState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    updateKnowledgeBaseStatus: (state, action: PayloadAction<{ id: string; status: string }>) => {
      const { id, status } = action.payload;
      const kb = state.knowledgeBases.find(k => k.id === id);
      if (kb) {
        kb.status = status;
        kb.updatedAt = new Date().toISOString();
      }
      if (state.currentKnowledgeBase?.id === id) {
        state.currentKnowledgeBase.status = status;
        state.currentKnowledgeBase.updatedAt = new Date().toISOString();
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch Knowledge Bases
    builder
      .addCase(fetchKnowledgeBases.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchKnowledgeBases.fulfilled, (state, action) => {
        state.loading = false;
        state.knowledgeBases = action.payload.items;
        state.pagination = {
          current: action.payload.page,
          pageSize: action.payload.pageSize,
          total: action.payload.total,
        };
        state.error = null;
      })
      .addCase(fetchKnowledgeBases.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Fetch Knowledge Base By ID
    builder
      .addCase(fetchKnowledgeBaseById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchKnowledgeBaseById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentKnowledgeBase = action.payload;
        state.error = null;
      })
      .addCase(fetchKnowledgeBaseById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Create Knowledge Base
    builder
      .addCase(createKnowledgeBase.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createKnowledgeBase.fulfilled, (state, action) => {
        state.loading = false;
        state.knowledgeBases.unshift(action.payload);
        state.pagination.total += 1;
        state.error = null;
      })
      .addCase(createKnowledgeBase.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Update Knowledge Base
    builder
      .addCase(updateKnowledgeBase.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateKnowledgeBase.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.knowledgeBases.findIndex(kb => kb.id === action.payload.id);
        if (index !== -1) {
          state.knowledgeBases[index] = action.payload;
        }
        if (state.currentKnowledgeBase?.id === action.payload.id) {
          state.currentKnowledgeBase = action.payload;
        }
        state.error = null;
      })
      .addCase(updateKnowledgeBase.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Delete Knowledge Base
    builder
      .addCase(deleteKnowledgeBase.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteKnowledgeBase.fulfilled, (state, action) => {
        state.loading = false;
        state.knowledgeBases = state.knowledgeBases.filter(kb => kb.id !== action.payload);
        state.pagination.total -= 1;
        if (state.currentKnowledgeBase?.id === action.payload) {
          state.currentKnowledgeBase = null;
        }
        state.error = null;
      })
      .addCase(deleteKnowledgeBase.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Add Document to Knowledge Base
    builder
      .addCase(addDocumentToKnowledgeBase.fulfilled, (state, action) => {
        if (state.currentKnowledgeBase?.id === action.payload.id) {
          state.currentKnowledgeBase = action.payload;
        }
        const index = state.knowledgeBases.findIndex(kb => kb.id === action.payload.id);
        if (index !== -1) {
          state.knowledgeBases[index] = action.payload;
        }
      })
      .addCase(addDocumentToKnowledgeBase.rejected, (state, action) => {
        state.error = action.payload as string;
      })

    // Remove Document from Knowledge Base
    builder
      .addCase(removeDocumentFromKnowledgeBase.fulfilled, (state, action) => {
        const { knowledgeBaseId, documentId } = action.payload;
        if (state.currentKnowledgeBase?.id === knowledgeBaseId) {
          state.currentKnowledgeBase.documents = state.currentKnowledgeBase.documents?.filter(
            doc => doc.id !== documentId
          );
        }
        const kb = state.knowledgeBases.find(k => k.id === knowledgeBaseId);
        if (kb && kb.documents) {
          kb.documents = kb.documents.filter(doc => doc.id !== documentId);
        }
      })
      .addCase(removeDocumentFromKnowledgeBase.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const {
  clearError,
  setCurrentKnowledgeBase,
  setFilters,
  clearFilters,
  setPagination,
  updateKnowledgeBaseStatus,
} = knowledgeBaseSlice.actions;

export default knowledgeBaseSlice.reducer;