import React, { useState } from 'react';
import { Card, Form, Input, Button, message, Steps, Result } from 'antd';
import { MailOutlined, ArrowLeftOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { authService } from '@/services/authService';

const { Step } = Steps;

interface ForgotPasswordForm {
  email: string;
}

const ForgotPasswordPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [email, setEmail] = useState('');

  const handleSubmit = async (values: ForgotPasswordForm) => {
    setLoading(true);
    try {
      await authService.forgotPassword(values.email);
      setEmail(values.email);
      setCurrentStep(1);
      message.success('密码重置邮件已发送');
    } catch (error: any) {
      message.error(error.response?.data?.message || '发送失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Card className="w-full max-w-md mx-auto">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold text-gray-900">忘记密码</h1>
              <p className="text-gray-600 mt-2">
                请输入您的邮箱地址，我们将向您发送密码重置链接
              </p>
            </div>

            <Form
              form={form}
              onFinish={handleSubmit}
              layout="vertical"
              size="large"
            >
              <Form.Item
                name="email"
                label="邮箱地址"
                rules={[
                  { required: true, message: '请输入邮箱地址' },
                  { type: 'email', message: '请输入有效的邮箱地址' },
                ]}
              >
                <Input
                  prefix={<MailOutlined />}
                  placeholder="请输入您的邮箱地址"
                  autoComplete="email"
                />
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  className="w-full"
                >
                  发送重置邮件
                </Button>
              </Form.Item>
            </Form>

            <div className="text-center mt-4">
              <Link
                to="/auth/login"
                className="text-blue-600 hover:text-blue-500 flex items-center justify-center"
              >
                <ArrowLeftOutlined className="mr-1" />
                返回登录
              </Link>
            </div>
          </Card>
        );

      case 1:
        return (
          <Card className="w-full max-w-md mx-auto">
            <Result
              icon={<CheckCircleOutlined className="text-green-500" />}
              title="邮件已发送"
              subTitle={
                <div className="text-gray-600">
                  <p>我们已向 <strong>{email}</strong> 发送了密码重置邮件</p>
                  <p className="mt-2">请检查您的邮箱并点击邮件中的链接来重置密码</p>
                </div>
              }
              extra={[
                <Button key="resend" onClick={() => setCurrentStep(0)}>
                  重新发送
                </Button>,
                <Button key="login" type="primary">
                  <Link to="/auth/login">返回登录</Link>
                </Button>,
              ]}
            />

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">没有收到邮件？</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 请检查垃圾邮件文件夹</li>
                <li>• 确认邮箱地址是否正确</li>
                <li>• 邮件可能需要几分钟才能到达</li>
              </ul>
            </div>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8">
          <Steps current={currentStep} size="small">
            <Step title="输入邮箱" />
            <Step title="邮件发送" />
          </Steps>
        </div>
        {renderStepContent()}
      </div>
    </div>
  );
};

export default ForgotPasswordPage;