import React, { useState } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  Alert,
  message,
  Steps,
  Row,
  Col,
  Checkbox,
  Select,
  Upload,
  Avatar,
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  UploadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store';
import { register } from '@/store/slices/authSlice';
import type { RegisterData } from '@/types';

const { Title, Text } = Typography;
const { Step } = Steps;
const { Option } = Select;

interface RegisterFormData extends RegisterData {
  confirmPassword: string;
  agreement: boolean;
  emailCode?: string;
  phoneCode?: string;
}

const RegisterPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { loading, error } = useAppSelector(state => state.auth);
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [emailCodeSent, setEmailCodeSent] = useState(false);
  const [phoneCodeSent, setPhoneCodeSent] = useState(false);
  const [emailCountdown, setEmailCountdown] = useState(0);
  const [phoneCountdown, setPhoneCountdown] = useState(0);
  const [avatar, setAvatar] = useState<string>('');

  // 发送邮箱验证码
  const sendEmailCode = async () => {
    try {
      const email = form.getFieldValue('email');
      if (!email) {
        message.error('请先输入邮箱地址');
        return;
      }
      
      // TODO: 调用发送邮箱验证码 API
      setEmailCodeSent(true);
      setEmailCountdown(60);
      message.success('验证码已发送到您的邮箱');
      
      // 倒计时
      const timer = setInterval(() => {
        setEmailCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error) {
      message.error('发送验证码失败');
    }
  };

  // 发送手机验证码
  const sendPhoneCode = async () => {
    try {
      const phone = form.getFieldValue('phone');
      if (!phone) {
        message.error('请先输入手机号码');
        return;
      }
      
      // TODO: 调用发送手机验证码 API
      setPhoneCodeSent(true);
      setPhoneCountdown(60);
      message.success('验证码已发送到您的手机');
      
      // 倒计时
      const timer = setInterval(() => {
        setPhoneCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (error) {
      message.error('发送验证码失败');
    }
  };

  // 下一步
  const handleNext = async () => {
    try {
      if (currentStep === 0) {
        // 验证基本信息
        await form.validateFields(['username', 'email', 'password', 'confirmPassword']);
      } else if (currentStep === 1) {
        // 验证验证码
        await form.validateFields(['emailCode', 'phoneCode']);
      }
      setCurrentStep(prev => prev + 1);
    } catch (error) {
      // 验证失败
    }
  };

  // 上一步
  const handlePrev = () => {
    setCurrentStep(prev => prev - 1);
  };

  // 提交注册
  const handleSubmit = async (values: RegisterFormData) => {
    try {
      const { confirmPassword, agreement, emailCode, phoneCode, ...registerData } = values;
      
      if (avatar) {
        registerData.avatar = avatar;
      }
      
      await dispatch(register(registerData)).unwrap();
      message.success('注册成功！请登录您的账户');
      navigate('/auth/login');
    } catch (error) {
      // 错误已在 Redux 中处理
    }
  };

  // 头像上传
  const handleAvatarChange = (info: any) => {
    if (info.file.status === 'done') {
      setAvatar(info.file.response.url);
      message.success('头像上传成功');
    } else if (info.file.status === 'error') {
      message.error('头像上传失败');
    }
  };

  const steps = [
    {
      title: '基本信息',
      description: '填写账户基本信息',
    },
    {
      title: '身份验证',
      description: '验证邮箱和手机',
    },
    {
      title: '完善资料',
      description: '完善个人资料',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Logo 和标题 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
            <svg
              className="w-8 h-8 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm2 6a2 2 0 114 0 2 2 0 01-4 0zm8-2a2 2 0 100 4 2 2 0 000-4z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <Title level={2} className="mb-2">创建账户</Title>
          <Text type="secondary">加入 RAGFlow 智能文档处理平台</Text>
        </div>

        <Card className="shadow-lg">
          {/* 步骤指示器 */}
          <Steps current={currentStep} className="mb-8">
            {steps.map((step, index) => (
              <Step
                key={index}
                title={step.title}
                description={step.description}
                icon={currentStep > index ? <CheckCircleOutlined /> : undefined}
              />
            ))}
          </Steps>

          {error && (
            <Alert
              message="注册失败"
              description={error}
              type="error"
              showIcon
              className="mb-6"
            />
          )}

          <Form
            form={form}
            name="register"
            onFinish={handleSubmit}
            layout="vertical"
            size="large"
          >
            {/* 第一步：基本信息 */}
            {currentStep === 0 && (
              <div>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="username"
                      label="用户名"
                      rules={[
                        { required: true, message: '请输入用户名' },
                        { min: 3, max: 20, message: '用户名长度为3-20个字符' },
                        { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' },
                      ]}
                    >
                      <Input
                        prefix={<UserOutlined />}
                        placeholder="请输入用户名"
                        autoComplete="username"
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
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
                        placeholder="请输入邮箱地址"
                        autoComplete="email"
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="password"
                      label="密码"
                      rules={[
                        { required: true, message: '请输入密码' },
                        { min: 8, message: '密码至少8个字符' },
                        {
                          pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                          message: '密码必须包含大小写字母、数字和特殊字符',
                        },
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined />}
                        placeholder="请输入密码"
                        autoComplete="new-password"
                        iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="confirmPassword"
                      label="确认密码"
                      dependencies={['password']}
                      rules={[
                        { required: true, message: '请确认密码' },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            if (!value || getFieldValue('password') === value) {
                              return Promise.resolve();
                            }
                            return Promise.reject(new Error('两次输入的密码不一致'));
                          },
                        }),
                      ]}
                    >
                      <Input.Password
                        prefix={<LockOutlined />}
                        placeholder="请再次输入密码"
                        autoComplete="new-password"
                        iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item
                  name="phone"
                  label="手机号码"
                  rules={[
                    { required: true, message: '请输入手机号码' },
                    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' },
                  ]}
                >
                  <Input
                    prefix={<PhoneOutlined />}
                    placeholder="请输入手机号码"
                    autoComplete="tel"
                  />
                </Form.Item>
              </div>
            )}

            {/* 第二步：身份验证 */}
            {currentStep === 1 && (
              <div>
                <Alert
                  message="身份验证"
                  description="为了确保账户安全，请验证您的邮箱和手机号码。"
                  type="info"
                  showIcon
                  className="mb-6"
                />

                <Form.Item
                  name="emailCode"
                  label="邮箱验证码"
                  rules={[
                    { required: true, message: '请输入邮箱验证码' },
                    { len: 6, message: '验证码为6位数字' },
                  ]}
                >
                  <Row gutter={8}>
                    <Col span={16}>
                      <Input placeholder="请输入邮箱验证码" />
                    </Col>
                    <Col span={8}>
                      <Button
                        block
                        disabled={emailCountdown > 0}
                        onClick={sendEmailCode}
                      >
                        {emailCountdown > 0 ? `${emailCountdown}s` : '发送验证码'}
                      </Button>
                    </Col>
                  </Row>
                </Form.Item>

                <Form.Item
                  name="phoneCode"
                  label="手机验证码"
                  rules={[
                    { required: true, message: '请输入手机验证码' },
                    { len: 6, message: '验证码为6位数字' },
                  ]}
                >
                  <Row gutter={8}>
                    <Col span={16}>
                      <Input placeholder="请输入手机验证码" />
                    </Col>
                    <Col span={8}>
                      <Button
                        block
                        disabled={phoneCountdown > 0}
                        onClick={sendPhoneCode}
                      >
                        {phoneCountdown > 0 ? `${phoneCountdown}s` : '发送验证码'}
                      </Button>
                    </Col>
                  </Row>
                </Form.Item>
              </div>
            )}

            {/* 第三步：完善资料 */}
            {currentStep === 2 && (
              <div>
                <Row gutter={16}>
                  <Col span={8}>
                    <Form.Item label="头像">
                      <div className="text-center">
                        <Avatar
                          size={80}
                          src={avatar}
                          icon={<UserOutlined />}
                          className="mb-2"
                        />
                        <Upload
                          name="avatar"
                          action="/api/upload/avatar"
                          showUploadList={false}
                          onChange={handleAvatarChange}
                          accept="image/*"
                        >
                          <Button size="small" icon={<UploadOutlined />}>
                            上传头像
                          </Button>
                        </Upload>
                      </div>
                    </Form.Item>
                  </Col>
                  <Col span={16}>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          name="firstName"
                          label="姓"
                        >
                          <Input placeholder="请输入姓" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          name="lastName"
                          label="名"
                        >
                          <Input placeholder="请输入名" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item
                      name="company"
                      label="公司/组织"
                    >
                      <Input placeholder="请输入公司或组织名称" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="role"
                      label="职位角色"
                    >
                      <Select placeholder="请选择职位角色">
                        <Option value="developer">开发者</Option>
                        <Option value="researcher">研究员</Option>
                        <Option value="manager">管理者</Option>
                        <Option value="student">学生</Option>
                        <Option value="other">其他</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="industry"
                      label="行业领域"
                    >
                      <Select placeholder="请选择行业领域">
                        <Option value="technology">科技</Option>
                        <Option value="education">教育</Option>
                        <Option value="finance">金融</Option>
                        <Option value="healthcare">医疗</Option>
                        <Option value="government">政府</Option>
                        <Option value="other">其他</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item
                  name="agreement"
                  valuePropName="checked"
                  rules={[
                    {
                      validator: (_, value) =>
                        value ? Promise.resolve() : Promise.reject(new Error('请同意服务条款和隐私政策')),
                    },
                  ]}
                >
                  <Checkbox>
                    我已阅读并同意{' '}
                    <Link to="/terms" target="_blank" className="text-blue-600">
                      服务条款
                    </Link>
                    {' '}和{' '}
                    <Link to="/privacy" target="_blank" className="text-blue-600">
                      隐私政策
                    </Link>
                  </Checkbox>
                </Form.Item>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex justify-between mt-8">
              <div>
                {currentStep > 0 && (
                  <Button onClick={handlePrev}>
                    上一步
                  </Button>
                )}
              </div>
              <div>
                {currentStep < steps.length - 1 ? (
                  <Button type="primary" onClick={handleNext}>
                    下一步
                  </Button>
                ) : (
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    className="min-w-24"
                  >
                    完成注册
                  </Button>
                )}
              </div>
            </div>
          </Form>

          <div className="text-center mt-6">
            <Text type="secondary">
              已有账户？{' '}
              <Link to="/auth/login" className="text-blue-600 hover:text-blue-800">
                立即登录
              </Link>
            </Text>
          </div>
        </Card>

        {/* 页脚 */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          © 2024 RAGFlow. All rights reserved.
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;