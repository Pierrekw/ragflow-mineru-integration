import React, { useEffect, useState } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Modal,
  message,
  Tag,
  Tooltip,
  Progress,
  Card,
  Row,
  Col,
  Statistic,
  Descriptions,
  Timeline,
  Alert,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  RedoOutlined,
  EyeOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  fetchTasks,
  createTask,
  updateTask,
  deleteTask,
  cancelTask,
  retryTask,
} from '@/store/slices/taskSlice';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { ColumnsType } from 'antd/es/table';
import type { Task, TaskStatus, TaskType } from '@/types';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

const TasksPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { tasks, loading, pagination, filters } = useAppSelector(state => state.task);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [filterVisible, setFilterVisible] = useState(false);
  const [taskDetailVisible, setTaskDetailVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  useEffect(() => {
    dispatch(setPageTitle('任务管理'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/dashboard' },
      { title: '任务管理' },
    ]));
    
    // 加载任务列表
    dispatch(fetchTasks({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  }, [dispatch, pagination.current, pagination.pageSize, filters]);

  // 获取任务类型标签
  const getTaskTypeTag = (type: TaskType) => {
    const typeConfig = {
      document_parse: { color: 'blue', text: '文档解析' },
      knowledge_base_build: { color: 'green', text: '知识库构建' },
      data_import: { color: 'orange', text: '数据导入' },
      data_export: { color: 'purple', text: '数据导出' },
      system_backup: { color: 'cyan', text: '系统备份' },
      system_maintenance: { color: 'red', text: '系统维护' },
    };
    const config = typeConfig[type];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 获取状态标签和图标
  const getStatusTag = (status: TaskStatus) => {
    const statusConfig = {
      pending: { color: 'default', text: '等待中', icon: <ClockCircleOutlined /> },
      running: { color: 'processing', text: '运行中', icon: <SyncOutlined spin /> },
      completed: { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', text: '失败', icon: <ExclamationCircleOutlined /> },
      cancelled: { color: 'warning', text: '已取消', icon: <StopOutlined /> },
    };
    const config = statusConfig[status];
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 计算任务进度
  const getTaskProgress = (task: Task) => {
    if (task.status === 'completed') return 100;
    if (task.status === 'failed' || task.status === 'cancelled') return 0;
    if (task.status === 'running') {
      // 根据任务的实际进度计算
      return task.progress || 0;
    }
    return 0;
  };

  // 表格列定义
  const columns: ColumnsType<Task> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Task) => (
        <span
          className="cursor-pointer text-blue-600 hover:text-blue-800"
          onClick={() => handleViewDetail(record)}
        >
          {text}
        </span>
      ),
    },
    {
      title: '任务类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: TaskType) => getTaskTypeTag(type),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TaskStatus) => getStatusTag(status),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (_, record: Task) => {
        const progress = getTaskProgress(record);
        return (
          <Progress
            percent={progress}
            size="small"
            status={record.status === 'failed' ? 'exception' : 'normal'}
          />
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '完成时间',
      dataIndex: 'completedAt',
      key: 'completedAt',
      width: 180,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record: Task) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          {record.status === 'pending' && (
            <Tooltip title="开始任务">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStartTask(record)}
              />
            </Tooltip>
          )}
          {record.status === 'running' && (
            <Tooltip title="取消任务">
              <Button
                type="text"
                icon={<StopOutlined />}
                onClick={() => handleCancelTask(record)}
              />
            </Tooltip>
          )}
          {record.status === 'failed' && (
            <Tooltip title="重试任务">
              <Button
                type="text"
                icon={<RedoOutlined />}
                onClick={() => handleRetryTask(record)}
              />
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteTask(record)}
              disabled={record.status === 'running'}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 处理搜索
  const handleSearch = (value: string) => {
    dispatch(fetchTasks({
      page: 1,
      pageSize: pagination.pageSize,
      ...filters,
      search: value,
    }));
  };

  // 处理筛选
  const handleFilter = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    dispatch(fetchTasks({
      page: 1,
      pageSize: pagination.pageSize,
      ...newFilters,
    }));
  };

  // 查看任务详情
  const handleViewDetail = (task: Task) => {
    setSelectedTask(task);
    setTaskDetailVisible(true);
  };

  // 开始任务
  const handleStartTask = (task: Task) => {
    // TODO: 实现开始任务功能
    message.info('开始任务功能开发中');
  };

  // 取消任务
  const handleCancelTask = (task: Task) => {
    Modal.confirm({
      title: '确认取消',
      content: `确定要取消任务 "${task.name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        dispatch(cancelTask(task.id));
      },
    });
  };

  // 重试任务
  const handleRetryTask = (task: Task) => {
    dispatch(retryTask(task.id));
  };

  // 删除任务
  const handleDeleteTask = (task: Task) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除任务 "${task.name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        dispatch(deleteTask(task.id));
      },
    });
  };

  // 批量操作
  const handleBatchOperation = (operation: string) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要操作的任务');
      return;
    }
    
    Modal.confirm({
      title: `确认批量${operation}`,
      content: `确定要${operation}选中的 ${selectedRowKeys.length} 个任务吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        // TODO: 实现批量操作
        message.success(`批量${operation}成功`);
        setSelectedRowKeys([]);
      },
    });
  };

  // 刷新数据
  const handleRefresh = () => {
    dispatch(fetchTasks({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  };

  // 统计数据
  const stats = {
    total: tasks.length,
    pending: tasks.filter(task => task.status === 'pending').length,
    running: tasks.filter(task => task.status === 'running').length,
    completed: tasks.filter(task => task.status === 'completed').length,
    failed: tasks.filter(task => task.status === 'failed').length,
  };

  return (
    <div className="p-6">
      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={5}>
          <Card>
            <Statistic title="总任务数" value={stats.total} prefix={<ClockCircleOutlined />} />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic title="等待中" value={stats.pending} valueStyle={{ color: '#8c8c8c' }} />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic title="运行中" value={stats.running} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic title="已完成" value={stats.completed} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="失败" value={stats.failed} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <div className="mb-4 flex justify-between items-center">
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            创建任务
          </Button>
          <Button
            icon={<PlayCircleOutlined />}
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBatchOperation('开始')}
          >
            批量开始
          </Button>
          <Button
            icon={<StopOutlined />}
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBatchOperation('取消')}
          >
            批量取消
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBatchOperation('删除')}
          >
            批量删除
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </Space>
        
        <Space>
          <Search
            placeholder="搜索任务名称"
            allowClear
            style={{ width: 250 }}
            onSearch={handleSearch}
          />
          <Button
            icon={<FilterOutlined />}
            onClick={() => setFilterVisible(!filterVisible)}
          >
            筛选
          </Button>
        </Space>
      </div>

      {/* 筛选面板 */}
      {filterVisible && (
        <Card className="mb-4">
          <Row gutter={16}>
            <Col span={6}>
              <Select
                placeholder="选择任务类型"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('type', value)}
              >
                <Option value="document_parse">文档解析</Option>
                <Option value="knowledge_base_build">知识库构建</Option>
                <Option value="data_import">数据导入</Option>
                <Option value="data_export">数据导出</Option>
                <Option value="system_backup">系统备份</Option>
                <Option value="system_maintenance">系统维护</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Select
                placeholder="选择状态"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('status', value)}
              >
                <Option value="pending">等待中</Option>
                <Option value="running">运行中</Option>
                <Option value="completed">已完成</Option>
                <Option value="failed">失败</Option>
                <Option value="cancelled">已取消</Option>
              </Select>
            </Col>
            <Col span={8}>
              <RangePicker
                style={{ width: '100%' }}
                onChange={(dates) => handleFilter('dateRange', dates)}
              />
            </Col>
            <Col span={4}>
              <Button
                block
                onClick={() => {
                  handleFilter('type', undefined);
                  handleFilter('status', undefined);
                  handleFilter('dateRange', undefined);
                }}
              >
                重置
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      {/* 任务表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 任务详情模态框 */}
      <Modal
        title="任务详情"
        open={taskDetailVisible}
        onCancel={() => setTaskDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTask && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="任务名称" span={2}>
                {selectedTask.name}
              </Descriptions.Item>
              <Descriptions.Item label="任务类型">
                {getTaskTypeTag(selectedTask.type)}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {getStatusTag(selectedTask.status)}
              </Descriptions.Item>
              <Descriptions.Item label="进度">
                <Progress percent={getTaskProgress(selectedTask)} />
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedTask.createdAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {selectedTask.startedAt ? dayjs(selectedTask.startedAt).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {selectedTask.completedAt ? dayjs(selectedTask.completedAt).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedTask.description || '无描述'}
              </Descriptions.Item>
            </Descriptions>
            
            {selectedTask.error && (
              <Alert
                message="错误信息"
                description={selectedTask.error.message}
                type="error"
                showIcon
                className="mt-4"
              />
            )}
            
            {/* 任务日志时间线 */}
            <div className="mt-6">
              <h4>任务日志</h4>
              <Timeline>
                <Timeline.Item color="blue">
                  任务创建 - {dayjs(selectedTask.createdAt).format('YYYY-MM-DD HH:mm:ss')}
                </Timeline.Item>
                {selectedTask.startedAt && (
                  <Timeline.Item color="green">
                    任务开始 - {dayjs(selectedTask.startedAt).format('YYYY-MM-DD HH:mm:ss')}
                  </Timeline.Item>
                )}
                {selectedTask.completedAt && (
                  <Timeline.Item color={selectedTask.status === 'completed' ? 'green' : 'red'}>
                    任务{selectedTask.status === 'completed' ? '完成' : '失败'} - {dayjs(selectedTask.completedAt).format('YYYY-MM-DD HH:mm:ss')}
                  </Timeline.Item>
                )}
              </Timeline>
            </div>
          </div>
        )}
      </Modal>

      {/* 创建任务模态框 */}
      <Modal
        title="创建任务"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={600}
      >
        {/* TODO: 实现创建任务表单 */}
        <div className="text-center py-8">
          <p>创建任务表单开发中...</p>
        </div>
      </Modal>
    </div>
  );
};

export default TasksPage;