import React, { useEffect } from 'react';
import {
  Card,
  Button,
  Typography,
  Tag,
  Modal,
  Form,
  Input,
  message,
  Dropdown,
  Space,
  Spin,
  Empty,
} from 'antd';
import {
  useNavigate,
} from 'react-router-dom';
import {
  PlusOutlined,
  PlayCircleOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  UserOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useWorkflowStore } from '../stores/workflowStore';
import { useAuthStore } from '../stores/authStore';
import type { Workflow } from '../types';

const { Title, Paragraph } = Typography;

const WorkflowListPage: React.FC = () => {
  const navigate = useNavigate();
  const { workflows, createWorkflow, deleteWorkflow, setCurrentWorkflow, loadWorkflows, isLoading } =
    useWorkflowStore();
  const { user, logout } = useAuthStore();
  const [modalVisible, setModalVisible] = React.useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadWorkflows();
  }, [loadWorkflows]);

  const handleCreate = (values: { name: string; description?: string }) => {
    const workflow = createWorkflow(values.name, values.description);
    setCurrentWorkflow(workflow);
    setModalVisible(false);
    form.resetFields();
    navigate(`/workflows/${workflow.id}/edit`);
  };

  const handleEdit = (workflow: Workflow) => {
    setCurrentWorkflow(workflow);
    navigate(`/workflows/${workflow.id}/edit`);
  };

  const handleRun = (workflow: Workflow) => {
    message.info(`运行工作流: ${workflow.name}`);
  };

  const handleDelete = (workflow: Workflow) => {
    Modal.confirm({
      title: '删除工作流',
      content: `确定要删除 "${workflow.name}" 吗？此操作不可撤销。`,
      okText: '删除',
      okType: 'danger',
      onOk: () => {
        deleteWorkflow(workflow.id);
        message.success('工作流已删除');
      },
    });
  };

  const getTriggerIcon = (type: 'manual' | 'cron') => {
    return type === 'manual' ? <UserOutlined /> : <ClockCircleOutlined />;
  };

  const getTriggerLabel = (type: 'manual' | 'cron') => {
    return type === 'manual' ? '手动触发' : '定时触发';
  };

  const userMenuItems = [
    {
      key: 'settings',
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      label: '退出登录',
      onClick: logout,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <ThunderboltOutlined className="text-2xl text-indigo-600 mr-2" />
              <Title level={4} className="!mb-0 !text-gray-800">
                AI 自动化工作流
              </Title>
            </div>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => loadWorkflows()}
                loading={isLoading}
                title="刷新"
              />
              <span className="text-gray-600 text-sm">{user?.name}</span>
              <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
                <Button shape="circle" icon={<UserOutlined />} />
              </Dropdown>
            </Space>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <Title level={3} className="!mb-0">
            我的工作流
          </Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="large"
            onClick={() => setModalVisible(true)}
          >
            新建工作流
          </Button>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center py-24">
            <Spin size="large" tip="加载中..." />
          </div>
        ) : workflows.length === 0 ? (
          <Card className="text-center py-16">
            <Empty description="还没有工作流，点击上方按钮创建第一个" />
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflows.map((workflow) => (
              <Card
                key={workflow.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleEdit(workflow)}
                actions={[
                  <Button
                    key="run"
                    type="text"
                    icon={<PlayCircleOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRun(workflow);
                    }}
                  >
                    运行
                  </Button>,
                  <Button
                    key="delete"
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(workflow);
                    }}
                  >
                    删除
                  </Button>,
                ]}
              >
                <Card.Meta
                  title={
                    <Space>
                      <span className="text-lg">{workflow.name}</span>
                      <Tag color={workflow.status === 'published' ? 'green' : 'orange'}>
                        {workflow.status === 'published' ? '已发布' : '草稿'}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div className="mt-2">
                      {workflow.description && (
                        <Paragraph
                          type="secondary"
                          ellipsis={{ rows: 2 }}
                          className="!mb-2 !text-sm"
                        >
                          {workflow.description}
                        </Paragraph>
                      )}
                      <Space className="mt-2">
                        <Tag icon={getTriggerIcon(workflow.trigger.type)}>
                          {getTriggerLabel(workflow.trigger.type)}
                        </Tag>
                      </Space>
                      <div className="mt-2 text-xs text-gray-400">
                        最后更新: {new Date(workflow.updatedAt).toLocaleDateString('zh-CN')}
                      </div>
                    </div>
                  }
                />
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      <Modal
        title="新建工作流"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="工作流名称"
            rules={[{ required: true, message: '请输入工作流名称' }]}
          >
            <Input placeholder="例如：周报自动生成器" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="简要描述这个工作流的用途..." />
          </Form.Item>
          <Form.Item className="!mb-0">
            <Space className="w-full justify-end">
              <Button
                onClick={() => {
                  setModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建并编辑
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default WorkflowListPage;
