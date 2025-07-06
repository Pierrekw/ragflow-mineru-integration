import React, { useEffect, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Button,
  Select,
  DatePicker,
  Space,
  Alert,
  Typography,
  Tabs,
  List,
  Timeline,
  Tooltip,
  Modal,
  message,
} from 'antd';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  MemoryStickOutlined,
  HddOutlined,
  WifiOutlined,
  BugOutlined,
  SettingOutlined,
  DownloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  fetchSystemStats,
  checkSystemHealth,
  fetchSystemInfo,
} from '@/store/slices/systemSlice';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { ColumnsType } from 'antd/es/table';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface MetricData {
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  source: string;
  details?: string;
}

interface AlertItem {
  id: string;
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'service';
  level: 'warning' | 'critical';
  message: string;
  timestamp: string;
  resolved: boolean;
}

const MonitoringPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { stats, systemInfo, healthStatus, loading } = useAppSelector(state => state.system);
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('cpu');

  // 模拟数据
  const [metricsData, setMetricsData] = useState<MetricData[]>([
    { timestamp: '00:00', cpu: 45, memory: 62, disk: 78, network: 23 },
    { timestamp: '00:05', cpu: 52, memory: 65, disk: 78, network: 31 },
    { timestamp: '00:10', cpu: 48, memory: 68, disk: 79, network: 28 },
    { timestamp: '00:15', cpu: 61, memory: 71, disk: 79, network: 42 },
    { timestamp: '00:20', cpu: 55, memory: 69, disk: 80, network: 35 },
    { timestamp: '00:25', cpu: 49, memory: 66, disk: 80, network: 29 },
    { timestamp: '00:30', cpu: 58, memory: 73, disk: 81, network: 38 },
  ]);

  const [alerts, setAlerts] = useState<AlertItem[]>([
    {
      id: '1',
      type: 'memory',
      level: 'warning',
      message: '内存使用率超过 70%',
      timestamp: '2024-01-15 10:30:00',
      resolved: false,
    },
    {
      id: '2',
      type: 'disk',
      level: 'critical',
      message: '磁盘空间不足，剩余空间少于 10%',
      timestamp: '2024-01-15 09:15:00',
      resolved: false,
    },
    {
      id: '3',
      type: 'service',
      level: 'warning',
      message: '数据库连接池接近满载',
      timestamp: '2024-01-15 08:45:00',
      resolved: true,
    },
  ]);

  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: '1',
      timestamp: '2024-01-15 10:35:22',
      level: 'error',
      message: '文档解析失败',
      source: 'DocumentParser',
      details: 'Failed to parse PDF document: invalid format',
    },
    {
      id: '2',
      timestamp: '2024-01-15 10:34:15',
      level: 'warn',
      message: '任务队列积压',
      source: 'TaskManager',
      details: 'Task queue has 150 pending tasks',
    },
    {
      id: '3',
      timestamp: '2024-01-15 10:33:08',
      level: 'info',
      message: '用户登录成功',
      source: 'AuthService',
      details: 'User admin logged in from 192.168.1.100',
    },
    {
      id: '4',
      timestamp: '2024-01-15 10:32:45',
      level: 'debug',
      message: '缓存更新完成',
      source: 'CacheManager',
      details: 'Updated 25 cache entries',
    },
  ]);

  useEffect(() => {
    dispatch(setPageTitle('系统监控'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/dashboard' },
      { title: '系统监控' },
    ]));
    
    // 加载系统数据
    dispatch(fetchSystemStats());
    dispatch(checkSystemHealth());
    dispatch(fetchSystemInfo());
  }, [dispatch]);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      dispatch(fetchSystemStats());
      dispatch(checkSystemHealth());
    }, refreshInterval * 1000);
    
    return () => clearInterval(interval);
  }, [dispatch, autoRefresh, refreshInterval]);

  // 手动刷新
  const handleRefresh = () => {
    dispatch(fetchSystemStats());
    dispatch(checkSystemHealth());
    dispatch(fetchSystemInfo());
    message.success('数据已刷新');
  };

  // 解决告警
  const handleResolveAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, resolved: true } : alert
    ));
    message.success('告警已解决');
  };

  // 查看日志详情
  const handleViewLogDetails = (log: LogEntry) => {
    Modal.info({
      title: '日志详情',
      width: 600,
      content: (
        <div>
          <p><strong>时间:</strong> {log.timestamp}</p>
          <p><strong>级别:</strong> <Tag color={getLogLevelColor(log.level)}>{log.level.toUpperCase()}</Tag></p>
          <p><strong>来源:</strong> {log.source}</p>
          <p><strong>消息:</strong> {log.message}</p>
          {log.details && (
            <div>
              <p><strong>详情:</strong></p>
              <pre style={{ background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                {log.details}
              </pre>
            </div>
          )}
        </div>
      ),
    });
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'red';
      case 'warn': return 'orange';
      case 'info': return 'blue';
      case 'debug': return 'gray';
      default: return 'default';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'cpu': return <CloudServerOutlined />;
      case 'memory': return <MemoryStickOutlined />;
      case 'disk': return <HddOutlined />;
      case 'network': return <WifiOutlined />;
      case 'service': return <SettingOutlined />;
      default: return <ExclamationCircleOutlined />;
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default: return <ExclamationCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  // 表格列定义
  const alertColumns: ColumnsType<AlertItem> = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Space>
          {getAlertIcon(type)}
          <span>{type}</span>
        </Space>
      ),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (level: string) => (
        <Tag color={level === 'critical' ? 'red' : 'orange'}>
          {level === 'critical' ? '严重' : '警告'}
        </Tag>
      ),
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
    },
    {
      title: '状态',
      dataIndex: 'resolved',
      key: 'resolved',
      render: (resolved: boolean) => (
        <Tag color={resolved ? 'green' : 'red'}>
          {resolved ? '已解决' : '未解决'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {!record.resolved && (
            <Button
              type="link"
              size="small"
              onClick={() => handleResolveAlert(record.id)}
            >
              解决
            </Button>
          )}
          <Button type="link" size="small">
            详情
          </Button>
        </Space>
      ),
    },
  ];

  const logColumns: ColumnsType<LogEntry> = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => (
        <Tag color={getLogLevelColor(level)}>
          {level.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 120,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewLogDetails(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  // 图表颜色
  const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d'];

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <Title level={2} className="mb-2">系统监控</Title>
          <Text type="secondary">实时监控系统运行状态和性能指标</Text>
        </div>
        <Space>
          <Select
            value={refreshInterval}
            onChange={setRefreshInterval}
            style={{ width: 120 }}
          >
            <Option value={10}>10秒</Option>
            <Option value={30}>30秒</Option>
            <Option value={60}>1分钟</Option>
            <Option value={300}>5分钟</Option>
          </Select>
          <Button
            type={autoRefresh ? 'primary' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '停止自动刷新' : '开启自动刷新'}
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 告警信息 */}
      {alerts.filter(alert => !alert.resolved).length > 0 && (
        <Alert
          message={`当前有 ${alerts.filter(alert => !alert.resolved).length} 个未解决的告警`}
          type="warning"
          showIcon
          className="mb-6"
          action={
            <Button size="small" type="text">
              查看全部
            </Button>
          }
        />
      )}

      <Tabs defaultActiveKey="overview">
        {/* 概览 */}
        <TabPane tab="系统概览" key="overview">
          {/* 系统状态卡片 */}
          <Row gutter={16} className="mb-6">
            <Col span={6}>
              <Card>
                <Statistic
                  title="CPU 使用率"
                  value={58}
                  suffix="%"
                  prefix={<CloudServerOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
                <Progress percent={58} showInfo={false} strokeColor="#1890ff" />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="内存使用率"
                  value={73}
                  suffix="%"
                  prefix={<MemoryStickOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
                <Progress percent={73} showInfo={false} strokeColor="#faad14" />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="磁盘使用率"
                  value={81}
                  suffix="%"
                  prefix={<HddOutlined />}
                  valueStyle={{ color: '#f5222d' }}
                />
                <Progress percent={81} showInfo={false} strokeColor="#f5222d" />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="网络流量"
                  value={38}
                  suffix="MB/s"
                  prefix={<WifiOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
                <div className="mt-2">
                  <Text type="secondary">上行: 15MB/s | 下行: 23MB/s</Text>
                </div>
              </Card>
            </Col>
          </Row>

          {/* 性能趋势图 */}
          <Row gutter={16} className="mb-6">
            <Col span={16}>
              <Card title="性能趋势" extra={
                <Select value={timeRange} onChange={setTimeRange} style={{ width: 100 }}>
                  <Option value="1h">1小时</Option>
                  <Option value="6h">6小时</Option>
                  <Option value="24h">24小时</Option>
                  <Option value="7d">7天</Option>
                </Select>
              }>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metricsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="cpu" stroke="#1890ff" name="CPU" />
                    <Line type="monotone" dataKey="memory" stroke="#faad14" name="内存" />
                    <Line type="monotone" dataKey="disk" stroke="#f5222d" name="磁盘" />
                    <Line type="monotone" dataKey="network" stroke="#52c41a" name="网络" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={8}>
              <Card title="服务状态">
                <List
                  dataSource={[
                    { name: '数据库', status: 'healthy' },
                    { name: '缓存服务', status: 'healthy' },
                    { name: '文件存储', status: 'warning' },
                    { name: '邮件服务', status: 'error' },
                    { name: '任务队列', status: 'healthy' },
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <Space>
                        {getHealthIcon(item.status)}
                        <span>{item.name}</span>
                        <Tag color={
                          item.status === 'healthy' ? 'green' :
                          item.status === 'warning' ? 'orange' : 'red'
                        }>
                          {item.status === 'healthy' ? '正常' :
                           item.status === 'warning' ? '警告' : '错误'}
                        </Tag>
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 告警管理 */}
        <TabPane tab={`告警 (${alerts.filter(a => !a.resolved).length})`} key="alerts">
          <Card title="系统告警" extra={
            <Space>
              <Button>导出告警</Button>
              <Button type="primary">告警设置</Button>
            </Space>
          }>
            <Table
              columns={alertColumns}
              dataSource={alerts}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        {/* 日志查看 */}
        <TabPane tab="系统日志" key="logs">
          <Card title="系统日志" extra={
            <Space>
              <Select placeholder="选择日志级别" style={{ width: 120 }} allowClear>
                <Option value="error">错误</Option>
                <Option value="warn">警告</Option>
                <Option value="info">信息</Option>
                <Option value="debug">调试</Option>
              </Select>
              <Select placeholder="选择来源" style={{ width: 150 }} allowClear>
                <Option value="DocumentParser">文档解析器</Option>
                <Option value="TaskManager">任务管理器</Option>
                <Option value="AuthService">认证服务</Option>
                <Option value="CacheManager">缓存管理器</Option>
              </Select>
              <RangePicker showTime />
              <Button icon={<DownloadOutlined />}>导出日志</Button>
            </Space>
          }>
            <Table
              columns={logColumns}
              dataSource={logs}
              rowKey="id"
              pagination={{ pageSize: 20 }}
              scroll={{ y: 400 }}
            />
          </Card>
        </TabPane>

        {/* 性能分析 */}
        <TabPane tab="性能分析" key="performance">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="资源使用分布">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'CPU', value: 58 },
                        { name: '内存', value: 73 },
                        { name: '磁盘', value: 81 },
                        { name: '网络', value: 38 },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label
                    >
                      {metricsData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="响应时间趋势">
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={[
                    { time: '00:00', api: 120, db: 45, cache: 12 },
                    { time: '00:05', api: 135, db: 52, cache: 15 },
                    { time: '00:10', api: 128, db: 48, cache: 13 },
                    { time: '00:15', api: 142, db: 58, cache: 18 },
                    { time: '00:20', api: 138, db: 55, cache: 16 },
                    { time: '00:25', api: 125, db: 49, cache: 14 },
                    { time: '00:30', api: 148, db: 62, cache: 19 },
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Area type="monotone" dataKey="api" stackId="1" stroke="#1890ff" fill="#1890ff" name="API响应" />
                    <Area type="monotone" dataKey="db" stackId="1" stroke="#52c41a" fill="#52c41a" name="数据库" />
                    <Area type="monotone" dataKey="cache" stackId="1" stroke="#faad14" fill="#faad14" name="缓存" />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default MonitoringPage;