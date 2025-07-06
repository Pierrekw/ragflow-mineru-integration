import React, { useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, Table, Tag, Space, Button } from 'antd';
import {
  FileTextOutlined,
  UserOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';

const DashboardPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector(state => state.auth);

  useEffect(() => {
    dispatch(setPageTitle('仪表板'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/dashboard' },
    ]));
  }, [dispatch]);

  // 模拟数据
  const stats = {
    totalDocuments: 1248,
    totalUsers: 156,
    todayUploads: 23,
    successRate: 94.5,
  };

  const recentDocuments = [
    {
      key: '1',
      name: '产品需求文档.pdf',
      status: 'completed',
      uploadTime: '2024-01-15 14:30',
      size: '2.3 MB',
      user: '张三',
    },
    {
      key: '2',
      name: '技术方案设计.docx',
      status: 'processing',
      uploadTime: '2024-01-15 14:25',
      size: '1.8 MB',
      user: '李四',
    },
    {
      key: '3',
      name: '用户手册.pdf',
      status: 'failed',
      uploadTime: '2024-01-15 14:20',
      size: '5.2 MB',
      user: '王五',
    },
    {
      key: '4',
      name: '会议纪要.txt',
      status: 'completed',
      uploadTime: '2024-01-15 14:15',
      size: '0.5 MB',
      user: '赵六',
    },
  ];

  const getStatusTag = (status: string) => {
    const statusMap = {
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      processing: { color: 'processing', icon: <ClockCircleOutlined />, text: '处理中' },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' },
    };
    const config = statusMap[status as keyof typeof statusMap];
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  const columns = [
    {
      title: '文档名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '上传时间',
      dataIndex: 'uploadTime',
      key: 'uploadTime',
    },
    {
      title: '文件大小',
      dataIndex: 'size',
      key: 'size',
    },
    {
      title: '上传者',
      dataIndex: 'user',
      key: 'user',
    },
  ];

  return (
    <div className="p-6">
      {/* 欢迎信息 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          欢迎回来，{user?.username}！
        </h1>
        <p className="text-gray-600">
          今天是 {new Date().toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long',
          })}
        </p>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总文档数"
              value={stats.totalDocuments}
              prefix={<FileTextOutlined className="text-blue-500" />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="用户总数"
              value={stats.totalUsers}
              prefix={<UserOutlined className="text-green-500" />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日上传"
              value={stats.todayUploads}
              prefix={<CloudUploadOutlined className="text-orange-500" />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats.successRate}
              suffix="%"
              prefix={<CheckCircleOutlined className="text-green-500" />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress
              percent={stats.successRate}
              showInfo={false}
              strokeColor="#52c41a"
              className="mt-2"
            />
          </Card>
        </Col>
      </Row>

      {/* 最近文档 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title="最近上传的文档"
            extra={
              <Space>
                <Button icon={<ReloadOutlined />} size="small">
                  刷新
                </Button>
                <Button type="primary" size="small">
                  查看全部
                </Button>
              </Space>
            }
          >
            <Table
              columns={columns}
              dataSource={recentDocuments}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Space direction="vertical" size="middle" className="w-full">
            {/* 系统状态 */}
            <Card title="系统状态" size="small">
              <Space direction="vertical" className="w-full">
                <div className="flex justify-between items-center">
                  <span>CPU 使用率</span>
                  <span>45%</span>
                </div>
                <Progress percent={45} size="small" />
                
                <div className="flex justify-between items-center">
                  <span>内存使用率</span>
                  <span>62%</span>
                </div>
                <Progress percent={62} size="small" status="active" />
                
                <div className="flex justify-between items-center">
                  <span>存储使用率</span>
                  <span>78%</span>
                </div>
                <Progress percent={78} size="small" strokeColor="#faad14" />
              </Space>
            </Card>

            {/* 快速操作 */}
            <Card title="快速操作" size="small">
              <Space direction="vertical" className="w-full">
                <Button type="primary" block icon={<CloudUploadOutlined />}>
                  上传文档
                </Button>
                <Button block icon={<FileTextOutlined />}>
                  查看文档
                </Button>
                <Button block icon={<UserOutlined />}>
                  用户管理
                </Button>
              </Space>
            </Card>
          </Space>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;