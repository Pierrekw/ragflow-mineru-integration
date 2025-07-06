import React from 'react';
import { Outlet } from 'react-router-dom';
import { Layout } from 'antd';

const { Content } = Layout;

const AuthLayout: React.FC = () => {
  return (
    <Layout className="min-h-screen">
      <Content className="flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </Content>
    </Layout>
  );
};

export default AuthLayout;