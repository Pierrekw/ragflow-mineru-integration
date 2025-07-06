import React, { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Switch,
  Select,
  InputNumber,
  Upload,
  message,
  Tabs,
  Divider,
  Space,
  Alert,
  Row,
  Col,
  Typography,
  Modal,
  Progress,
  List,
  Tag,
  Tooltip,
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  DatabaseOutlined,
  MailOutlined,
  SecurityScanOutlined,
  CloudOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  fetchSystemSettings,
  updateSystemSettings,
  fetchSystemInfo,
  checkSystemHealth,
} from '@/store/slices/systemSlice';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { SystemSettings, SystemInfo } from '@/types';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

const SettingsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { settings, systemInfo, loading } = useAppSelector(state => state.system);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('general');
  const [saving, setSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);

  useEffect(() => {
    dispatch(setPageTitle('系统设置'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/dashboard' },
      { title: '系统设置' },
    ]));
    
    // 加载系统设置和信息
    dispatch(fetchSystemSettings());
    dispatch(fetchSystemInfo());
    dispatch(checkSystemHealth());
  }, [dispatch]);

  useEffect(() => {
    if (settings) {
      form.setFieldsValue(settings);
    }
  }, [settings, form]);

  // 保存设置
  const handleSave = async () => {
    try {
      setSaving(true);
      const values = await form.validateFields();
      await dispatch(updateSystemSettings(values)).unwrap();
      message.success('设置保存成功');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  // 重置设置
  const handleReset = () => {
    Modal.confirm({
      title: '确认重置',
      content: '确定要重置所有设置到默认值吗？此操作不可撤销。',
      icon: <ExclamationCircleOutlined />,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        form.resetFields();
        message.info('设置已重置');
      },
    });
  };

  // 测试连接
  const handleTestConnection = async (type: string) => {
    setTestingConnection(type);
    try {
      // TODO: 实现连接测试
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success(`${type}连接测试成功`);
    } catch (error) {
      message.error(`${type}连接测试失败`);
    } finally {
      setTestingConnection(null);
    }
  };

  // 系统健康状态
  const healthStatus = {
    database: 'healthy',
    storage: 'healthy',
    email: 'warning',
    cache: 'healthy',
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const getHealthText = (status: string) => {
    switch (status) {
      case 'healthy':
        return '正常';
      case 'warning':
        return '警告';
      case 'error':
        return '错误';
      default:
        return '未知';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <Title level={2} className="mb-2">系统设置</Title>
          <Text type="secondary">配置系统参数和功能选项</Text>
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              dispatch(fetchSystemSettings());
              dispatch(fetchSystemInfo());
            }}
          >
            刷新
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            onClick={handleSave}
          >
            保存设置
          </Button>
        </Space>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 基本设置 */}
        <TabPane tab={<span><SettingOutlined />基本设置</span>} key="general">
          <Card>
            <Form form={form} layout="vertical">
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="siteName"
                    label="站点名称"
                    rules={[{ required: true, message: '请输入站点名称' }]}
                  >
                    <Input placeholder="请输入站点名称" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="siteUrl"
                    label="站点URL"
                    rules={[{ required: true, message: '请输入站点URL' }]}
                  >
                    <Input placeholder="https://example.com" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item
                name="description"
                label="站点描述"
              >
                <TextArea rows={3} placeholder="请输入站点描述" />
              </Form.Item>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="language"
                    label="默认语言"
                  >
                    <Select placeholder="选择默认语言">
                      <Option value="zh-CN">简体中文</Option>
                      <Option value="en-US">English</Option>
                      <Option value="ja-JP">日本語</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="timezone"
                    label="时区"
                  >
                    <Select placeholder="选择时区">
                      <Option value="Asia/Shanghai">Asia/Shanghai</Option>
                      <Option value="UTC">UTC</Option>
                      <Option value="America/New_York">America/New_York</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              
              <Divider>功能开关</Divider>
              
              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    name="enableRegistration"
                    label="允许用户注册"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="enableEmailVerification"
                    label="邮箱验证"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="enableTwoFactor"
                    label="双因子认证"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </TabPane>

        {/* 数据库设置 */}
        <TabPane tab={<span><DatabaseOutlined />数据库</span>} key="database">
          <Card>
            <Alert
              message="数据库配置"
              description="修改数据库配置需要重启系统才能生效，请谨慎操作。"
              type="warning"
              showIcon
              className="mb-4"
            />
            
            <Form form={form} layout="vertical">
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['database', 'host']}
                    label="数据库主机"
                  >
                    <Input placeholder="localhost" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['database', 'port']}
                    label="端口"
                  >
                    <InputNumber min={1} max={65535} placeholder="5432" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['database', 'name']}
                    label="数据库名"
                  >
                    <Input placeholder="ragflow" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['database', 'username']}
                    label="用户名"
                  >
                    <Input placeholder="postgres" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item
                name={['database', 'password']}
                label="密码"
              >
                <Input.Password placeholder="请输入数据库密码" />
              </Form.Item>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['database', 'maxConnections']}
                    label="最大连接数"
                  >
                    <InputNumber min={1} max={1000} placeholder="100" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['database', 'connectionTimeout']}
                    label="连接超时(秒)"
                  >
                    <InputNumber min={1} max={300} placeholder="30" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Button
                  type="primary"
                  loading={testingConnection === 'database'}
                  onClick={() => handleTestConnection('数据库')}
                >
                  测试连接
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* 邮件设置 */}
        <TabPane tab={<span><MailOutlined />邮件</span>} key="email">
          <Card>
            <Form form={form} layout="vertical">
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['email', 'host']}
                    label="SMTP服务器"
                  >
                    <Input placeholder="smtp.gmail.com" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['email', 'port']}
                    label="端口"
                  >
                    <InputNumber min={1} max={65535} placeholder="587" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['email', 'username']}
                    label="用户名"
                  >
                    <Input placeholder="your-email@gmail.com" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['email', 'password']}
                    label="密码"
                  >
                    <Input.Password placeholder="请输入邮箱密码" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['email', 'fromName']}
                    label="发件人名称"
                  >
                    <Input placeholder="RAGFlow System" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['email', 'fromEmail']}
                    label="发件人邮箱"
                  >
                    <Input placeholder="noreply@example.com" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    name={['email', 'enableSSL']}
                    label="启用SSL"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['email', 'enableTLS']}
                    label="启用TLS"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['email', 'enableAuth']}
                    label="启用认证"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    loading={testingConnection === 'email'}
                    onClick={() => handleTestConnection('邮件')}
                  >
                    测试连接
                  </Button>
                  <Button>
                    发送测试邮件
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* 存储设置 */}
        <TabPane tab={<span><CloudOutlined />存储</span>} key="storage">
          <Card>
            <Form form={form} layout="vertical">
              <Form.Item
                name={['storage', 'type']}
                label="存储类型"
              >
                <Select placeholder="选择存储类型">
                  <Option value="local">本地存储</Option>
                  <Option value="s3">Amazon S3</Option>
                  <Option value="oss">阿里云OSS</Option>
                  <Option value="cos">腾讯云COS</Option>
                </Select>
              </Form.Item>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['storage', 'bucket']}
                    label="存储桶名称"
                  >
                    <Input placeholder="my-bucket" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['storage', 'region']}
                    label="区域"
                  >
                    <Input placeholder="us-east-1" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['storage', 'accessKey']}
                    label="Access Key"
                  >
                    <Input placeholder="请输入Access Key" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['storage', 'secretKey']}
                    label="Secret Key"
                  >
                    <Input.Password placeholder="请输入Secret Key" />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['storage', 'maxFileSize']}
                    label="最大文件大小(MB)"
                  >
                    <InputNumber min={1} max={1024} placeholder="100" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['storage', 'allowedTypes']}
                    label="允许的文件类型"
                  >
                    <Select mode="tags" placeholder="pdf,doc,docx,txt">
                      <Option value="pdf">PDF</Option>
                      <Option value="doc">DOC</Option>
                      <Option value="docx">DOCX</Option>
                      <Option value="txt">TXT</Option>
                      <Option value="md">Markdown</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item>
                <Button
                  type="primary"
                  loading={testingConnection === 'storage'}
                  onClick={() => handleTestConnection('存储')}
                >
                  测试连接
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* 安全设置 */}
        <TabPane tab={<span><SecurityScanOutlined />安全</span>} key="security">
          <Card>
            <Form form={form} layout="vertical">
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['security', 'sessionTimeout']}
                    label="会话超时(分钟)"
                  >
                    <InputNumber min={5} max={1440} placeholder="30" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['security', 'maxLoginAttempts']}
                    label="最大登录尝试次数"
                  >
                    <InputNumber min={1} max={10} placeholder="5" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name={['security', 'lockoutDuration']}
                    label="锁定时长(分钟)"
                  >
                    <InputNumber min={1} max={1440} placeholder="15" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['security', 'passwordMinLength']}
                    label="密码最小长度"
                  >
                    <InputNumber min={6} max={32} placeholder="8" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Divider>密码策略</Divider>
              
              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    name={['security', 'requireUppercase']}
                    label="需要大写字母"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['security', 'requireLowercase']}
                    label="需要小写字母"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['security', 'requireNumbers']}
                    label="需要数字"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    name={['security', 'requireSpecialChars']}
                    label="需要特殊字符"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['security', 'enableIPWhitelist']}
                    label="启用IP白名单"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['security', 'enableAuditLog']}
                    label="启用审计日志"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </TabPane>

        {/* 通知设置 */}
        <TabPane tab={<span><BellOutlined />通知</span>} key="notifications">
          <Card>
            <Form form={form} layout="vertical">
              <Divider>邮件通知</Divider>
              
              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    name={['notifications', 'emailOnUserRegister']}
                    label="用户注册通知"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['notifications', 'emailOnTaskComplete']}
                    label="任务完成通知"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['notifications', 'emailOnSystemError']}
                    label="系统错误通知"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
              
              <Divider>系统通知</Divider>
              
              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    name={['notifications', 'systemMaintenanceNotice']}
                    label="维护通知"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['notifications', 'systemUpdateNotice']}
                    label="更新通知"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name={['notifications', 'securityAlerts']}
                    label="安全警报"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </TabPane>

        {/* 系统信息 */}
        <TabPane tab={<span><InfoCircleOutlined />系统信息</span>} key="info">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="系统状态" className="mb-4">
                <List
                  dataSource={[
                    { name: '数据库', status: healthStatus.database },
                    { name: '存储', status: healthStatus.storage },
                    { name: '邮件服务', status: healthStatus.email },
                    { name: '缓存', status: healthStatus.cache },
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <Space>
                        {getHealthIcon(item.status)}
                        <span>{item.name}</span>
                        <Tag color={item.status === 'healthy' ? 'green' : item.status === 'warning' ? 'orange' : 'red'}>
                          {getHealthText(item.status)}
                        </Tag>
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="系统信息" className="mb-4">
                {systemInfo && (
                  <List
                    dataSource={[
                      { label: '版本', value: systemInfo.version },
                      { label: '构建时间', value: systemInfo.buildTime },
                      { label: '运行时间', value: systemInfo.uptime },
                      { label: 'Node.js版本', value: systemInfo.nodeVersion },
                      { label: '操作系统', value: systemInfo.platform },
                      { label: '内存使用', value: `${systemInfo.memoryUsage}MB` },
                    ]}
                    renderItem={(item) => (
                      <List.Item>
                        <div className="flex justify-between w-full">
                          <span>{item.label}:</span>
                          <span className="font-mono">{item.value}</span>
                        </div>
                      </List.Item>
                    )}
                  />
                )}
              </Card>
            </Col>
          </Row>
          
          <Card title="操作">
            <Space>
              <Button icon={<DownloadOutlined />}>
                导出配置
              </Button>
              <Upload
                accept=".json"
                showUploadList={false}
                beforeUpload={() => false}
              >
                <Button icon={<UploadOutlined />}>
                  导入配置
                </Button>
              </Upload>
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleReset}
              >
                重置设置
              </Button>
            </Space>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default SettingsPage;