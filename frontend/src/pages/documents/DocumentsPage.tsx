import React, { useEffect, useState } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Upload,
  Modal,
  message,
  Tag,
  Tooltip,
  Dropdown,
  Progress,
  Card,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  EditOutlined,
  ReloadOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FileImageOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store';
import { fetchDocuments, deleteDocument, uploadDocument } from '@/store/slices/documentSlice';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { ColumnsType } from 'antd/es/table';
import type { Document, DocumentStatus } from '@/types';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Dragger } = Upload;

const DocumentsPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { documents, loading, pagination, filters } = useAppSelector(state => state.document);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [filterVisible, setFilterVisible] = useState(false);

  useEffect(() => {
    dispatch(setPageTitle('文档管理'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/dashboard' },
      { title: '文档管理' },
    ]));
    
    // 加载文档列表
    dispatch(fetchDocuments({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  }, [dispatch, pagination.current, pagination.pageSize, filters]);

  // 获取文件图标
  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
    if (type.includes('word') || type.includes('doc')) return <FileWordOutlined style={{ color: '#1890ff' }} />;
    if (type.includes('excel') || type.includes('sheet')) return <FileExcelOutlined style={{ color: '#52c41a' }} />;
    if (type.includes('image')) return <FileImageOutlined style={{ color: '#722ed1' }} />;
    return <FileTextOutlined style={{ color: '#8c8c8c' }} />;
  };

  // 获取状态标签
  const getStatusTag = (status: DocumentStatus) => {
    const statusConfig = {
      uploaded: { color: 'blue', text: '已上传' },
      processing: { color: 'orange', text: '处理中' },
      processed: { color: 'green', text: '已处理' },
      failed: { color: 'red', text: '处理失败' },
    };
    const config = statusConfig[status];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 表格列定义
  const columns: ColumnsType<Document> = [
    {
      title: '文档名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Document) => (
        <Space>
          {getFileIcon(record.type)}
          <span
            className="cursor-pointer text-blue-600 hover:text-blue-800"
            onClick={() => navigate(`/documents/${record.id}`)}
          >
            {text}
          </span>
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: DocumentStatus) => getStatusTag(status),
    },
    {
      title: '上传时间',
      dataIndex: 'uploadedAt',
      key: 'uploadedAt',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '处理时间',
      dataIndex: 'processedAt',
      key: 'processedAt',
      width: 180,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record: Document) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/documents/${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="下载">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 处理搜索
  const handleSearch = (value: string) => {
    dispatch(fetchDocuments({
      page: 1,
      pageSize: pagination.pageSize,
      ...filters,
      search: value,
    }));
  };

  // 处理筛选
  const handleFilter = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    dispatch(fetchDocuments({
      page: 1,
      pageSize: pagination.pageSize,
      ...newFilters,
    }));
  };

  // 处理上传
  const handleUpload = (info: any) => {
    const { status, response } = info.file;
    if (status === 'done') {
      message.success(`${info.file.name} 上传成功`);
      setUploadModalVisible(false);
      // 重新加载文档列表
      dispatch(fetchDocuments({
        page: pagination.current,
        pageSize: pagination.pageSize,
        ...filters,
      }));
    } else if (status === 'error') {
      message.error(`${info.file.name} 上传失败`);
    }
  };

  // 处理编辑
  const handleEdit = (record: Document) => {
    // TODO: 实现编辑功能
    message.info('编辑功能开发中');
  };

  // 处理下载
  const handleDownload = (record: Document) => {
    // TODO: 实现下载功能
    message.info('下载功能开发中');
  };

  // 处理删除
  const handleDelete = (record: Document) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文档 "${record.name}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        dispatch(deleteDocument(record.id));
      },
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的文档');
      return;
    }
    
    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 个文档吗？`,
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
    dispatch(fetchDocuments({
      page: pagination.current,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  };

  // 统计数据
  const stats = {
    total: documents.length,
    processed: documents.filter(doc => doc.status === 'processed').length,
    processing: documents.filter(doc => doc.status === 'processing').length,
    failed: documents.filter(doc => doc.status === 'failed').length,
  };

  return (
    <div className="p-6">
      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card>
            <Statistic title="总文档数" value={stats.total} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已处理" value={stats.processed} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="处理中" value={stats.processing} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="处理失败" value={stats.failed} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <div className="mb-4 flex justify-between items-center">
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setUploadModalVisible(true)}
          >
            上传文档
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            disabled={selectedRowKeys.length === 0}
            onClick={handleBatchDelete}
          >
            批量删除
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </Space>
        
        <Space>
          <Search
            placeholder="搜索文档名称"
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
                <Option value="uploaded">已上传</Option>
                <Option value="processing">处理中</Option>
                <Option value="processed">已处理</Option>
                <Option value="failed">处理失败</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Select
                placeholder="选择文件类型"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('type', value)}
              >
                <Option value="pdf">PDF</Option>
                <Option value="doc">Word</Option>
                <Option value="excel">Excel</Option>
                <Option value="image">图片</Option>
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
                  handleFilter('type', undefined);
                  handleFilter('dateRange', undefined);
                }}
              >
                重置
              </Button>
            </Col>
          </Row>
        </Card>
      )}

      {/* 文档表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={documents}
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

      {/* 上传模态框 */}
      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Dragger
          name="files"
          multiple
          action="/api/documents/upload"
          onChange={handleUpload}
          accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md,.jpg,.jpeg,.png,.gif"
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或批量上传。支持 PDF、Word、Excel、PowerPoint、文本、图片等格式。
          </p>
        </Dragger>
      </Modal>
    </div>
  );
};

export default DocumentsPage;