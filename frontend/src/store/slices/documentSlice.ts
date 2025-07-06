import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Document, DocumentStatus, ParseResult, PaginatedResponse } from '@/types';
import { documentService } from '@/services/documentService';

interface DocumentState {
  documents: Document[];
  currentDocument: Document | null;
  parseResults: ParseResult[];
  total: number;
  loading: boolean;
  uploading: boolean;
  parsing: boolean;
  error: string | null;
  filters: {
    status?: DocumentStatus;
    search?: string;
    dateRange?: [string, string];
  };
  pagination: {
    page: number;
    pageSize: number;
  };
  uploadProgress: number;
}

const initialState: DocumentState = {
  documents: [],
  currentDocument: null,
  parseResults: [],
  total: 0,
  loading: false,
  uploading: false,
  parsing: false,
  error: null,
  filters: {},
  pagination: {
    page: 1,
    pageSize: 10,
  },
  uploadProgress: 0,
};

// 异步 actions
export const fetchDocuments = createAsyncThunk(
  'document/fetchDocuments',
  async (params: { page?: number; pageSize?: number; filters?: any }, { rejectWithValue }) => {
    try {
      const response = await documentService.getDocuments(params);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取文档列表失败');
    }
  }
);

export const uploadDocument = createAsyncThunk(
  'document/uploadDocument',
  async (file: File, { rejectWithValue, dispatch }) => {
    try {
      const response = await documentService.uploadDocument(file, (progress) => {
        dispatch(setUploadProgress(progress));
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '文档上传失败');
    }
  }
);

export const parseDocument = createAsyncThunk(
  'document/parseDocument',
  async (documentId: string, { rejectWithValue }) => {
    try {
      const response = await documentService.parseDocument(documentId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '文档解析失败');
    }
  }
);

export const getParseResult = createAsyncThunk(
  'document/getParseResult',
  async (documentId: string, { rejectWithValue }) => {
    try {
      const response = await documentService.getParseResult(documentId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取解析结果失败');
    }
  }
);

export const deleteDocument = createAsyncThunk(
  'document/deleteDocument',
  async (id: string, { rejectWithValue }) => {
    try {
      await documentService.deleteDocument(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '删除文档失败');
    }
  }
);

export const downloadDocument = createAsyncThunk(
  'document/downloadDocument',
  async ({ id, format }: { id: string; format: string }, { rejectWithValue }) => {
    try {
      const response = await documentService.downloadDocument(id, format);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '下载文档失败');
    }
  }
);

const documentSlice = createSlice({
  name: 'document',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<Partial<DocumentState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    setPagination: (state, action: PayloadAction<Partial<DocumentState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    setCurrentDocument: (state, action: PayloadAction<Document | null>) => {
      state.currentDocument = action.payload;
    },
    setUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateDocumentStatus: (state, action: PayloadAction<{ id: string; status: DocumentStatus }>) => {
      const document = state.documents.find(doc => doc.id === action.payload.id);
      if (document) {
        document.status = action.payload.status;
      }
      if (state.currentDocument?.id === action.payload.id) {
        state.currentDocument.status = action.payload.status;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch Documents
    builder
      .addCase(fetchDocuments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.loading = false;
        state.documents = action.payload.items;
        state.total = action.payload.total;
        state.pagination.page = action.payload.page;
        state.pagination.pageSize = action.payload.pageSize;
      })
      .addCase(fetchDocuments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Upload Document
    builder
      .addCase(uploadDocument.pending, (state) => {
        state.uploading = true;
        state.error = null;
        state.uploadProgress = 0;
      })
      .addCase(uploadDocument.fulfilled, (state, action) => {
        state.uploading = false;
        state.uploadProgress = 100;
        state.documents.unshift(action.payload);
        state.total += 1;
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.uploading = false;
        state.uploadProgress = 0;
        state.error = action.payload as string;
      })

    // Parse Document
    builder
      .addCase(parseDocument.pending, (state) => {
        state.parsing = true;
        state.error = null;
      })
      .addCase(parseDocument.fulfilled, (state, action) => {
        state.parsing = false;
        const document = state.documents.find(doc => doc.id === action.payload.documentId);
        if (document) {
          document.status = 'parsing';
        }
      })
      .addCase(parseDocument.rejected, (state, action) => {
        state.parsing = false;
        state.error = action.payload as string;
      })

    // Get Parse Result
    builder
      .addCase(getParseResult.fulfilled, (state, action) => {
        const existingIndex = state.parseResults.findIndex(result => result.documentId === action.payload.documentId);
        if (existingIndex !== -1) {
          state.parseResults[existingIndex] = action.payload;
        } else {
          state.parseResults.push(action.payload);
        }
      })
      .addCase(getParseResult.rejected, (state, action) => {
        state.error = action.payload as string;
      })

    // Delete Document
    builder
      .addCase(deleteDocument.fulfilled, (state, action) => {
        state.documents = state.documents.filter(doc => doc.id !== action.payload);
        state.parseResults = state.parseResults.filter(result => result.documentId !== action.payload);
        state.total -= 1;
        if (state.currentDocument?.id === action.payload) {
          state.currentDocument = null;
        }
      })
      .addCase(deleteDocument.rejected, (state, action) => {
        state.error = action.payload as string;
      })

    // Download Document
    builder
      .addCase(downloadDocument.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const {
  setFilters,
  setPagination,
  setCurrentDocument,
  setUploadProgress,
  clearError,
  updateDocumentStatus,
} = documentSlice.actions;

export default documentSlice.reducer;