import React from 'react';
import { Form, Input, Button, Card, Typography, message, Divider } from 'antd';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();
  const [form] = Form.useForm();

  const onFinish = async (values: { name: string; email: string; password: string }) => {
    try {
      await register(values.name, values.email, values.password);
      message.success('注册成功！');
      navigate('/workflows');
    } catch {
      message.error('注册失败，请稍后重试');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg rounded-xl" bordered={false}>
        <div className="text-center mb-8">
          <Title level={2} className="!mb-1 !text-indigo-700">
            AI 自动化工作流
          </Title>
          <Text type="secondary">创建您的账户</Text>
        </div>

        <Form
          name="register"
          form={form}
          onFinish={onFinish}
          layout="vertical"
          requiredMark={false}
        >
          <Form.Item
            name="name"
            rules={[{ required: true, message: '请输入您的姓名' }]}
          >
            <Input
              prefix={<UserOutlined className="text-gray-400" />}
              placeholder="姓名"
              size="large"
              autoComplete="name"
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input
              prefix={<MailOutlined className="text-gray-400" />}
              placeholder="邮箱"
              size="large"
              autoComplete="email"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-gray-400" />}
              placeholder="密码"
              size="large"
              autoComplete="new-password"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined className="text-gray-400" />}
              placeholder="确认密码"
              size="large"
              autoComplete="new-password"
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
              注册
            </Button>
          </Form.Item>
        </Form>

        <Divider plain>
          <Text type="secondary" className="text-xs">或</Text>
        </Divider>

        <div className="text-center">
          <Text>已有账户？</Text>
          <Link to="/login" className="text-indigo-600 hover:text-indigo-500 font-medium ml-1">
            立即登录
          </Link>
        </div>


      </Card>
    </div>
  );
};

export default RegisterPage;
