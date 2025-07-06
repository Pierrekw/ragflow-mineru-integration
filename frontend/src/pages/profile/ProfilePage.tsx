import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Avatar,
  Upload,
  Row,
  Col,
  Tabs,
  Switch,
  Select,
  DatePicker,
  TimePicker,
  Divider,
  Space,
  message,
  Modal,
  List,
  Tag,
  Badge,
  Typography,
  Alert,
  Tooltip,
  Progress,
  Statistic,
  Table,
} from 'antd';
import {
  UserOutlined,
  CameraOutlined,
  LockOutlined,
  SettingOutlined,
  BellOutlined,
  SecurityScanOutlined,
  HistoryOutlined,
  ApiOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  DownloadOutlined,
  GlobalOutlined,
  MobileOutlined,
  MailOutlined,
  CalendarOutlined,
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { UploadProps } from 'antd';
import dayjs from 'dayjs';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { confirm } = Modal;

interface UserProfile {
  id: string;
  username: string;
  email: string;
  phone: string;
  fullName: string;
  avatar: string;
  bio: string;
  company: string;
  position: string;
  location: string;
  website: string;
  birthday: string;
  gender: string;
  language: string;
  timezone: string;
  createdAt: string;
  lastLoginAt: string;
  emailVerified: boolean;
  phoneVerified: boolean;
  twoFactorEnabled: boolean;
}

interface LoginHistory {
  id: string;
  ip: string;
  location: string;
  device: string;
  browser: string;
  loginTime: string;
  success: boolean;
}

interface ApiKey {
  id: string;
  name: string;
  key: string;
  permissions: string[];
  lastUsed: string;
  createdAt: string;
  expiresAt: string;
  status: 'active' | 'expired' | 'revoked';
}

const ProfilePage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loginHistory, setLoginHistory] = useState<LoginHistory[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    pushNotifications: false,
    smsNotifications: false,
    marketingEmails: false,
    securityAlerts: true,
    weeklyReports: true,
    autoSave: true,
    darkMode: false,
    compactMode: false,
    showTips: true,
  });

  useEffect(() => {
    dispatch(setPageTitle('个人资料'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/' },
      { title: '个人资料' },
    ]));

    loadUserProfile();
    loadLoginHistory();
    loadApiKeys();
  }, [dispatch]);

  const loadUserProfile = () => {
    // 模拟用户数据
    const mockProfile: UserProfile = {
      id: 'user_123',
      username: 'john_doe',
      email: 'john.doe@example.com',
      phone: '+86 138 0013 8000',
      fullName: '张三',
      avatar: '',
      bio: '资深数据分析师，专注于AI和机器学习领域',
      company: 'AI科技有限公司',
      position: '高级数据科学家',
      location: '北京市朝阳区',
      website: 'https://johndoe.com',
      birthday: '1990-05-15',
      gender: 'male',
      language: 'zh-CN',
      timezone: 'Asia/Shanghai',
      createdAt: '2023-01-15T08:30:00Z',
      lastLoginAt: '2024-01-15T14:30:00Z',
      emailVerified: true,
      phoneVerified: false,
      twoFactorEnabled: true,
    };

    setProfile(mockProfile);
    form.setFieldsValue(mockProfile);
  };

  const loadLoginHistory = () => {
    // 模拟登录历史
    const mockHistory: LoginHistory[] = [
      {
        id: '1',
        ip: '192.168.1.100',
        location: '北京市朝阳区',
        device: 'Windows 11',
        browser: 'Chrome 120.0',
        loginTime: '2024-01-15T14:30:00Z',
        success: true,
      },
      {
        id: '2',
        ip: '192.168.1.101',
        location: '上海市浦东新区',
        device: 'iPhone 15',
        browser: 'Safari 17.0',
        loginTime: '2024-01-14T09:15:00Z',
        success: true,
      },
      {
        id: '3',
        ip: '10.0.0.50',
        location: '广州市天河区',
        device: 'MacBook Pro',
        browser: 'Chrome 119.0',
        loginTime: '2024-01-13T16:45:00Z',
        success: false,
      },
    ];

    setLoginHistory(mockHistory);
  };

  const loadApiKeys = () => {
    // 模拟API密钥
    const mockApiKeys: ApiKey[] = [
      {
        id: '1',
        name: '生产环境密钥',
        key: 'sk-1234567890abcdef',
        permissions: ['read', 'write'],
        lastUsed: '2024-01-15T10:30:00Z',
        createdAt: '2023-12-01T08:00:00Z',
        expiresAt: '2024-12-01T08:00:00Z',
        status: 'active',
      },
      {
        id: '2',
        name: '测试环境密钥',
        key: 'sk-abcdef1234567890',
        permissions: ['read'],
        lastUsed: '2024-01-10T15:20:00Z',
        createdAt: '2023-11-15T10:00:00Z',
        expiresAt: '2024-11-15T10:00:00Z',
        status: 'active',
      },
    ];

    setApiKeys(mockApiKeys);
  };

  const handleProfileUpdate = async (values: any) => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setProfile(prev => prev ? { ...prev, ...values } : null);
      message.success('个人资料更新成功！');
    } catch (error) {
      message.error('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: any) => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      message.success('密码修改成功！');
      passwordForm.resetFields();
    } catch (error) {
      message.error('密码修改失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload: UploadProps['customRequest'] = (options) => {
    const { file, onSuccess, onError } = options;
    
    // 模拟上传
    setTimeout(() => {
      if (Math.random() > 0.1) {
        message.success('头像上传成功！');
        onSuccess?.(file);
      } else {
        message.error('上传失败，请重试');
        onError?.(new Error('Upload failed'));
      }
    }, 1000);
  };

  const handlePreferenceChange = (key: string, value: boolean) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value,
    }));
    message.success('偏好设置已保存');
  };

  const handleDeleteAccount = () => {
    confirm({
      title: '确认删除账户',
      content: '删除账户后，所有数据将无法恢复。请确认您要继续此操作。',
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk() {
        message.success('账户删除请求已提交，我们会在24小时内处理');
      },
    });
  };

  const handleRevokeApiKey = (keyId: string) => {
    setApiKeys(prev => prev.map(key => 
      key.id === keyId 
        ? { ...key, status: 'revoked' as const }
        : key
    ));
    message.success('API密钥已撤销');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'expired': return 'orange';
      case 'revoked': return 'red';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '活跃';
      case 'expired': return '已过期';
      case 'revoked': return '已撤销';
      default: return status;
    }
  };

  const loginHistoryColumns = [
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: '设备',
      dataIndex: 'device',
      key: 'device',
    },
    {
      title: '浏览器',
      dataIndex: 'browser',
      key: 'browser',
    },
    {
      title: '登录时间',
      dataIndex: 'loginTime',
      key: 'loginTime',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      render: (success: boolean) => (
        <Tag color={success ? 'green' : 'red'}>
          {success ? '成功' : '失败'}
        </Tag>
      ),
    },
  ];

  if (!profile) {
    return <div>加载中...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto">
      <Row gutter={[24, 24]}>
        {/* 左侧个人信息卡片 */}
        <Col span={8}>
          <Card>
            <div className="text-center">
              <div className="relative inline-block mb-4">
                <Avatar size={120} src={profile.avatar} icon={<UserOutlined />} />
                <Upload
                  customRequest={handleAvatarUpload}
                  showUploadList={false}
                  accept="image/*"
                >
                  <Button
                    type="primary"
                    shape="circle"
                    icon={<CameraOutlined />}
                    className="absolute bottom-0 right-0"
                    size="small"
                  />
                </Upload>
              </div>
              
              <Title level={4}>{profile.fullName}</Title>
              <Text type="secondary">@{profile.username}</Text>
              
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-center space-x-2">
                  <MailOutlined />
                  <Text>{profile.email}</Text>
                  {profile.emailVerified && (
                    <CheckCircleOutlined className="text-green-500" />
                  )}
                </div>
                
                <div className="flex items-center justify-center space-x-2">
                  <MobileOutlined />
                  <Text>{profile.phone}</Text>
                  {!profile.phoneVerified && (
                    <ExclamationCircleOutlined className="text-orange-500" />
                  )}
                </div>
                
                <div className="flex items-center justify-center space-x-2">
                  <CalendarOutlined />
                  <Text>加入于 {dayjs(profile.createdAt).format('YYYY年MM月')}</Text>
                </div>
              </div>
              
              <Divider />
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <Text>账户安全</Text>
                  <Progress 
                    percent={profile.twoFactorEnabled ? 90 : 60} 
                    size="small" 
                    status={profile.twoFactorEnabled ? 'success' : 'normal'}
                    showInfo={false}
                  />
                </div>
                
                <div className="flex justify-between">
                  <Text>资料完整度</Text>
                  <Progress 
                    percent={85} 
                    size="small" 
                    showInfo={false}
                  />
                </div>
              </div>
            </div>
          </Card>
        </Col>
        
        {/* 右侧主要内容 */}
        <Col span={16}>
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            {/* 基本信息 */}
            <TabPane tab={<span><UserOutlined />基本信息</span>} key="profile">
              <Card title="个人信息">
                <Form
                  form={form}
                  layout="vertical"
                  onFinish={handleProfileUpdate}
                  initialValues={profile}
                >
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label="用户名"
                        name="username"
                        rules={[{ required: true, message: '请输入用户名' }]}
                      >
                        <Input disabled />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="真实姓名"
                        name="fullName"
                        rules={[{ required: true, message: '请输入真实姓名' }]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label="邮箱"
                        name="email"
                        rules={[
                          { required: true, message: '请输入邮箱' },
                          { type: 'email', message: '请输入有效的邮箱地址' },
                        ]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="手机号"
                        name="phone"
                        rules={[{ required: true, message: '请输入手机号' }]}
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label="公司"
                        name="company"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="职位"
                        name="position"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label="所在地"
                        name="location"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="个人网站"
                        name="website"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        label="生日"
                        name="birthday"
                      >
                        <DatePicker className="w-full" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="性别"
                        name="gender"
                      >
                        <Select>
                          <Option value="male">男</Option>
                          <Option value="female">女</Option>
                          <Option value="other">其他</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Form.Item
                    label="个人简介"
                    name="bio"
                  >
                    <TextArea rows={4} placeholder="介绍一下自己..." />
                  </Form.Item>
                  
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      保存更改
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            </TabPane>
            
            {/* 安全设置 */}
            <TabPane tab={<span><LockOutlined />安全设置</span>} key="security">
              <Space direction="vertical" size="large" className="w-full">
                {/* 修改密码 */}
                <Card title="修改密码">
                  <Form
                    form={passwordForm}
                    layout="vertical"
                    onFinish={handlePasswordChange}
                  >
                    <Form.Item
                      label="当前密码"
                      name="currentPassword"
                      rules={[{ required: true, message: '请输入当前密码' }]}
                    >
                      <Input.Password
                        iconRender={(visible) => 
                          visible ? <EyeOutlined /> : <EyeInvisibleOutlined />
                        }
                      />
                    </Form.Item>
                    
                    <Form.Item
                      label="新密码"
                      name="newPassword"
                      rules={[
                        { required: true, message: '请输入新密码' },
                        { min: 8, message: '密码至少8位' },
                      ]}
                    >
                      <Input.Password
                        iconRender={(visible) => 
                          visible ? <EyeOutlined /> : <EyeInvisibleOutlined />
                        }
                      />
                    </Form.Item>
                    
                    <Form.Item
                      label="确认新密码"
                      name="confirmPassword"
                      dependencies={['newPassword']}
                      rules={[
                        { required: true, message: '请确认新密码' },
                        ({ getFieldValue }) => ({
                          validator(_, value) {
                            if (!value || getFieldValue('newPassword') === value) {
                              return Promise.resolve();
                            }
                            return Promise.reject(new Error('两次输入的密码不一致'));
                          },
                        }),
                      ]}
                    >
                      <Input.Password
                        iconRender={(visible) => 
                          visible ? <EyeOutlined /> : <EyeInvisibleOutlined />
                        }
                      />
                    </Form.Item>
                    
                    <Form.Item>
                      <Button type="primary" htmlType="submit" loading={loading}>
                        修改密码
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
                
                {/* 两步验证 */}
                <Card title="两步验证">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">两步验证</div>
                      <Text type="secondary">
                        为您的账户添加额外的安全保护
                      </Text>
                    </div>
                    <Switch 
                      checked={profile.twoFactorEnabled}
                      onChange={(checked) => {
                        setProfile(prev => prev ? { ...prev, twoFactorEnabled: checked } : null);
                        message.success(checked ? '两步验证已启用' : '两步验证已关闭');
                      }}
                    />
                  </div>
                </Card>
                
                {/* 登录历史 */}
                <Card title="登录历史">
                  <Table
                    dataSource={loginHistory}
                    columns={loginHistoryColumns}
                    rowKey="id"
                    pagination={{ pageSize: 5 }}
                    size="small"
                  />
                </Card>
              </Space>
            </TabPane>
            
            {/* 通知设置 */}
            <TabPane tab={<span><BellOutlined />通知设置</span>} key="notifications">
              <Card title="通知偏好">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">邮件通知</div>
                      <Text type="secondary">接收重要更新和通知邮件</Text>
                    </div>
                    <Switch 
                      checked={preferences.emailNotifications}
                      onChange={(checked) => handlePreferenceChange('emailNotifications', checked)}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">推送通知</div>
                      <Text type="secondary">接收浏览器推送通知</Text>
                    </div>
                    <Switch 
                      checked={preferences.pushNotifications}
                      onChange={(checked) => handlePreferenceChange('pushNotifications', checked)}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">短信通知</div>
                      <Text type="secondary">接收重要安全提醒短信</Text>
                    </div>
                    <Switch 
                      checked={preferences.smsNotifications}
                      onChange={(checked) => handlePreferenceChange('smsNotifications', checked)}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">营销邮件</div>
                      <Text type="secondary">接收产品更新和营销信息</Text>
                    </div>
                    <Switch 
                      checked={preferences.marketingEmails}
                      onChange={(checked) => handlePreferenceChange('marketingEmails', checked)}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">安全警报</div>
                      <Text type="secondary">接收账户安全相关警报</Text>
                    </div>
                    <Switch 
                      checked={preferences.securityAlerts}
                      onChange={(checked) => handlePreferenceChange('securityAlerts', checked)}
                    />
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">周报</div>
                      <Text type="secondary">接收每周使用情况报告</Text>
                    </div>
                    <Switch 
                      checked={preferences.weeklyReports}
                      onChange={(checked) => handlePreferenceChange('weeklyReports', checked)}
                    />
                  </div>
                </div>
              </Card>
            </TabPane>
            
            {/* 偏好设置 */}
            <TabPane tab={<span><SettingOutlined />偏好设置</span>} key="preferences">
              <Space direction="vertical" size="large" className="w-full">
                <Card title="界面设置">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">深色模式</div>
                        <Text type="secondary">使用深色主题界面</Text>
                      </div>
                      <Switch 
                        checked={preferences.darkMode}
                        onChange={(checked) => handlePreferenceChange('darkMode', checked)}
                      />
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">紧凑模式</div>
                        <Text type="secondary">使用更紧凑的界面布局</Text>
                      </div>
                      <Switch 
                        checked={preferences.compactMode}
                        onChange={(checked) => handlePreferenceChange('compactMode', checked)}
                      />
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">显示提示</div>
                        <Text type="secondary">显示操作提示和帮助信息</Text>
                      </div>
                      <Switch 
                        checked={preferences.showTips}
                        onChange={(checked) => handlePreferenceChange('showTips', checked)}
                      />
                    </div>
                  </div>
                </Card>
                
                <Card title="功能设置">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">自动保存</div>
                        <Text type="secondary">自动保存编辑内容</Text>
                      </div>
                      <Switch 
                        checked={preferences.autoSave}
                        onChange={(checked) => handlePreferenceChange('autoSave', checked)}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <div className="font-medium">语言设置</div>
                      <Select value={profile.language} className="w-full">
                        <Option value="zh-CN">简体中文</Option>
                        <Option value="zh-TW">繁体中文</Option>
                        <Option value="en-US">English</Option>
                        <Option value="ja-JP">日本語</Option>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="font-medium">时区设置</div>
                      <Select value={profile.timezone} className="w-full">
                        <Option value="Asia/Shanghai">北京时间 (UTC+8)</Option>
                        <Option value="Asia/Tokyo">东京时间 (UTC+9)</Option>
                        <Option value="America/New_York">纽约时间 (UTC-5)</Option>
                        <Option value="Europe/London">伦敦时间 (UTC+0)</Option>
                      </Select>
                    </div>
                  </div>
                </Card>
              </Space>
            </TabPane>
            
            {/* API密钥 */}
            <TabPane tab={<span><ApiOutlined />API密钥</span>} key="api">
              <Card 
                title="API密钥管理"
                extra={
                  <Button type="primary">
                    创建新密钥
                  </Button>
                }
              >
                <List
                  dataSource={apiKeys}
                  renderItem={(item) => (
                    <List.Item
                      actions={[
                        <Tooltip title="复制密钥">
                          <Button 
                            type="text" 
                            icon={<DownloadOutlined />}
                            onClick={() => {
                              navigator.clipboard.writeText(item.key);
                              message.success('密钥已复制到剪贴板');
                            }}
                          />
                        </Tooltip>,
                        <Tooltip title="撤销密钥">
                          <Button 
                            type="text" 
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => handleRevokeApiKey(item.id)}
                            disabled={item.status === 'revoked'}
                          />
                        </Tooltip>,
                      ]}
                    >
                      <List.Item.Meta
                        title={
                          <div className="flex items-center space-x-2">
                            <span>{item.name}</span>
                            <Tag color={getStatusColor(item.status)}>
                              {getStatusText(item.status)}
                            </Tag>
                          </div>
                        }
                        description={
                          <div className="space-y-1">
                            <div>
                              <Text code>{item.key.substring(0, 20)}...</Text>
                            </div>
                            <div className="flex space-x-4 text-sm text-gray-500">
                              <span>权限: {item.permissions.join(', ')}</span>
                              <span>最后使用: {dayjs(item.lastUsed).format('YYYY-MM-DD')}</span>
                              <span>过期时间: {dayjs(item.expiresAt).format('YYYY-MM-DD')}</span>
                            </div>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </TabPane>
            
            {/* 账户管理 */}
            <TabPane tab={<span><SecurityScanOutlined />账户管理</span>} key="account">
              <Space direction="vertical" size="large" className="w-full">
                <Card title="账户统计">
                  <Row gutter={16}>
                    <Col span={6}>
                      <Statistic title="总文档数" value={156} />
                    </Col>
                    <Col span={6}>
                      <Statistic title="知识库数" value={8} />
                    </Col>
                    <Col span={6}>
                      <Statistic title="API调用" value={2340} />
                    </Col>
                    <Col span={6}>
                      <Statistic title="存储使用" value={1.2} suffix="GB" />
                    </Col>
                  </Row>
                </Card>
                
                <Card title="数据导出">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">导出个人数据</div>
                        <Text type="secondary">下载您的所有个人数据和文档</Text>
                      </div>
                      <Button icon={<DownloadOutlined />}>
                        导出数据
                      </Button>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium">导出聊天记录</div>
                        <Text type="secondary">下载您的所有对话历史</Text>
                      </div>
                      <Button icon={<DownloadOutlined />}>
                        导出记录
                      </Button>
                    </div>
                  </div>
                </Card>
                
                <Card title="危险操作">
                  <Alert
                    message="警告"
                    description="以下操作不可逆，请谨慎操作"
                    type="warning"
                    showIcon
                    className="mb-4"
                  />
                  
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium text-red-600">删除账户</div>
                        <Text type="secondary">永久删除您的账户和所有数据</Text>
                      </div>
                      <Button 
                        danger 
                        icon={<DeleteOutlined />}
                        onClick={handleDeleteAccount}
                      >
                        删除账户
                      </Button>
                    </div>
                  </div>
                </Card>
              </Space>
            </TabPane>
          </Tabs>
        </Col>
      </Row>
    </div>
  );
};

export default ProfilePage;