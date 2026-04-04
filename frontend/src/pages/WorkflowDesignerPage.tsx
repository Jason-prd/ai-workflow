import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  BackgroundVariant,
} from '@xyflow/react';
import type { Node, Connection, NodeTypes } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Button, Typography, Tag, Space, message, Spin, Divider, Select, Input, Form, Slider } from 'antd';
import { ArrowLeftOutlined, SaveOutlined, PlayCircleOutlined, ThunderboltOutlined, ClockCircleOutlined, RobotOutlined, BranchesOutlined } from '@ant-design/icons';
import { useWorkflowStore } from '../stores/workflowStore';
import { useExecutionStore } from '../stores/executionStore';
import { workflowApi } from '../services/api';
import type { WorkflowNodeData, TriggerNodeData, AITaskNodeData, ToolNodeData, ConditionNodeData } from '../types';

// ==================== Custom Nodes ====================

const TriggerNodeWidget: React.FC<{ data: TriggerNodeData; selected: boolean }> = ({ data, selected }) => (
  <div className={`px-4 py-3 rounded-lg border-2 min-w-[160px] ${selected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 bg-white'}`}>
    <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    <div className="flex items-center gap-2">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${data.triggerType === 'manual' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'}`}>
        {data.triggerType === 'manual' ? <ThunderboltOutlined /> : <ClockCircleOutlined />}
      </div>
      <div>
        <div className="font-medium text-sm">{data.label}</div>
        <div className="text-xs text-gray-500">
          {data.triggerType === 'manual' ? '手动触发' : `CRON: ${data.cronExpression}`}
        </div>
      </div>
    </div>
  </div>
);

const AITaskNodeWidget: React.FC<{ data: AITaskNodeData; selected: boolean }> = ({ data, selected }) => (
  <div className={`px-4 py-3 rounded-lg border-2 min-w-[180px] ${selected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 bg-white'}`}>
    <Handle type="target" position={Position.Top} className="!bg-gray-400" />
    <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-full flex items-center justify-center bg-purple-100 text-purple-600">
        <RobotOutlined />
      </div>
      <div>
        <div className="font-medium text-sm">{data.label}</div>
        <div className="text-xs text-gray-500">{data.model}</div>
      </div>
    </div>
  </div>
);

const ToolNodeWidget: React.FC<{ data: ToolNodeData; selected: boolean }> = ({ data, selected }) => {
  const toolIcons: Record<string, React.ReactNode> = {
    feishu_message: '💬',
    feishu_doc: '📄',
    http_request: '🌐',
  };
  const toolLabels: Record<string, string> = {
    feishu_message: '飞书消息',
    feishu_doc: '飞书文档',
    http_request: 'HTTP请求',
  };

  return (
    <div className={`px-4 py-3 rounded-lg border-2 min-w-[160px] ${selected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 bg-white'}`}>
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-green-100 text-lg">
          {toolIcons[data.toolType]}
        </div>
        <div>
          <div className="font-medium text-sm">{data.label}</div>
          <div className="text-xs text-gray-500">{toolLabels[data.toolType]}</div>
        </div>
      </div>
    </div>
  );
};

const ConditionNodeWidget: React.FC<{ data: ConditionNodeData; selected: boolean }> = ({ data, selected }) => (
  <div className={`px-4 py-3 rounded-lg border-2 min-w-[160px] ${selected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 bg-white'}`}>
    <Handle type="target" position={Position.Top} className="!bg-gray-400" />
    <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-full flex items-center justify-center bg-yellow-100 text-yellow-600">
        <BranchesOutlined />
      </div>
      <div>
        <div className="font-medium text-sm">{data.label}</div>
        <div className="text-xs text-gray-500 truncate max-w-[120px]">{data.expression}</div>
      </div>
    </div>
  </div>
);

const nodeTypes: NodeTypes = {
  trigger: TriggerNodeWidget as any,
  aiTask: AITaskNodeWidget as any,
  tool: ToolNodeWidget as any,
  condition: ConditionNodeWidget as any,
};

// ==================== Node Palette ====================

interface PaletteItem {
  type: string;
  nodeType: 'trigger' | 'aiTask' | 'tool' | 'condition';
  label: string;
  icon: React.ReactNode;
  color: string;
  defaultData: Partial<WorkflowNodeData>;
}

const paletteItems: PaletteItem[] = [
  {
    type: 'manual-trigger',
    nodeType: 'trigger',
    label: '手动触发',
    icon: <ThunderboltOutlined />,
    color: 'bg-blue-500',
    defaultData: { label: '手动触发', triggerType: 'manual' } as TriggerNodeData,
  },
  {
    type: 'cron-trigger',
    nodeType: 'trigger',
    label: '定时触发',
    icon: <ClockCircleOutlined />,
    color: 'bg-orange-500',
    defaultData: { label: '定时触发', triggerType: 'cron', cronExpression: '0 9 * * *' } as TriggerNodeData,
  },
  {
    type: 'llm-task',
    nodeType: 'aiTask',
    label: 'LLM 任务',
    icon: <RobotOutlined />,
    color: 'bg-purple-500',
    defaultData: { label: 'LLM 任务', model: 'gpt-4o', prompt: '', inputVariables: [], outputVariable: 'result', temperature: 0.7, maxTokens: 2000 } as AITaskNodeData,
  },
  {
    type: 'feishu-message',
    nodeType: 'tool',
    label: '飞书消息',
    icon: <span>💬</span>,
    color: 'bg-green-500',
    defaultData: { label: '发送消息', toolType: 'feishu_message', config: { chatId: '', message: '' } } as ToolNodeData,
  },
  {
    type: 'http-request',
    nodeType: 'tool',
    label: 'HTTP 请求',
    icon: <span>🌐</span>,
    color: 'bg-gray-500',
    defaultData: { label: 'HTTP请求', toolType: 'http_request', config: { url: '', method: 'GET' as const, headers: {}, body: '', timeout: 30 } } as ToolNodeData,
  },
  {
    type: 'condition',
    nodeType: 'condition',
    label: '条件分支',
    icon: <BranchesOutlined />,
    color: 'bg-yellow-500',
    defaultData: { label: '条件判断', expression: '' } as ConditionNodeData,
  },
];

// ==================== Node Config Panel ====================

interface NodeConfigPanelProps {
  nodeId: string | null;
  nodes: Node[];
  onUpdate: (nodeId: string, data: Partial<WorkflowNodeData>) => void;
  onRemove: (nodeId: string) => void;
}

const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({ nodeId, nodes, onUpdate, onRemove }) => {
  const node = useMemo(() => nodes.find((n) => n.id === nodeId), [nodeId, nodes]);

  if (!node) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        选择一个节点以配置
      </div>
    );
  }

  const data = node.data as WorkflowNodeData;

  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="mb-4">
        <Typography.Title level={5} className="!mb-1">节点配置</Typography.Title>
        <Tag color="blue">{node.type}</Tag>
      </div>

      <Form layout="vertical" size="small">
        <Form.Item label="节点名称">
          <Input
            value={data.label}
            onChange={(e) => onUpdate(node.id, { label: e.target.value })}
          />
        </Form.Item>

        {node.type === 'trigger' && (data as TriggerNodeData).triggerType === 'cron' && (
          <>
            <Form.Item label="CRON 表达式">
              <Input
                value={(data as TriggerNodeData).cronExpression}
                onChange={(e) => onUpdate(node.id, { cronExpression: e.target.value })}
                placeholder="0 9 * * *"
              />
            </Form.Item>
            <Form.Item label="时区">
              <Select
                value={(data as TriggerNodeData).timezone || 'Asia/Shanghai'}
                onChange={(val) => onUpdate(node.id, { timezone: val })}
                options={[
                  { value: 'Asia/Shanghai', label: 'Asia/Shanghai (UTC+8)' },
                  { value: 'UTC', label: 'UTC' },
                  { value: 'America/New_York', label: 'America/New_York (UTC-5)' },
                ]}
              />
            </Form.Item>
          </>
        )}

        {node.type === 'aiTask' && (
          <>
            <Form.Item label="模型">
              <Select
                value={(data as AITaskNodeData).model}
                onChange={(val) => onUpdate(node.id, { model: val })}
                options={[
                  { value: 'gpt-4o', label: 'GPT-4o' },
                  { value: 'gpt-4o-mini', label: 'GPT-4o-mini' },
                ]}
              />
            </Form.Item>
            <Form.Item label="提示词">
              <Input.TextArea
                rows={4}
                value={(data as AITaskNodeData).prompt}
                onChange={(e) => onUpdate(node.id, { prompt: e.target.value })}
                placeholder="使用 {{variable}} 引用变量"
              />
            </Form.Item>
            <Form.Item label="Temperature">
              <Slider
                min={0}
                max={2}
                step={0.1}
                value={(data as AITaskNodeData).temperature}
                onChange={(val) => onUpdate(node.id, { temperature: val })}
              />
            </Form.Item>
            <Form.Item label="Max Tokens">
              <Input
                type="number"
                value={(data as AITaskNodeData).maxTokens}
                onChange={(e) => onUpdate(node.id, { maxTokens: parseInt(e.target.value) || 2000 })}
              />
            </Form.Item>
          </>
        )}

        {node.type === 'tool' && (
          <>
            <Form.Item label="工具类型">
              <Select
                value={(data as ToolNodeData).toolType}
                onChange={(val) => {
                  const toolData = data as ToolNodeData;
                  let newConfig: ToolNodeData['config'] = toolData.config;
                  if (val === 'feishu_message') {
                    newConfig = { chatId: '', message: '' };
                  } else if (val === 'http_request') {
                    newConfig = { url: '', method: 'GET', headers: {}, body: '', timeout: 30 };
                  }
                  onUpdate(node.id, { toolType: val, config: newConfig });
                }}
                options={[
                  { value: 'feishu_message', label: '飞书消息' },
                  { value: 'feishu_doc', label: '飞书文档' },
                  { value: 'http_request', label: 'HTTP请求' },
                ]}
              />
            </Form.Item>

            {(data as ToolNodeData).toolType === 'feishu_message' && (
              <>
                <Form.Item label="群 ID">
                  <Input
                    value={((data as ToolNodeData).config as any).chatId || ''}
                    onChange={(e) =>
                      onUpdate(node.id, {
                        config: { ...(data as ToolNodeData).config, chatId: e.target.value },
                      })
                    }
                    placeholder="oc_xxx"
                  />
                </Form.Item>
                <Form.Item label="消息内容">
                  <Input.TextArea
                    rows={3}
                    value={((data as ToolNodeData).config as any).message || ''}
                    onChange={(e) =>
                      onUpdate(node.id, {
                        config: { ...(data as ToolNodeData).config, message: e.target.value },
                      })
                    }
                    placeholder="使用 {{variable}} 引用变量"
                  />
                </Form.Item>
              </>
            )}

            {(data as ToolNodeData).toolType === 'http_request' && (
              <>
                <Form.Item label="URL">
                  <Input
                    value={((data as ToolNodeData).config as any).url || ''}
                    onChange={(e) =>
                      onUpdate(node.id, {
                        config: { ...(data as ToolNodeData).config, url: e.target.value },
                      })
                    }
                    placeholder="https://api.example.com"
                  />
                </Form.Item>
                <Form.Item label="Method">
                  <Select
                    value={((data as ToolNodeData).config as any).method || 'GET'}
                    onChange={(val) =>
                      onUpdate(node.id, {
                        config: { ...(data as ToolNodeData).config, method: val },
                      })
                    }
                    options={[
                      { value: 'GET', label: 'GET' },
                      { value: 'POST', label: 'POST' },
                      { value: 'PUT', label: 'PUT' },
                      { value: 'DELETE', label: 'DELETE' },
                    ]}
                  />
                </Form.Item>
              </>
            )}
          </>
        )}

        <Divider />

        <Button danger block onClick={() => onRemove(node.id)}>
          删除节点
        </Button>
      </Form>
    </div>
  );
};

// ==================== Main Designer Page ====================

const WorkflowDesignerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { workflows, currentWorkflow, setCurrentWorkflow, updateWorkflow, updateNode, removeNode, addEdge: addWorkflowEdge, saveCurrentWorkflow } = useWorkflowStore();
  const { runWorkflow, isLoading: isRunning } = useExecutionStore();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Initialize workflow
  useEffect(() => {
    if (!currentWorkflow || currentWorkflow.id !== id) {
      const wf = workflows.find((w) => w.id === id);
      if (wf) {
        setCurrentWorkflow(wf);
      } else if (id) {
        navigate('/workflows');
      }
    }
  }, [id, workflows, currentWorkflow, setCurrentWorkflow, navigate]);

  // Convert store nodes to React Flow nodes
  const rfNodes = useMemo(() => {
    if (!currentWorkflow) return [];
    return currentWorkflow.nodes.map((n) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: n.data as Record<string, unknown>,
      selected: n.id === selectedNodeId,
    })) as Node[];
  }, [currentWorkflow, selectedNodeId]);

  // Convert store edges to React Flow edges
  const rfEdges = useMemo(() => {
    if (!currentWorkflow) return [];
    return currentWorkflow.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#6366f1', strokeWidth: 2 },
    }));
  }, [currentWorkflow]);

  const [nodes, setNodes, onNodesChange] = useNodesState(rfNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(rfEdges);

  // Sync React Flow state with store
  useEffect(() => {
    setNodes(rfNodes);
  }, [rfNodes, setNodes]);

  useEffect(() => {
    setEdges(rfEdges);
  }, [rfEdges, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => {
      if (params.source && params.target) {
        addWorkflowEdge(params.source, params.target);
        setEdges((eds) =>
          addEdge({ ...params, type: 'smoothstep', animated: true, style: { stroke: '#6366f1', strokeWidth: 2 } }, eds)
        );
      }
    },
    [addWorkflowEdge]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const paletteItem = paletteItems.find((p) => p.type === type);
      if (!paletteItem) return;

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - reactFlowBounds.left - 80,
        y: event.clientY - reactFlowBounds.top - 30,
      };

      const newNode = {
        id: `node-${Date.now()}`,
        type: paletteItem.nodeType,
        position,
        data: { ...paletteItem.defaultData },
      };

      setNodes((nds) => [...nds, newNode as Node]);
      updateWorkflow(currentWorkflow!.id, {
        nodes: [...currentWorkflow!.nodes, { ...newNode, data: newNode.data as any }],
      });
    },
    [currentWorkflow, setNodes, updateWorkflow]
  );

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id === selectedNodeId ? null : node.id);
  }, [selectedNodeId]);

  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChange(changes);
      // Update positions in store
      changes.forEach((change: any) => {
        if (change.type === 'position' && change.position) {
          updateWorkflow(currentWorkflow!.id, {
            nodes: currentWorkflow!.nodes.map((n) =>
              n.id === change.id ? { ...n, position: change.position } : n
            ),
          });
        }
      });
    },
    [currentWorkflow, onNodesChange, updateWorkflow]
  );

  const handleUpdateNode = useCallback(
    (nodeId: string, data: Partial<WorkflowNodeData>) => {
      updateNode(nodeId, data);
      setNodes((nds) =>
        nds.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...data } as Record<string, unknown> } : n))
      );
    },
    [updateNode, setNodes]
  );

  const handleRemoveNode = useCallback(
    (nodeId: string) => {
      removeNode(nodeId);
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
      setSelectedNodeId(null);
    },
    [removeNode, setNodes, setEdges]
  );

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      await saveCurrentWorkflow();
      message.success('工作流已保存');
    } catch {
      message.error('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  }, [saveCurrentWorkflow]);

  const handleTest = useCallback(async () => {
    if (!currentWorkflow) return;
    message.loading({ content: 'Running workflow...', key: 'run' });
    try {
      await runWorkflow(currentWorkflow.id);
      message.success({ content: 'Workflow executed successfully!', key: 'run' });
    } catch {
      message.error({ content: 'Workflow execution failed', key: 'run' });
    }
  }, [currentWorkflow, runWorkflow]);

  const handleDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  if (!currentWorkflow) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 h-14 flex items-center justify-between flex-shrink-0">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/workflows')} type="text" />
          <Typography.Title level={5} className="!mb-0">
            {currentWorkflow.name}
          </Typography.Title>
          <Tag color={currentWorkflow.status === 'published' ? 'green' : 'orange'}>
            {currentWorkflow.status === 'published' ? '已发布' : '草稿'}
          </Tag>
        </Space>
        <Space>
          <Button icon={<SaveOutlined />} onClick={handleSave} loading={isSaving}>
            保存
          </Button>
          {currentWorkflow.status === 'draft' && (
            <Button
              icon={<ThunderboltOutlined />}
              onClick={async () => {
                try {
                  await workflowApi.publish(currentWorkflow.id);
                  updateWorkflow(currentWorkflow.id, { status: 'published' });
                  message.success('工作流已发布，可设置定时触发');
                } catch {
                  message.error('发布失败，请检查工作流配置');
                }
              }}
            >
              发布
            </Button>
          )}
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleTest}
            loading={isRunning}
          >
            测试运行
          </Button>
          <Button onClick={() => navigate(`/workflows/${currentWorkflow.id}/logs`)}>
            执行日志
          </Button>
        </Space>
      </header>

      {/* Main Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Node Palette */}
        <div className="w-64 bg-white border-r border-gray-200 flex-shrink-0 overflow-y-auto">
          <div className="p-4">
            <Typography.Title level={5} className="!mb-3">
              节点面板
            </Typography.Title>

            <div className="space-y-3">
              <div>
                <Typography.Text type="secondary" className="text-xs uppercase font-semibold">
                  触发器
                </Typography.Text>
                <div className="mt-2 space-y-2">
                  {paletteItems
                    .filter((p) => p.nodeType === 'trigger')
                    .map((item) => (
                      <div
                        key={item.type}
                        draggable
                        onDragStart={(e) => handleDragStart(e, item.type)}
                        className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg cursor-grab hover:bg-gray-100 border border-gray-200"
                      >
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-sm ${item.color}`}>
                          {item.icon}
                        </div>
                        <span className="text-sm">{item.label}</span>
                      </div>
                    ))}
                </div>
              </div>

              <Divider className="!my-3" />

              <div>
                <Typography.Text type="secondary" className="text-xs uppercase font-semibold">
                  AI 任务
                </Typography.Text>
                <div className="mt-2 space-y-2">
                  {paletteItems
                    .filter((p) => p.nodeType === 'aiTask')
                    .map((item) => (
                      <div
                        key={item.type}
                        draggable
                        onDragStart={(e) => handleDragStart(e, item.type)}
                        className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg cursor-grab hover:bg-gray-100 border border-gray-200"
                      >
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-sm ${item.color}`}>
                          {item.icon}
                        </div>
                        <span className="text-sm">{item.label}</span>
                      </div>
                    ))}
                </div>
              </div>

              <Divider className="!my-3" />

              <div>
                <Typography.Text type="secondary" className="text-xs uppercase font-semibold">
                  工具
                </Typography.Text>
                <div className="mt-2 space-y-2">
                  {paletteItems
                    .filter((p) => p.nodeType === 'tool')
                    .map((item) => (
                      <div
                        key={item.type}
                        draggable
                        onDragStart={(e) => handleDragStart(e, item.type)}
                        className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg cursor-grab hover:bg-gray-100 border border-gray-200"
                      >
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-sm ${item.color}`}>
                          {item.icon}
                        </div>
                        <span className="text-sm">{item.label}</span>
                      </div>
                    ))}
                </div>
              </div>

              <Divider className="!my-3" />

              <div>
                <Typography.Text type="secondary" className="text-xs uppercase font-semibold">
                  逻辑
                </Typography.Text>
                <div className="mt-2 space-y-2">
                  {paletteItems
                    .filter((p) => p.nodeType === 'condition')
                    .map((item) => (
                      <div
                        key={item.type}
                        draggable
                        onDragStart={(e) => handleDragStart(e, item.type)}
                        className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg cursor-grab hover:bg-gray-100 border border-gray-200"
                      >
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-sm ${item.color}`}>
                          {item.icon}
                        </div>
                        <span className="text-sm">{item.label}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* React Flow Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={handleNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={handleNodeClick}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[15, 15]}
          >
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                switch (node.type) {
                  case 'trigger': return '#3b82f6';
                  case 'aiTask': return '#a855f7';
                  case 'tool': return '#22c55e';
                  case 'condition': return '#eab308';
                  default: return '#6b7280';
                }
              }}
            />
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
          </ReactFlow>
        </div>

        {/* Right Sidebar - Config Panel */}
        <div className="w-80 bg-white border-l border-gray-200 flex-shrink-0">
          <NodeConfigPanel
            nodeId={selectedNodeId}
            nodes={nodes}
            onUpdate={handleUpdateNode}
            onRemove={handleRemoveNode}
          />
        </div>
      </div>
    </div>
  );
};

export default WorkflowDesignerPage;
