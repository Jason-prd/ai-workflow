import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Typography, Tag, Space, Collapse, Descriptions, Spin, message } from 'antd';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useExecutionStore } from '../stores/executionStore';
import type { NodeExecution, ExecutionStatus } from '../types';
import { executionApi } from '../services/api';

const { Title, Text, Paragraph } = Typography;

const ExecutionDetailPage: React.FC = () => {
  const { id, execId } = useParams<{ id: string; execId: string }>();
  const navigate = useNavigate();
  const { currentLog, setCurrentLog } = useExecutionStore();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchDetail = async () => {
      if (!execId) return;
      setIsLoading(true);
      try {
        const detail = await executionApi.get(execId);
        const mapped = {
          id: String(detail.id),
          workflowId: String(detail.workflow_id),
          workflowName: currentLog?.workflowName || '',
          triggerType: detail.trigger_type as 'manual' | 'cron',
          status: detail.status as ExecutionStatus,
          startTime: detail.started_at || detail.created_at,
          endTime: detail.ended_at,
          duration: detail.started_at && detail.ended_at
            ? (new Date(detail.ended_at).getTime() - new Date(detail.started_at).getTime()) / 1000
            : undefined,
          nodeExecutions: detail.logs.map((log) => ({
            nodeId: log.node_id,
            nodeName: log.node_name || log.node_id,
            status: log.status as ExecutionStatus,
            startTime: log.created_at,
            duration: log.duration_ms ? log.duration_ms / 1000 : undefined,
            input: log.input_data || {},
            output: log.output_data,
            error: log.error,
          })),
          errorMessage: detail.error_message,
        };
        setCurrentLog(mapped);
      } catch {
        // Try to use local data if API fails
        const log = useExecutionStore.getState().getLog(execId!);
        if (log) setCurrentLog(log);
        else message.error('无法加载执行详情');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetail();
  }, [execId, id, setCurrentLog, currentLog?.workflowName]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spin size="large" tip="加载执行详情..." />
      </div>
    );
  }

  if (!currentLog) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  const getStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />;
      case 'running':
        return <LoadingOutlined style={{ color: '#1890ff', fontSize: 18 }} />;
      default:
        return null;
    }
  };

  const getStatusTag = (status: ExecutionStatus) => {
    switch (status) {
      case 'success':
        return <Tag color="success">成功</Tag>;
      case 'failed':
        return <Tag color="error">失败</Tag>;
      case 'running':
        return <Tag color="processing">运行中</Tag>;
      default:
        return <Tag>{status}</Tag>;
    }
  };

  const nodeItems = currentLog.nodeExecutions.map((node: NodeExecution, index: number) => ({
    key: node.nodeId,
    label: (
      <Space className="w-full justify-between">
        <Space>
          <span className="font-medium">
            {index + 1}. {node.nodeName}
          </span>
          {getStatusIcon(node.status)}
        </Space>
        <Text type="secondary">
          {node.duration ? `${node.duration.toFixed(2)}s` : '-'}
        </Text>
      </Space>
    ),
    children: (
      <div className="space-y-4">
        {node.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <Text type="danger" className="font-medium">
              错误信息
            </Text>
            <Paragraph type="danger" className="!mb-0 mt-1">
              {node.error}
            </Paragraph>
          </div>
        )}

        <div>
          <Text strong className="text-xs uppercase text-gray-500">
            输入
          </Text>
          <Card size="small" className="mt-1 bg-gray-50">
            <pre className="text-xs overflow-x-auto whitespace-pre-wrap font-mono max-h-48 overflow-y-auto">
              {JSON.stringify(node.input, null, 2)}
            </pre>
          </Card>
        </div>

        <div>
          <Text strong className="text-xs uppercase text-gray-500">
            输出
          </Text>
          <Card size="small" className="mt-1 bg-gray-50">
            {node.output ? (
              <pre className="text-xs overflow-x-auto whitespace-pre-wrap font-mono max-h-48 overflow-y-auto">
                {JSON.stringify(node.output, null, 2)}
              </pre>
            ) : (
              <Text type="secondary">无输出</Text>
            )}
          </Card>
        </div>
      </div>
    ),
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-4">
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(`/workflows/${id}/logs`)}
              type="text"
            />
            <Title level={5} className="!mb-0 flex-1">
              执行详情 #{execId}
            </Title>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                if (execId) {
                  executionApi.get(execId).then(() => message.success('已刷新'));
                }
              }}
            >
              刷新
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Overview Card */}
        <Card>
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="工作流">{currentLog.workflowName}</Descriptions.Item>
            <Descriptions.Item label="状态">{getStatusTag(currentLog.status)}</Descriptions.Item>
            <Descriptions.Item label="触发方式">
              <Tag icon={currentLog.triggerType === 'manual' ? undefined : <ClockCircleOutlined />}>
                {currentLog.triggerType === 'manual' ? '手动触发' : '定时触发'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="执行时长">
              {currentLog.duration ? `${currentLog.duration.toFixed(2)}s` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="开始时间" span={2}>
              {new Date(currentLog.startTime).toLocaleString('zh-CN')}
            </Descriptions.Item>
            {currentLog.endTime && (
              <Descriptions.Item label="结束时间" span={2}>
                {new Date(currentLog.endTime).toLocaleString('zh-CN')}
              </Descriptions.Item>
            )}
            {currentLog.errorMessage && (
              <Descriptions.Item label="错误信息" span={2}>
                <Text type="danger">{currentLog.errorMessage}</Text>
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>

        {/* Node Executions */}
        <Card>
          <Title level={5} className="!mb-4">
            节点执行详情
          </Title>
          {nodeItems.length > 0 ? (
            <Collapse
              items={nodeItems}
              defaultActiveKey={[currentLog.nodeExecutions[0]?.nodeId]}
            />
          ) : (
            <Text type="secondary">暂无节点执行记录</Text>
          )}
        </Card>
      </main>
    </div>
  );
};

export default ExecutionDetailPage;
