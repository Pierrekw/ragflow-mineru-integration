import React, { useEffect, useState } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Modal,
  Form,
  message,
  Tag,
  Tooltip,
  Card,
  Row,
  Col,
  Statistic,
  Descriptions,
  List,
  Avatar,
  Popconfirm,
  Switch,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  ShareAltOutlined,
  CopyOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  SettingOutlined,
  ExportOutlined,
  ImportOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  fetchKnowledgeBases,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
} from '@/store/slices/knowledgeBaseSlice';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { ColumnsType } from 'antd/es/table';
import type { KnowledgeBase, KnowledgeBaseStatus } from '@/types';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const KnowledgeBasePage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { knowledgeBases, loading, pagination, filters } = useAppSelector(state => state.knowledgeBase);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [filterVisible, setFilterVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    dispatch(setPageTitle('知识库管理'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/dashboard' },
      { title: '知识库管理' },
    ]));
    
    // 加载知识库列表
    dispatch(fetchKnowledgeBases({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  }, [dispatch, pagination.current, pagination.pageSize, filters]);

  // 获取状态标签
  const getStatusTag = (status: KnowledgeBaseStatus) => {
    const statusConfig = {
      active: { color: 'green', text: '活跃' },
      building: { color: 'blue', text: '构建中' },
      inactive: { color: 'default', text: '未激活' },
      error: { color: 'red', text: '错误' },
    };
    const config = statusConfig[status];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 表格列定义
  const columns: ColumnsType<KnowledgeBase> = [
    {
      title: '知识库名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: KnowledgeBase) => (
        <Space>
          <DatabaseOutlined style={{ color: '#1890ff' }} />
          <span
            className="cursor-pointer text-blue-600 hover:text-blue-800"
            onClick={() => handleViewDetail(record)}
          >
            {text}
          </span>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: KnowledgeBaseStatus) => getStatusTag(status),
    },
    {
      title: '文档数量',
      dataIndex: 'documentCount',
      key: 'documentCount',
      width: 100,
      render: (count: number) => (
        <Space>
          <FileTextOutlined />
          {count}
        </Space>
      ),
    },
    {
      title: '是否公开',
      dataIndex: 'isPublic',
      key: 'isPublic',
      width: 100,
      render: (isPublic: boolean) => (
        <Tag color={isPublic ? 'green' : 'default'}>
          {isPublic ? '公开' : '私有'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_, record: KnowledgeBase) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="管理文档">
            <Button
              type="text"
              icon={<FileTextOutlined />}
              onClick={() => navigate(`/knowledge-base/${record.id}/documents`)}
            />
          </Tooltip>
          <Tooltip title="设置">
            <Button
              type="text"
              icon={<SettingOutlined />}
              onClick={() => navigate(`/knowledge-base/${record.id}/settings`)}
            />
          </Tooltip>
          <Tooltip title="分享">
            <Button
              type="text"
              icon={<ShareAltOutlined />}
              onClick={() => handleShare(record)}
            />
          </Tooltip>
          <Tooltip title="复制">
            <Button
              type="text"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个知识库吗？"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 处理搜索
  const handleSearch = (value: string) => {
    dispatch(fetchKnowledgeBases({
      page: 1,
      pageSize: pagination.pageSize,
      ...filters,
      search: value,
    }));
  };

  // 处理筛选
  const handleFilter = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    dispatch(fetchKnowledgeBases({
      page: 1,
      pageSize: pagination.pageSize,
      ...newFilters,
    }));
  };

  // 查看详情
  const handleViewDetail = (kb: KnowledgeBase) => {
    setSelectedKB(kb);
    setDetailModalVisible(true);
  };

  // 编辑知识库
  const handleEdit = (kb: KnowledgeBase) => {
    setSelectedKB(kb);
    editForm.setFieldsValue({
      name: kb.name,
      description: kb.description,
      isPublic: kb.isPublic,
    });
    setEditModalVisible(true);
  };

  // 删除知识库
  const handleDelete = (kb: KnowledgeBase) => {
    dispatch(deleteKnowledgeBase(kb.id));
  };

  // 分享知识库
  const handleShare = (kb: KnowledgeBase) => {
    // TODO: 实现分享功能
    message.info('分享功能开发中');
  };

  // 复制知识库
  const handleCopy = (kb: KnowledgeBase) => {
    // TODO: 实现复制功能
    message.info('复制功能开发中');
  };

  // 创建知识库
  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await dispatch(createKnowledgeBase(values)).unwrap();
      message.success('知识库创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      // 重新加载列表
      dispatch(fetchKnowledgeBases({
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...filters,
      }));
    } catch (error) {
      message.error('创建失败');
    }
  };

  // 更新知识库
  const handleUpdate = async () => {
    if (!selectedKB) return;
    
    try {
      const values = await editForm.validateFields();
      await dispatch(updateKnowledgeBase({
        id: selectedKB.id,
        data: values,
      })).unwrap();
      message.success('知识库更新成功');
      setEditModalVisible(false);
      editForm.resetFields();
      setSelectedKB(null);
      // 重新加载列表
      dispatch(fetchKnowledgeBases({
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...filters,
      }));
    } catch (error) {
      message.error('更新失败');
    }
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的知识库');
      return;
    }
    
    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个知识库吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        // TODO: 实现批量删除
        message.success('批量删除成功');
        setSelectedRowKeys([]);
      },
    });
  };

  // 刷新数据
  const handleRefresh = () => {
    dispatch(fetchKnowledgeBases({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  };

  // 统计数据
  const stats = {
    total: knowledgeBases.length,
    active: knowledgeBases.filter(kb => kb.status === 'active').length,
    building: knowledgeBases.filter(kb => kb.status === 'building').length,
    public: knowledgeBases.filter(kb => kb.isPublic).length,
  };

  return (
    <div className="p-6">
      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card>
            <Statistic title="总知识库数" value={stats.total} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="活跃" value={stats.active} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="构建中" value={stats.building} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="公开" value={stats.public} valueStyle={{ color: '#722ed1' }} />
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
            创建知识库
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            disabled={selectedRowKeys.length === 0}
            onClick={handleBatchDelete}
          >
            批量删除
          </Button>
          <Button icon={<ImportOutlined />}>
            导入
          </Button>
          <Button icon={<ExportOutlined />}>
            导出
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </Space>
        
        <Space>
          <Search
            placeholder="搜索知识库名称"
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
                placeholder="选择状态"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('status', value)}
              >
                <Option value="active">活跃</Option>
                <Option value="building">构建中</Option>
                <Option value="inactive">未激活</Option>
                <Option value="error">错误</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Select
                placeholder="选择可见性"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('isPublic', value)}
              >
                <Option value={true}>公开</Option>
                <Option value={false}>私有</Option>
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
                  handleFilter('status', undefined);
                  handleFilter('isPublic', undefined);
                  handleFilter('dateRange', undefined);
                }}
              >
                重置
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      {/* 知识库表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={knowledgeBases}
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

      {/* 创建知识库模态框 */}
      <Modal
        title="创建知识库"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[{ required: true, message: '请输入知识库名称' }]}
          >
            <Input placeholder="请输入知识库名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={4} placeholder="请输入知识库描述" />
          </Form.Item>
          <Form.Item
            name="isPublic"
            label="是否公开"
            valuePropName="checked"
          >
            <Switch checkedChildren="公开" unCheckedChildren="私有" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑知识库模态框 */}
      <Modal
        title="编辑知识库"
        open={editModalVisible}
        onOk={handleUpdate}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
          setSelectedKB(null);
        }}
        okText="更新"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical">
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[{ required: true, message: '请输入知识库名称' }]}
          >
            <Input placeholder="请输入知识库名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={4} placeholder="请输入知识库描述" />
          </Form.Item>
          <Form.Item
            name="isPublic"
            label="是否公开"
            valuePropName="checked"
          >
            <Switch checkedChildren="公开" unCheckedChildren="私有" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 知识库详情模态框 */}
      <Modal
        title="知识库详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSelectedKB(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="manage"
            type="primary"
            onClick={() => {
              if (selectedKB) {
                navigate(`/knowledge-base/${selectedKB.id}/documents`);
              }
            }}
          >
            管理文档
          </Button>,
        ]}
        width={800}
      >
        {selectedKB && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="知识库名称" span={2}>
                {selectedKB.name}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {getStatusTag(selectedKB.status)}
              </Descriptions.Item>
              <Descriptions.Item label="可见性">
                <Tag color={selectedKB.isPublic ? 'green' : 'default'}>
                  {selectedKB.isPublic ? '公开' : '私有'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="文档数量">
                {selectedKB.documentCount}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedKB.createdAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {dayjs(selectedKB.updatedAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedKB.description || '无描述'}
              </Descriptions.Item>
            </Descriptions>
            
            {/* 最近文档 */}
            <div className="mt-6">
              <h4>最近添加的文档</h4>
              <List
                size="small"
                dataSource={[]} // TODO: 从API获取最近文档
                renderItem={(item: any) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Avatar icon={<FileTextOutlined />} />}
                      title={item.name}
                      description={`添加时间: ${dayjs(item.createdAt).format('YYYY-MM-DD HH:mm:ss')}`}
                    />
                  </List.Item>
                )}
                locale={{ emptyText: '暂无文档' }}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default KnowledgeBasePage;