import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from './store';
import { getCurrentUser } from './store/slices/authSlice';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';

// 布局组件
import AuthLayout from './components/layouts/AuthLayout';
import MainLayout from './components/layouts/MainLayout';

// 页面组件
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import DocumentsPage from './pages/documents/DocumentsPage';
// import DocumentDetailPage from './pages/documents/DocumentDetailPage'; // 暂时注释，该组件尚未创建
import UsersPage from './pages/users/UsersPage';
import ProfilePage from './pages/profile/ProfilePage';
import SettingsPage from './pages/settings/SettingsPage';

// 工具组件
import ProtectedRoute from './components/common/ProtectedRoute';
import LoadingSpinner from './components/common/LoadingSpinner';
import NotificationContainer from './components/common/NotificationContainer';
import ErrorBoundary from './components/common/ErrorBoundary';

const App: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, loading: authLoading, token } = useAppSelector(state => state.auth);
  const { theme: currentTheme, language } = useAppSelector(state => state.ui);

  // 应用初始化
  useEffect(() => {
    // 如果有 token，尝试获取当前用户信息
    if (token && !isAuthenticated) {
      dispatch(getCurrentUser());
    }
  }, [dispatch, token, isAuthenticated]);

  // 主题配置
  const themeConfig = {
    algorithm: currentTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6,
      wireframe: false,
    },
  };

  // 语言配置
  const locale = language === 'en-US' ? enUS : zhCN;

  // 如果正在加载认证状态，显示加载页面
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" tip="正在加载..." />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <ConfigProvider theme={themeConfig} locale={locale}>
        <div className={`app ${currentTheme}`}>
          <Routes>
            {/* 认证相关路由 */}
            <Route path="/auth" element={<AuthLayout />}>
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
              <Route path="forgot-password" element={<ForgotPasswordPage />} />
              <Route index element={<Navigate to="login" replace />} />
            </Route>

            {/* 主应用路由 */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              {/* 仪表板 */}
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />

              {/* 文档管理 */}
              <Route path="documents" element={<DocumentsPage />} />
              {/* <Route path="documents/:id" element={<DocumentDetailPage />} /> */} {/* 暂时注释，该组件尚未创建 */}

              {/* 用户管理 */}
              <Route
                path="users"
                element={
                  <ProtectedRoute requiredPermissions={['user:read']}>
                    <UsersPage />
                  </ProtectedRoute>
                }
              />

              {/* 个人资料 */}
              <Route path="profile" element={<ProfilePage />} />

              {/* 系统设置 */}
              <Route
                path="settings"
                element={
                  <ProtectedRoute requiredPermissions={['system:manage']}>
                    <SettingsPage />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* 未匹配路由重定向 */}
            <Route
              path="*"
              element={
                isAuthenticated ? (
                  <Navigate to="/dashboard" replace />
                ) : (
                  <Navigate to="/auth/login" replace />
                )
              }
            />
          </Routes>

          {/* 全局通知容器 */}
          <NotificationContainer />
        </div>
      </ConfigProvider>
    </ErrorBoundary>
  );
};

export default App;