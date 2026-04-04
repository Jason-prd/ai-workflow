import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Table, Tag, Button, Typography, Spin } from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useExecutionStore } from '../stores/executionStore';
import { useWorkflowStore } from '../stores/workflowStore';
import type { ExecutionStatus, ExecutionLog } from '../types';

const { Title } = Typography;

const ExecutionLogsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { logs, loadLogs, isLoading } = useExecutionStore();
  const { workflows } = useWorkflowStore();
  const [pageSize, setPageSize] = useState(20);

  const workflow = useMemo(() => workflows.find((w) => w.id === id), [workflows, id]);

  useEffect(() => {
    if (id) {
      loadLogs(id);
    }
  }, [id, loadLogs]);

  const filteredLogs = useMemo(
    () => logs.filter((l) => l.workflowId === id),
    [logs, id]
  );

  const getStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      default:
        return null;
    }
  };

  const getStatusTag = (status: ExecutionStatus) => {
    switch (status) {
      case 'success':
        return <Tag color="success" icon={getStatusIcon(status)}>成功</Tag>;
      case 'failed':
        return <Tag color="error" icon={getStatusIcon(status)}>失败</Tag>;
      case 'running':
        return <Tag color="processing" icon={getStatusIcon(status)}>运行中</Tag>;
      default:
        return <Tag>{status}</Tag>;
    }
  };

  const columns = [
    {
      title: '执行ID',
      dataIndex: 'id',
      key: 'id',
      width: 140,
      render: (id: string) => <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">{id}</code>,
    },
    {
      title: '触发方式',
      dataIndex: 'triggerType',
      key: 'triggerType',
      width: 100,
      render: (type: string) => (
        <Tag icon={type === 'manual' ? undefined : <ClockCircleOutlined />}>
          {type === 'manual' ? '手动' : '定时'}
        </Tag>
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
      sorter: (a: ExecutionLog, b: ExecutionLog) =>
        new Date(b.startTime).getTime() - new Date(a.startTime).getTime(),
      defaultSortOrder: 'descend' as const,
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      render: (duration?: number) => (duration ? `${duration.toFixed(1)}s` : '-'),
      sorter: (a: ExecutionLog, b: ExecutionLog) => (a.duration || 0) - (b.duration || 0),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: ExecutionStatus) => getStatusTag(status),
      filters: [
        { text: '成功', value: 'success' },
        { text: '失败', value: 'failed' },
        { text: '运行中', value: 'running' },
      ],
      onFilter: (value: unknown, record: ExecutionLog) => record.status === value,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: unknown, record: ExecutionLog) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/workflows/${id}/logs/${record.id}`)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-4">
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(`/workflows/${id}/edit`)}
              type="text"
            />
            <Title level={5} className="!mb-0 flex-1">
              {workflow?.name || '工作流'} - 执行日志
            </Title>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => id && loadLogs(id)}
              loading={isLoading}
            >
              刷新
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading && filteredLogs.length === 0 ? (
          <div className="flex justify-center items-center py-24">
            <Spin size="large" tip="加载执行记录..." />
          </div>
        ) : (
          <Card>
            <Table
              columns={columns}
              dataSource={filteredLogs}
              rowKey="id"
              pagination={{
                pageSize,
                showSizeChanger: true,
                pageSizeOptions: ['10', '20', '50', '100'],
                onShowSizeChange: (_, size) => setPageSize(size),
                showTotal: (total, range) =>
                  `${range[0]}-${range[1]} 共 ${total} 条记录`,
              }}
              locale={{ emptyText: '暂无执行记录，点击"测试运行"开始第一次执行' }}
              size="middle"
            />
          </Card>
        )}
      </main>
    </div>
  );
};

export default ExecutionLogsPage;
