import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Checkbox, Alert, Card, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined, EyeInvisibleOutlined, EyeTwoTone } from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store';
import { login } from '@/store/slices/authSlice';
import { LoginCredentials } from '@/types';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { loading, error, loginAttempts } = useAppSelector(state => state.auth);
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = async (values: LoginCredentials & { remember: boolean }) => {
    try {
      const { remember, ...credentials } = values;
      setRememberMe(remember);
      
      const result = await dispatch(login(credentials)).unwrap();
      
      if (result) {
        navigate('/', { replace: true });
      }
    } catch (error) {
      // 错误已在 Redux slice 中处理
      console.error('Login failed:', error);
    }
  };

  const isBlocked = loginAttempts >= 5;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <UserOutlined className="h-6 w-6 text-blue-600" />
          </div>
          <Title level={2} className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            登录您的账户
          </Title>
          <Text className="mt-2 text-center text-sm text-gray-600">
            欢迎使用 Ragflow-MinerU 集成平台
          </Text>
        </div>

        <Card className="shadow-lg">
          {error && (
            <Alert
              message="登录失败"
              description={error}
              type="error"
              showIcon
              className="mb-4"
            />
          )}

          {isBlocked && (
            <Alert
              message="账户已锁定"
              description="由于多次登录失败，您的账户已被临时锁定。请稍后再试或联系管理员。"
              type="warning"
              showIcon
              className="mb-4"
            />
          )}

          <Form
            form={form}
            name="login"
            onFinish={handleSubmit}
            layout="vertical"
            size="large"
            disabled={isBlocked}
          >
            <Form.Item
              name="username"
              label="用户名"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input
                prefix={<UserOutlined className="text-gray-400" />}
                placeholder="请输入用户名"
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined className="text-gray-400" />}
                placeholder="请输入密码"
                autoComplete="current-password"
                iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
              />
            </Form.Item>

            <Form.Item>
              <div className="flex items-center justify-between">
                <Form.Item name="remember" valuePropName="checked" noStyle>
                  <Checkbox>记住我</Checkbox>
                </Form.Item>
                <Link
                  to="/auth/forgot-password"
                  className="text-blue-600 hover:text-blue-500 text-sm"
                >
                  忘记密码？
                </Link>
              </div>
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                disabled={isBlocked}
                className="w-full h-10"
              >
                {loading ? '登录中...' : '登录'}
              </Button>
            </Form.Item>
          </Form>

          <div className="text-center mt-4">
            <Text className="text-gray-600">
              还没有账户？{' '}
              <Link to="/auth/register" className="text-blue-600 hover:text-blue-500">
                立即注册
              </Link>
            </Text>
          </div>
        </Card>

        <div className="text-center">
          <Space direction="vertical" size="small">
            <Text className="text-xs text-gray-500">
              登录即表示您同意我们的
              <Link to="/terms" className="text-blue-600 hover:text-blue-500 mx-1">
                服务条款
              </Link>
              和
              <Link to="/privacy" className="text-blue-600 hover:text-blue-500 mx-1">
                隐私政策
              </Link>
            </Text>
            <Text className="text-xs text-gray-400">
              © 2024 Ragflow-MinerU 集成平台. 保留所有权利.
            </Text>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;