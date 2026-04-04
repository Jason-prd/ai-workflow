import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography, Divider, message, Switch, Space } from 'antd';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftOutlined, SaveOutlined, KeyOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';

const { Title, Text } = Typography;

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);

  const handleSave = async (_values: unknown) => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 500));
    setLoading(false);
    message.success('Settings saved');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-4">
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/workflows')} type="text" />
            <Title level={5} className="!mb-0">设置</Title>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* User Info */}
        <Card>
          <Title level={5}>用户信息</Title>
          <Form layout="vertical" initialValues={{ name: user?.name, email: user?.email }}>
            <Form.Item name="name" label="姓名">
              <Input />
            </Form.Item>
            <Form.Item name="email" label="邮箱">
              <Input disabled />
            </Form.Item>
          </Form>
        </Card>

        {/* OpenAI Configuration */}
        <Card>
          <Title level={5} className="flex items-center gap-2">
            <KeyOutlined /> API 配置
          </Title>
          <Divider />
          <Form layout="vertical" onFinish={handleSave}>
            <Form.Item
              name="openaiApiKey"
              label="OpenAI API Key"
              extra="用于调用 GPT-4o 等大语言模型"
            >
              <Input.Password placeholder="sk-..." />
            </Form.Item>
            <Form.Item className="!mb-0">
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
                保存
              </Button>
            </Form.Item>
          </Form>
        </Card>

        {/* Feishu Configuration */}
        <Card>
          <Title level={5}>飞书集成配置</Title>
          <Text type="secondary" className="block mb-4">
            配置飞书企业应用以启用飞书消息和文档功能
          </Text>
          <Divider />
          <Form layout="vertical" onFinish={handleSave}>
            <Form.Item
              name="feishuAppId"
              label="飞书应用 App ID"
              extra="在飞书开放平台创建应用后获取"
            >
              <Input placeholder="cli_xxx" />
            </Form.Item>
            <Form.Item
              name="feishuAppSecret"
              label="飞书应用 App Secret"
              extra="在飞书开放平台创建应用后获取"
            >
              <Input.Password placeholder="应用密钥" />
            </Form.Item>
            <Form.Item className="!mb-0">
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
                保存
              </Button>
            </Form.Item>
          </Form>
        </Card>

        {/* Notifications */}
        <Card>
          <Title level={5}>通知设置</Title>
          <Divider />
          <Space direction="vertical" className="w-full">
            <div className="flex items-center justify-between">
              <div>
                <Text strong>执行失败通知</Text>
                <br />
                <Text type="secondary" className="text-sm">工作流执行失败时发送通知</Text>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Text strong>执行成功通知</Text>
                <br />
                <Text type="secondary" className="text-sm">工作流执行成功时发送通知</Text>
              </div>
              <Switch />
            </div>
          </Space>
        </Card>
      </main>
    </div>
  );
};

export default SettingsPage;
