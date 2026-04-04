import React from 'react';
import { Form, Input, Button, Card, Typography, message, Divider } from 'antd';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();
  const [form] = Form.useForm();

  const onFinish = async (values: { email: string; password: string }) => {
    try {
      await login(values.email, values.password);
      message.success('登录成功！');
      navigate('/workflows');
    } catch {
      message.error('登录失败，请检查邮箱和密码');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg rounded-xl" bordered={false}>
        <div className="text-center mb-8">
          <Title level={2} className="!mb-1 !text-indigo-700">
            AI 自动化工作流
          </Title>
          <Text type="secondary">登录到您的账户</Text>
        </div>

        <Form
          name="login"
          form={form}
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<UserOutlined className="text-gray-400" />}
              placeholder="邮箱"
              size="large"
              autoComplete="email"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-gray-400" />}
              placeholder="密码"
              size="large"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item className="!mb-0">
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading}
              block
              size="large"
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>
          <Text type="secondary" className="text-xs">或</Text>
        </Divider>

        <div className="text-center">
          <Text>还没有账户？</Text>
          <Link to="/register" className="text-indigo-600 hover:text-indigo-500 font-medium ml-1">
            立即注册
          </Link>
        </div>


      </Card>
    </div>
  );
};

export default LoginPage;
