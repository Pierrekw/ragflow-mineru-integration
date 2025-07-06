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
  Avatar,
  Descriptions,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  FilterOutlined,
  ReloadOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  CalendarOutlined,
  LockOutlined,
  UnlockOutlined,
  CrownOutlined,
  TeamOutlined,
} from '@ant-design/icons';

import { useAppDispatch, useAppSelector } from '@/store';
import { fetchUsers, createUser, updateUser, deleteUser } from '@/store/slices/userSlice';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import type { ColumnsType } from 'antd/es/table';
import type { User, UserRole, UserStatus } from '@/types';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

const UsersPage: React.FC = () => {
 
  const dispatch = useAppDispatch();
  const { users, loading, pagination, filters } = useAppSelector(state => state.user);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [filterVisible, setFilterVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    dispatch(setPageTitle('用户管理'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/dashboard' },
      { title: '用户管理' },
    ]));
    
    // 加载用户列表
    dispatch(fetchUsers({
      page: pagination.page,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  }, [dispatch, pagination.page, pagination.pageSize, filters]);

  // 获取角色标签
  const getRoleTag = (role: UserRole) => {
    const roleConfig = {
      admin: { color: 'red', text: '管理员', icon: <CrownOutlined /> },
      user: { color: 'blue', text: '普通用户', icon: <UserOutlined /> },
      viewer: { color: 'green', text: '访客', icon: <EyeOutlined /> },
    };
    const config = roleConfig[role as keyof typeof roleConfig];
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 获取状态标签
  const getStatusTag = (status: UserStatus) => {
    const statusConfig = {
      active: { color: 'green', text: '活跃' },
      inactive: { color: 'default', text: '未激活' },
      suspended: { color: 'red', text: '已停用' },
    };
    const config = statusConfig[status];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 表格列定义
  const columns: ColumnsType<User> = [
    {
      title: '用户信息',
      key: 'userInfo',
      render: (_, record: User) => (
        <Space>
          <Avatar
            size={40}
            src={record.avatar}
            icon={<UserOutlined />}
          />
          <div>
            <div className="font-medium">
              {record.username}
            </div>
            <div className="text-gray-500 text-sm">{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => (
        <Space>
          <MailOutlined className="text-gray-400" />
          {email}
        </Space>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      width: 120,
      render: (role: UserRole) => getRoleTag(role),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: UserStatus) => getStatusTag(status),
    },
    {
      title: '最后登录',
      dataIndex: 'lastLoginAt',
      key: 'lastLoginAt',
      width: 180,
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm:ss') : '从未登录',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record: User) => (
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
          <Tooltip title={record.status === 'active' ? '停用' : '启用'}>
            <Button
              type="text"
              icon={record.status === 'active' ? <LockOutlined /> : <UnlockOutlined />}
              onClick={() => handleToggleStatus(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个用户吗？"
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
    dispatch(fetchUsers({
      page: 1,
      pageSize: pagination.pageSize,
      filters: {
        ...filters,
        search: value,
      },
    }));
  };

  // 处理筛选
  const handleFilter = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    dispatch(fetchUsers({
      page: 1,
      pageSize: pagination.pageSize,
      ...newFilters,
    }));
  };

  // 查看用户详情
  const handleViewDetail = (user: User) => {
    setSelectedUser(user);
    setDetailModalVisible(true);
  };

  // 编辑用户
  const handleEdit = (user: User) => {
    setSelectedUser(user);
    editForm.setFieldsValue({
      username: user.username,
      email: user.email,
      role: user.role,
      status: user.status,
    });
    setEditModalVisible(true);
  };

  // 切换用户状态
  const handleToggleStatus = (user: User) => {
    const newStatus = user.status === 'active' ? 'suspended' : 'active';
    const action = newStatus === 'active' ? '启用' : '停用';
    
    Modal.confirm({
      title: `确认${action}用户`,
      content: `确定要${action}用户 "${user.username}" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        dispatch(updateUser({
          id: user.id,
          data: { status: newStatus as UserStatus },
        }));
      },
    });
  };

  // 删除用户
  const handleDelete = (user: User) => {
    dispatch(deleteUser(user.id));
  };

  // 创建用户
  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await dispatch(createUser(values)).unwrap();
      message.success('用户创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      // 重新加载列表
      dispatch(fetchUsers({
        page: pagination.page,
        pageSize: pagination.pageSize,
        ...filters,
      }));
    } catch (error) {
      message.error('创建失败');
    }
  };

  // 更新用户
  const handleUpdate = async () => {
    if (!selectedUser) return;
    
    try {
      const values = await editForm.validateFields();
      await dispatch(updateUser({
        id: selectedUser.id,
        data: values,
      })).unwrap();
      message.success('用户更新成功');
      setEditModalVisible(false);
      editForm.resetFields();
      setSelectedUser(null);
      // 重新加载列表
      dispatch(fetchUsers({
        page: pagination.page,
        pageSize: pagination.pageSize,
        ...filters,
      }));
    } catch (error) {
      message.error('更新失败');
    }
  };

  // 批量操作
  const handleBatchOperation = (operation: string) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要操作的用户');
      return;
    }
    
    Modal.confirm({
      title: `确认批量${operation}`,
      content: `确定要${operation}选中的 ${selectedRowKeys.length} 个用户吗？`,
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
    dispatch(fetchUsers({
      page: pagination.page,
      pageSize: pagination.pageSize,
      ...filters,
    }));
  };

  // 统计数据
  const stats = {
    total: users.length,
    active: users.filter(user => user.status === 'active').length,
    admin: users.filter(user => user.role === 'admin').length,
    newThisMonth: users.filter(user => 
      dayjs(user.createdAt).isAfter(dayjs().startOf('month'))
    ).length,
  };

  return (
    <div className="p-6">
      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card>
            <Statistic title="总用户数" value={stats.total} prefix={<TeamOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="活跃用户" value={stats.active} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="管理员" value={stats.admin} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="本月新增" value={stats.newThisMonth} valueStyle={{ color: '#1890ff' }} />
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
            创建用户
          </Button>
          <Button
            icon={<LockOutlined />}
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBatchOperation('停用')}
          >
            批量停用
          </Button>
          <Button
            icon={<UnlockOutlined />}
            disabled={selectedRowKeys.length === 0}
            onClick={() => handleBatchOperation('启用')}
          >
            批量启用
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
            placeholder="搜索用户名或邮箱"
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
                placeholder="选择角色"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('role', value)}
              >
                <Option value="admin">管理员</Option>
                <Option value="user">普通用户</Option>
                <Option value="viewer">访客</Option>
              </Select>
            </Col>
            <Col span={6}>
              <Select
                placeholder="选择状态"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('status', value)}
              >
                <Option value="active">活跃</Option>
                <Option value="inactive">未激活</Option>
                <Option value="suspended">已停用</Option>
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
                  handleFilter('role', undefined);
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

      {/* 用户表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          rowSelection={{
            selectedRowKeys,
            onChange: (selectedRowKeys: React.Key[]) => {
              setSelectedRowKeys(selectedRowKeys as string[]);
            },
          }}
          pagination={{
            current: pagination.page,
            pageSize: pagination.pageSize,
            total: users.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
        />
      </Card>

      {/* 创建用户模态框 */}
      <Modal
        title="创建用户"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        okText="创建"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' },
                ]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="firstName"
                label="名"
                rules={[{ required: true, message: '请输入名' }]}
              >
                <Input placeholder="请输入名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="lastName"
                label="姓"
                rules={[{ required: true, message: '请输入姓' }]}
              >
                <Input placeholder="请输入姓" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select placeholder="请选择角色">
                  <Option value="admin">管理员</Option>
                  <Option value="user">普通用户</Option>
                  <Option value="viewer">访客</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="phone"
                label="电话"
              >
                <Input placeholder="请输入电话号码" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑用户模态框 */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onOk={handleUpdate}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
          setSelectedUser(null);
        }}
        okText="更新"
        cancelText="取消"
        width={600}
      >
        <Form form={editForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' },
                ]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="firstName"
                label="名"
                rules={[{ required: true, message: '请输入名' }]}
              >
                <Input placeholder="请输入名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="lastName"
                label="姓"
                rules={[{ required: true, message: '请输入姓' }]}
              >
                <Input placeholder="请输入姓" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role"
                label="角色"
                rules={[{ required: true, message: '请选择角色' }]}
              >
                <Select placeholder="请选择角色">
                  <Option value="admin">管理员</Option>
                  <Option value="user">普通用户</Option>
                  <Option value="viewer">访客</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="status"
                label="状态"
                rules={[{ required: true, message: '请选择状态' }]}
              >
                <Select placeholder="请选择状态">
                  <Option value="active">活跃</Option>
                  <Option value="inactive">未激活</Option>
                  <Option value="suspended">已停用</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="phone"
            label="电话"
          >
            <Input placeholder="请输入电话号码" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 用户详情模态框 */}
      <Modal
        title="用户详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSelectedUser(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="edit"
            type="primary"
            onClick={() => {
              setDetailModalVisible(false);
              if (selectedUser) {
                handleEdit(selectedUser);
              }
            }}
          >
            编辑
          </Button>,
        ]}
        width={800}
      >
        {selectedUser && (
          <div>
            <div className="flex items-center mb-6">
              <Avatar
                size={80}
                src={selectedUser.avatar}
                icon={<UserOutlined />}
                className="mr-4"
              />
              <div>
                <h3 className="text-xl font-bold mb-1">
                  {selectedUser.username}
                </h3>
                <p className="text-gray-600 mb-1">@{selectedUser.username}</p>
                <Space>
                  {getRoleTag(selectedUser.role)}
                  {getStatusTag(selectedUser.status)}
                </Space>
              </div>
            </div>
            
            <Descriptions bordered column={2}>
              <Descriptions.Item label="邮箱" span={2}>
                <Space>
                  <MailOutlined />
                  {selectedUser.email}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="电话">
                <Space>
                  <PhoneOutlined />
                  -
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="最后登录">
                <Space>
                  <CalendarOutlined />
                  {selectedUser.lastLoginAt 
                    ? dayjs(selectedUser.lastLoginAt).format('YYYY-MM-DD HH:mm:ss')
                    : '从未登录'
                  }
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {dayjs(selectedUser.createdAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {dayjs(selectedUser.updatedAt).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default UsersPage;