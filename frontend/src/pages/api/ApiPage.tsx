import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Card,
  Typography,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  DatePicker,
  message,
  Tooltip,
  Popconfirm,
  Tabs,
  Statistic,
  Row,
  Col,
  Alert,
  Badge,
  Descriptions,
  Progress,
  Timeline,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  KeyOutlined,
  ApiOutlined,
  BarChartOutlined,
  SecurityScanOutlined,
  SettingOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

interface ApiKey {
  id: string;
  name: string;
  key: string;
  description?: string;
  permissions: string[];
  status: 'active' | 'inactive' | 'expired';
  expiresAt?: Date;
  createdAt: Date;
  lastUsed?: Date;
  usageCount: number;
  rateLimit: {
    requests: number;
    period: 'minute' | 'hour' | 'day';
  };
  allowedIPs?: string[];
  createdBy: string;
}

interface ApiEndpoint {
  id: string;
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  description: string;
  category: string;
  status: 'active' | 'deprecated' | 'maintenance';
  version: string;
  authentication: 'required' | 'optional' | 'none';
  rateLimit: {
    requests: number;
    period: 'minute' | 'hour' | 'day';
  };
  responseTime: number;
  successRate: number;
  lastUpdated: Date;
}

interface ApiUsage {
  date: string;
  requests: number;
  errors: number;
  avgResponseTime: number;
  uniqueUsers: number;
}

const ApiPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [activeTab, setActiveTab] = useState('keys');
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([]);
  const [usage, setUsage] = useState<ApiUsage[]>([]);
  const [loading, setLoading] = useState(false);
  const [keyModalVisible, setKeyModalVisible] = useState(false);
  const [endpointModalVisible, setEndpointModalVisible] = useState(false);
  const [editingKey, setEditingKey] = useState<ApiKey | null>(null);
  const [editingEndpoint, setEditingEndpoint] = useState<ApiEndpoint | null>(null);
  const [keyForm] = Form.useForm();
  const [endpointForm] = Form.useForm();
  const [showKeyValue, setShowKeyValue] = useState<Record<string, boolean>>({});

  useEffect(() => {
    dispatch(setPageTitle('API 管理'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/' },
      { title: 'API 管理' },
    ]));

    loadData();
  }, [dispatch]);

  const loadData = async () => {
    setLoading(true);
    try {
      // TODO: 调用实际 API
      await loadApiKeys();
      await loadEndpoints();
      await loadUsageData();
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const loadApiKeys = async () => {
    // 模拟数据
    const mockKeys: ApiKey[] = [
      {
        id: '1',
        name: '生产环境密钥',
        key: 'sk-1234567890abcdef',
        description: '用于生产环境的API访问',
        permissions: ['read', 'write', 'admin'],
        status: 'active',
        expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
        createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        lastUsed: new Date(Date.now() - 2 * 60 * 60 * 1000),
        usageCount: 15420,
        rateLimit: { requests: 1000, period: 'hour' },
        allowedIPs: ['192.168.1.100', '10.0.0.50'],
        createdBy: 'admin',
      },
      {
        id: '2',
        name: '测试环境密钥',
        key: 'sk-test567890abcdef',
        description: '用于测试环境的API访问',
        permissions: ['read', 'write'],
        status: 'active',
        createdAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
        lastUsed: new Date(Date.now() - 30 * 60 * 1000),
        usageCount: 2340,
        rateLimit: { requests: 100, period: 'hour' },
        createdBy: 'developer',
      },
      {
        id: '3',
        name: '已过期密钥',
        key: 'sk-expired567890abcdef',
        description: '已过期的API密钥',
        permissions: ['read'],
        status: 'expired',
        expiresAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
        createdAt: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
        lastUsed: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
        usageCount: 890,
        rateLimit: { requests: 50, period: 'hour' },
        createdBy: 'tester',
      },
    ];
    setApiKeys(mockKeys);
  };

  const loadEndpoints = async () => {
    // 模拟数据
    const mockEndpoints: ApiEndpoint[] = [
      {
        id: '1',
        path: '/api/v1/documents',
        method: 'GET',
        description: '获取文档列表',
        category: '文档管理',
        status: 'active',
        version: 'v1',
        authentication: 'required',
        rateLimit: { requests: 100, period: 'minute' },
        responseTime: 120,
        successRate: 99.5,
        lastUpdated: new Date(),
      },
      {
        id: '2',
        path: '/api/v1/documents',
        method: 'POST',
        description: '上传新文档',
        category: '文档管理',
        status: 'active',
        version: 'v1',
        authentication: 'required',
        rateLimit: { requests: 10, period: 'minute' },
        responseTime: 2500,
        successRate: 98.2,
        lastUpdated: new Date(),
      },
      {
        id: '3',
        path: '/api/v1/chat/completions',
        method: 'POST',
        description: 'AI对话接口',
        category: 'AI服务',
        status: 'active',
        version: 'v1',
        authentication: 'required',
        rateLimit: { requests: 60, period: 'minute' },
        responseTime: 1800,
        successRate: 97.8,
        lastUpdated: new Date(),
      },
      {
        id: '4',
        path: '/api/v0/legacy/upload',
        method: 'POST',
        description: '旧版文档上传接口',
        category: '文档管理',
        status: 'deprecated',
        version: 'v0',
        authentication: 'required',
        rateLimit: { requests: 5, period: 'minute' },
        responseTime: 3200,
        successRate: 95.1,
        lastUpdated: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      },
    ];
    setEndpoints(mockEndpoints);
  };

  const loadUsageData = async () => {
    // 模拟数据
    const mockUsage: ApiUsage[] = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
      mockUsage.push({
        date: date.toISOString().split('T')[0],
        requests: Math.floor(Math.random() * 10000) + 5000,
        errors: Math.floor(Math.random() * 100) + 10,
        avgResponseTime: Math.floor(Math.random() * 500) + 200,
        uniqueUsers: Math.floor(Math.random() * 200) + 50,
      });
    }
    setUsage(mockUsage);
  };

  const handleCreateKey = () => {
    setEditingKey(null);
    keyForm.resetFields();
    setKeyModalVisible(true);
  };

  const handleEditKey = (key: ApiKey) => {
    setEditingKey(key);
    keyForm.setFieldsValue({
      ...key,
      expiresAt: key.expiresAt ? dayjs(key.expiresAt) : undefined,
      allowedIPs: key.allowedIPs?.join('\n'),
    });
    setKeyModalVisible(true);
  };

  const handleSaveKey = async (values: any) => {
    try {
      const keyData = {
        ...values,
        expiresAt: values.expiresAt?.toDate(),
        allowedIPs: values.allowedIPs?.split('\n').filter((ip: string) => ip.trim()),
      };

      if (editingKey) {
        // 更新密钥
        setApiKeys(prev => prev.map(key => 
          key.id === editingKey.id 
            ? { ...key, ...keyData, lastUpdated: new Date() }
            : key
        ));
        message.success('API密钥更新成功');
      } else {
        // 创建新密钥
        const newKey: ApiKey = {
          id: Date.now().toString(),
          key: `sk-${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`,
          createdAt: new Date(),
          usageCount: 0,
          createdBy: 'current-user',
          status: 'active',
          ...keyData,
        };
        setApiKeys(prev => [newKey, ...prev]);
        message.success('API密钥创建成功');
      }

      setKeyModalVisible(false);
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleDeleteKey = async (keyId: string) => {
    try {
      setApiKeys(prev => prev.filter(key => key.id !== keyId));
      message.success('API密钥删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleToggleKeyStatus = async (keyId: string) => {
    try {
      setApiKeys(prev => prev.map(key => 
        key.id === keyId 
          ? { ...key, status: key.status === 'active' ? 'inactive' : 'active' }
          : key
      ));
      message.success('状态更新成功');
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  const toggleKeyVisibility = (keyId: string) => {
    setShowKeyValue(prev => ({
      ...prev,
      [keyId]: !prev[keyId],
    }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'orange';
      case 'expired': return 'red';
      case 'deprecated': return 'orange';
      case 'maintenance': return 'blue';
      default: return 'default';
    }
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'blue';
      case 'POST': return 'green';
      case 'PUT': return 'orange';
      case 'DELETE': return 'red';
      case 'PATCH': return 'purple';
      default: return 'default';
    }
  };

  const keyColumns: ColumnsType<ApiKey> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <div className="font-medium">{text}</div>
          {record.description && (
            <div className="text-sm text-gray-500">{record.description}</div>
          )}
        </div>
      ),
    },
    {
      title: 'API密钥',
      dataIndex: 'key',
      key: 'key',
      render: (text, record) => (
        <div className="flex items-center space-x-2">
          <code className="bg-gray-100 px-2 py-1 rounded text-sm">
            {showKeyValue[record.id] ? text : text.replace(/./g, '*')}
          </code>
          <Tooltip title={showKeyValue[record.id] ? '隐藏' : '显示'}>
            <Button
              type="text"
              size="small"
              icon={showKeyValue[record.id] ? <EyeInvisibleOutlined /> : <EyeOutlined />}
              onClick={() => toggleKeyVisibility(record.id)}
            />
          </Tooltip>
          <Tooltip title="复制">
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(text)}
            />
          </Tooltip>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status === 'active' ? '活跃' : status === 'inactive' ? '未激活' : '已过期'}
        </Tag>
      ),
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions) => (
        <div>
          {permissions.map((permission: string) => (
            <Tag key={permission} size="small">
              {permission === 'read' ? '读取' : permission === 'write' ? '写入' : '管理'}
            </Tag>
          ))}
        </div>
      ),
    },
    {
      title: '使用次数',
      dataIndex: 'usageCount',
      key: 'usageCount',
      render: (count) => count.toLocaleString(),
    },
    {
      title: '最后使用',
      dataIndex: 'lastUsed',
      key: 'lastUsed',
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '从未使用',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditKey(record)}
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? '停用' : '启用'}>
            <Button
              type="text"
              size="small"
              onClick={() => handleToggleKeyStatus(record.id)}
            >
              {record.status === 'active' ? '停用' : '启用'}
            </Button>
          </Tooltip>
          <Popconfirm
            title="确定要删除这个API密钥吗？"
            onConfirm={() => handleDeleteKey(record.id)}
          >
            <Tooltip title="删除">
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const endpointColumns: ColumnsType<ApiEndpoint> = [
    {
      title: '接口',
      key: 'endpoint',
      render: (_, record) => (
        <div>
          <div className="flex items-center space-x-2">
            <Tag color={getMethodColor(record.method)}>{record.method}</Tag>
            <code className="text-sm">{record.path}</code>
          </div>
          <div className="text-sm text-gray-500 mt-1">{record.description}</div>
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version) => <Tag>{version}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status === 'active' ? '活跃' : status === 'deprecated' ? '已弃用' : '维护中'}
        </Tag>
      ),
    },
    {
      title: '认证',
      dataIndex: 'authentication',
      key: 'authentication',
      render: (auth) => (
        <Tag color={auth === 'required' ? 'red' : auth === 'optional' ? 'orange' : 'green'}>
          {auth === 'required' ? '必需' : auth === 'optional' ? '可选' : '无需'}
        </Tag>
      ),
    },
    {
      title: '限流',
      key: 'rateLimit',
      render: (_, record) => (
        <span>{record.rateLimit.requests}/{record.rateLimit.period}</span>
      ),
    },
    {
      title: '响应时间',
      dataIndex: 'responseTime',
      key: 'responseTime',
      render: (time) => `${time}ms`,
    },
    {
      title: '成功率',
      dataIndex: 'successRate',
      key: 'successRate',
      render: (rate) => (
        <div className="flex items-center space-x-2">
          <Progress
            percent={rate}
            size="small"
            status={rate >= 99 ? 'success' : rate >= 95 ? 'normal' : 'exception'}
            showInfo={false}
            className="w-16"
          />
          <span className="text-sm">{rate}%</span>
        </div>
      ),
    },
  ];

  const totalRequests = usage.reduce((sum, day) => sum + day.requests, 0);
  const totalErrors = usage.reduce((sum, day) => sum + day.errors, 0);
  const avgResponseTime = usage.length > 0 
    ? Math.round(usage.reduce((sum, day) => sum + day.avgResponseTime, 0) / usage.length)
    : 0;
  const errorRate = totalRequests > 0 ? ((totalErrors / totalRequests) * 100).toFixed(2) : '0';

  return (
    <div className="space-y-6">
      {/* 统计概览 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总请求数"
              value={totalRequests}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃密钥"
              value={apiKeys.filter(key => key.status === 'active').length}
              prefix={<KeyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="错误率"
              value={errorRate}
              suffix="%"
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: parseFloat(errorRate) > 5 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={avgResponseTime}
              suffix="ms"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: avgResponseTime > 1000 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* API密钥管理 */}
          <TabPane tab="API密钥" key="keys">
            <div className="mb-4 flex justify-between items-center">
              <div>
                <Title level={4}>API密钥管理</Title>
                <Text type="secondary">管理系统的API访问密钥</Text>
              </div>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadApiKeys}>
                  刷新
                </Button>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateKey}>
                  创建密钥
                </Button>
              </Space>
            </div>

            <Table
              columns={keyColumns}
              dataSource={apiKeys}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个密钥`,
              }}
            />
          </TabPane>

          {/* API接口管理 */}
          <TabPane tab="API接口" key="endpoints">
            <div className="mb-4 flex justify-between items-center">
              <div>
                <Title level={4}>API接口管理</Title>
                <Text type="secondary">查看和管理系统的API接口</Text>
              </div>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={loadEndpoints}>
                  刷新
                </Button>
                <Button type="primary" icon={<SettingOutlined />}>
                  接口配置
                </Button>
              </Space>
            </div>

            <Table
              columns={endpointColumns}
              dataSource={endpoints}
              rowKey="id"
              loading={loading}
              pagination={{
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个接口`,
              }}
            />
          </TabPane>

          {/* 使用统计 */}
          <TabPane tab="使用统计" key="usage">
            <div className="mb-4">
              <Title level={4}>API使用统计</Title>
              <Text type="secondary">查看API的使用情况和性能指标</Text>
            </div>

            <Row gutter={16} className="mb-6">
              <Col span={12}>
                <Card title="最近7天请求趋势">
                  <div className="space-y-2">
                    {usage.map((day, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <span className="text-sm">{dayjs(day.date).format('MM-DD')}</span>
                        <div className="flex items-center space-x-4">
                          <span className="text-sm text-green-600">{day.requests.toLocaleString()}</span>
                          <span className="text-sm text-red-600">{day.errors}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="性能指标">
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">平均响应时间</span>
                        <span className="text-sm">{avgResponseTime}ms</span>
                      </div>
                      <Progress
                        percent={Math.min((avgResponseTime / 2000) * 100, 100)}
                        status={avgResponseTime > 1000 ? 'exception' : 'success'}
                        showInfo={false}
                      />
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">错误率</span>
                        <span className="text-sm">{errorRate}%</span>
                      </div>
                      <Progress
                        percent={Math.min(parseFloat(errorRate) * 10, 100)}
                        status={parseFloat(errorRate) > 5 ? 'exception' : 'success'}
                        showInfo={false}
                      />
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm">活跃用户</span>
                        <span className="text-sm">{usage[usage.length - 1]?.uniqueUsers || 0}</span>
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>

            <Card title="API调用日志">
              <Timeline>
                <Timeline.Item color="green">
                  <div className="flex justify-between">
                    <span>POST /api/v1/chat/completions - 200</span>
                    <span className="text-gray-500">2分钟前</span>
                  </div>
                  <div className="text-sm text-gray-500">响应时间: 1.2s | 用户: user123</div>
                </Timeline.Item>
                <Timeline.Item color="green">
                  <div className="flex justify-between">
                    <span>GET /api/v1/documents - 200</span>
                    <span className="text-gray-500">5分钟前</span>
                  </div>
                  <div className="text-sm text-gray-500">响应时间: 0.3s | 用户: user456</div>
                </Timeline.Item>
                <Timeline.Item color="red">
                  <div className="flex justify-between">
                    <span>POST /api/v1/documents - 429</span>
                    <span className="text-gray-500">8分钟前</span>
                  </div>
                  <div className="text-sm text-gray-500">错误: 请求频率超限 | 用户: user789</div>
                </Timeline.Item>
                <Timeline.Item color="green">
                  <div className="flex justify-between">
                    <span>GET /api/v1/knowledge-bases - 200</span>
                    <span className="text-gray-500">12分钟前</span>
                  </div>
                  <div className="text-sm text-gray-500">响应时间: 0.8s | 用户: user123</div>
                </Timeline.Item>
              </Timeline>
            </Card>
          </TabPane>
        </Tabs>
      </Card>

      {/* 创建/编辑密钥模态框 */}
      <Modal
        title={editingKey ? '编辑API密钥' : '创建API密钥'}
        open={keyModalVisible}
        onCancel={() => setKeyModalVisible(false)}
        onOk={() => keyForm.submit()}
        width={600}
      >
        <Form
          form={keyForm}
          layout="vertical"
          onFinish={handleSaveKey}
        >
          <Form.Item
            name="name"
            label="密钥名称"
            rules={[{ required: true, message: '请输入密钥名称' }]}
          >
            <Input placeholder="请输入密钥名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea placeholder="请输入密钥描述" rows={3} />
          </Form.Item>

          <Form.Item
            name="permissions"
            label="权限"
            rules={[{ required: true, message: '请选择权限' }]}
          >
            <Select mode="multiple" placeholder="请选择权限">
              <Option value="read">读取</Option>
              <Option value="write">写入</Option>
              <Option value="admin">管理</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name={['rateLimit', 'requests']}
                label="请求限制"
                rules={[{ required: true, message: '请输入请求限制' }]}
              >
                <Input type="number" placeholder="请求数量" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name={['rateLimit', 'period']}
                label="时间周期"
                rules={[{ required: true, message: '请选择时间周期' }]}
              >
                <Select placeholder="请选择时间周期">
                  <Option value="minute">每分钟</Option>
                  <Option value="hour">每小时</Option>
                  <Option value="day">每天</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="expiresAt"
            label="过期时间"
          >
            <DatePicker
              showTime
              placeholder="选择过期时间（可选）"
              className="w-full"
            />
          </Form.Item>

          <Form.Item
            name="allowedIPs"
            label="允许的IP地址"
          >
            <Input.TextArea
              placeholder="每行一个IP地址（可选）\n例如：\n192.168.1.100\n10.0.0.50"
              rows={3}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiPage;