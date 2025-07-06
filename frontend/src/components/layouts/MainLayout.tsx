import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Space,
  Badge,
  Switch,
  Breadcrumb,
} from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  FileTextOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  BellOutlined,
  MoonOutlined,
  SunOutlined,
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector, RootState } from '@/store';
import { logout } from '@/store/slices/authSlice';
import { toggleSidebar, setTheme } from '@/store/slices/uiSlice';

const { Header, Sider, Content } = Layout;

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state: RootState) => state.auth);
  const { sidebarCollapsed, theme, breadcrumbs, pageTitle } = useAppSelector((state: RootState) => state.ui);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/auth/login');
  };

  const handleThemeChange = (checked: boolean) => {
    dispatch(setTheme(checked ? 'dark' : 'light'));
  };

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/documents',
      icon: <FileTextOutlined />,
      label: '文档管理',
    },
    {
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '账户设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.startsWith('/documents')) return ['/documents'];
    if (path.startsWith('/users')) return ['/users'];
    if (path.startsWith('/settings')) return ['/settings'];
    return ['/dashboard'];
  };

  return (
    <Layout className="min-h-screen">
      <Sider
        trigger={null}
        collapsible
        collapsed={sidebarCollapsed}
        className="layout-sider"
        width={256}
      >
        <div className="flex items-center justify-center h-16 border-b border-gray-200 dark:border-gray-700">
          <div className="text-lg font-bold text-blue-600">
            {sidebarCollapsed ? 'RM' : 'Ragflow-MinerU'}
          </div>
        </div>
        
        <Menu
          theme={theme === 'dark' ? 'dark' : 'light'}
          mode="inline"
          selectedKeys={getSelectedKeys()}
          items={menuItems}
          onClick={handleMenuClick}
          className="border-r-0"
        />
      </Sider>
      
      <Layout>
        <Header className="layout-header px-4 flex items-center justify-between">
          <div className="flex items-center">
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => dispatch(toggleSidebar())}
              className="text-lg"
            />
            
            {breadcrumbs.length > 0 && (
              <Breadcrumb className="ml-4">
                {breadcrumbs.map((item: { path?: string; title: string }, index: number) => (
                  <Breadcrumb.Item key={index}>
                    {item.path ? (
                      <a onClick={() => navigate(item.path!)}>{item.title}</a>
                    ) : (
                      item.title
                    )}
                  </Breadcrumb.Item>
                ))}
              </Breadcrumb>
            )}
          </div>
          
          <Space size="middle">
            {/* 主题切换 */}
            <Space>
              <SunOutlined />
              <Switch
                checked={theme === 'dark'}
                onChange={handleThemeChange}
                size="small"
              />
              <MoonOutlined />
            </Space>
            
            {/* 通知 */}
            <Badge count={5} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                className="text-lg"
              />
            </Badge>
            
            {/* 用户菜单 */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
            >
              <Space className="cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 px-2 py-1 rounded">
                <Avatar
                  size="small"
                  src={user?.avatar}
                  icon={<UserOutlined />}
                />
                <span className="hidden sm:inline">
                  {user?.username}
                </span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        
        <Content className="layout-content">
          {pageTitle && (
            <div className="mb-4">
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {pageTitle}
              </h1>
            </div>
          )}
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;