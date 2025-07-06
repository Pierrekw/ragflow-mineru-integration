import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { SystemInfo, SystemSettings, SystemStats, Notification } from '@/types';
import { systemService } from '@/services/systemService';

interface SystemState {
  info: SystemInfo | null;
  settings: SystemSettings | null;
  stats: SystemStats | null;
  notifications: Notification[];
  loading: boolean;
  error: string | null;
  healthStatus: {
    status: 'healthy' | 'warning' | 'error' | 'unknown';
    lastCheck: string | null;
    services: {
      database: boolean;
      redis: boolean;
      storage: boolean;
      mineru: boolean;
      ragflow: boolean;
    };
  };
}

const initialState: SystemState = {
  info: null,
  settings: null,
  stats: null,
  notifications: [],
  loading: false,
  error: null,
  healthStatus: {
    status: 'unknown',
    lastCheck: null,
    services: {
      database: false,
      redis: false,
      storage: false,
      mineru: false,
      ragflow: false,
    },
  },
};

// 异步 actions
export const fetchSystemInfo = createAsyncThunk(
  'system/fetchSystemInfo',
  async (_, { rejectWithValue }) => {
    try {
      const response = await systemService.getSystemInfo();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取系统信息失败');
    }
  }
);

export const fetchSystemSettings = createAsyncThunk(
  'system/fetchSystemSettings',
  async (_, { rejectWithValue }) => {
    try {
      const response = await systemService.getSystemSettings();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取系统设置失败');
    }
  }
);

export const updateSystemSettings = createAsyncThunk(
  'system/updateSystemSettings',
  async (settings: Partial<SystemSettings>, { rejectWithValue }) => {
    try {
      const response = await systemService.updateSystemSettings(settings);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '更新系统设置失败');
    }
  }
);

export const fetchSystemStats = createAsyncThunk(
  'system/fetchSystemStats',
  async (_, { rejectWithValue }) => {
    try {
      const response = await systemService.getSystemStats();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取系统统计失败');
    }
  }
);

export const checkSystemHealth = createAsyncThunk(
  'system/checkSystemHealth',
  async (_, { rejectWithValue }) => {
    try {
      const response = await systemService.checkHealth();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '检查系统健康状态失败');
    }
  }
);

export const fetchNotifications = createAsyncThunk(
  'system/fetchNotifications',
  async (params: { page?: number; pageSize?: number; unreadOnly?: boolean }, { rejectWithValue }) => {
    try {
      const response = await systemService.getNotifications(params);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '获取通知失败');
    }
  }
);

export const markNotificationAsRead = createAsyncThunk(
  'system/markNotificationAsRead',
  async (notificationId: string, { rejectWithValue }) => {
    try {
      await systemService.markNotificationAsRead(notificationId);
      return notificationId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '标记通知为已读失败');
    }
  }
);

export const markAllNotificationsAsRead = createAsyncThunk(
  'system/markAllNotificationsAsRead',
  async (_, { rejectWithValue }) => {
    try {
      await systemService.markAllNotificationsAsRead();
      return true;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '标记所有通知为已读失败');
    }
  }
);

export const deleteNotification = createAsyncThunk(
  'system/deleteNotification',
  async (notificationId: string, { rejectWithValue }) => {
    try {
      await systemService.deleteNotification(notificationId);
      return notificationId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '删除通知失败');
    }
  }
);

export const restartService = createAsyncThunk(
  'system/restartService',
  async (serviceName: string, { rejectWithValue }) => {
    try {
      const response = await systemService.restartService(serviceName);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || '重启服务失败');
    }
  }
);

const systemSlice = createSlice({
  name: 'system',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.unshift(action.payload);
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    updateHealthStatus: (state, action: PayloadAction<Partial<SystemState['healthStatus']>>) => {
      state.healthStatus = { ...state.healthStatus, ...action.payload };
    },
    updateServiceStatus: (state, action: PayloadAction<{ service: keyof SystemState['healthStatus']['services']; status: boolean }>) => {
      const { service, status } = action.payload;
      state.healthStatus.services[service] = status;
      
      // 更新整体健康状态
      const services = Object.values(state.healthStatus.services);
      const allHealthy = services.every(s => s);
      const anyUnhealthy = services.some(s => !s);
      
      if (allHealthy) {
        state.healthStatus.status = 'healthy';
      } else if (anyUnhealthy) {
        state.healthStatus.status = 'error';
      } else {
        state.healthStatus.status = 'warning';
      }
      
      state.healthStatus.lastCheck = new Date().toISOString();
    },
  },
  extraReducers: (builder) => {
    // Fetch System Info
    builder
      .addCase(fetchSystemInfo.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSystemInfo.fulfilled, (state, action) => {
        state.loading = false;
        state.info = action.payload;
        state.error = null;
      })
      .addCase(fetchSystemInfo.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Fetch System Settings
    builder
      .addCase(fetchSystemSettings.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSystemSettings.fulfilled, (state, action) => {
        state.loading = false;
        state.settings = action.payload;
        state.error = null;
      })
      .addCase(fetchSystemSettings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Update System Settings
    builder
      .addCase(updateSystemSettings.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateSystemSettings.fulfilled, (state, action) => {
        state.loading = false;
        state.settings = action.payload;
        state.error = null;
      })
      .addCase(updateSystemSettings.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Fetch System Stats
    builder
      .addCase(fetchSystemStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSystemStats.fulfilled, (state, action) => {
        state.loading = false;
        state.stats = action.payload;
        state.error = null;
      })
      .addCase(fetchSystemStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })

    // Check System Health
    builder
      .addCase(checkSystemHealth.fulfilled, (state, action) => {
        state.healthStatus = {
          ...action.payload,
          lastCheck: new Date().toISOString(),
        };
      })
      .addCase(checkSystemHealth.rejected, (state, action) => {
        state.error = action.payload as string;
        state.healthStatus.status = 'error';
        state.healthStatus.lastCheck = new Date().toISOString();
      })

    // Fetch Notifications
    builder
      .addCase(fetchNotifications.fulfilled, (state, action) => {
        state.notifications = action.payload.items;
      })
      .addCase(fetchNotifications.rejected, (state, action) => {
        state.error = action.payload as string;
      })

    // Mark Notification as Read
    builder
      .addCase(markNotificationAsRead.fulfilled, (state, action) => {
        const notification = state.notifications.find(n => n.id === action.payload);
        if (notification) {
          notification.isRead = true;
        }
      })
      .addCase(markNotificationAsRead.rejected, (state, action) => {
        state.error = action.payload as string;
      })

    // Mark All Notifications as Read
    builder
      .addCase(markAllNotificationsAsRead.fulfilled, (state) => {
        state.notifications.forEach(notification => {
          notification.isRead = true;
        });
      })
      .addCase(markAllNotificationsAsRead.rejected, (state, action) => {
        state.error = action.payload as string;
      })

    // Delete Notification
    builder
      .addCase(deleteNotification.fulfilled, (state, action) => {
        state.notifications = state.notifications.filter(n => n.id !== action.payload);
      })
      .addCase(deleteNotification.rejected, (state, action) => {
        state.error = action.payload as string;
      })

    // Restart Service
    builder
      .addCase(restartService.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(restartService.fulfilled, (state) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(restartService.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  clearError,
  addNotification,
  removeNotification,
  updateHealthStatus,
  updateServiceStatus,
} = systemSlice.actions;

export default systemSlice.reducer;