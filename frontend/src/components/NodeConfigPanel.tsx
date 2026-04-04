import { useEffect } from 'react';
import { Form, Input, Select, InputNumber, Button, message } from 'antd';
import { Delete, Zap, Brain, Wrench, GitBranch } from 'lucide-react';
import { useWorkflowStore } from '../stores/workflowStore';
import type { NodeType } from '../types';

const NodeConfigPanel = () => {
  const { currentWorkflow, selectedNodeId, updateNode, removeNode } = useWorkflowStore();
  const [form] = Form.useForm();

  const selectedNodeData = currentWorkflow?.nodes.find((n) => n.id === selectedNodeId);

  useEffect(() => {
    if (selectedNodeData) {
      form.setFieldsValue(selectedNodeData.data);
    }
  }, [selectedNodeData, form]);

  if (!selectedNodeData) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p>请选择一个节点进行配置</p>
      </div>
    );
  }

  const nodeType = selectedNodeData.type;

  const handleValuesChange = (_changedValues: unknown, allValues: unknown) => {
    if (selectedNodeId) {
      updateNode(selectedNodeId, allValues as Record<string, unknown>);
    }
  };

  const handleDelete = () => {
    if (selectedNodeId) {
      removeNode(selectedNodeId);
      message.success('节点已删除');
    }
  };

  const getNodeIcon = (type: NodeType) => {
    switch (type) {
      case 'trigger':
        return <Zap size={18} className="text-purple-600" />;
      case 'aiTask':
        return <Brain size={18} className="text-green-600" />;
      case 'tool':
        return <Wrench size={18} className="text-orange-600" />;
      case 'condition':
        return <GitBranch size={18} className="text-blue-600" />;
      default:
        return null;
    }
  };

  const getNodeTitle = (type: NodeType) => {
    switch (type) {
      case 'trigger':
        return '触发器';
      case 'aiTask':
        return 'AI 任务';
      case 'tool':
        return '工具';
      case 'condition':
        return '条件分支';
      default:
        return '节点';
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getNodeIcon(nodeType)}
          <span className="font-medium">{getNodeTitle(nodeType)}</span>
        </div>
        <Button
          type="text"
          danger
          icon={<Delete size={16} />}
          onClick={handleDelete}
        >
          删除
        </Button>
      </div>
      <div className="flex-1 overflow-auto p-4">
        <Form
          form={form}
          layout="vertical"
          onValuesChange={handleValuesChange}
          initialValues={selectedNodeData?.data}
        >
          <Form.Item name="label" label="节点名称">
            <Input />
          </Form.Item>

          {nodeType === 'trigger' && (
            <>
              <Form.Item name="triggerType" label="触发类型">
                <Select>
                  <Select.Option value="manual">手动触发</Select.Option>
                  <Select.Option value="cron">定时触发</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item
                noStyle
                shouldUpdate={(prev, curr) => prev.triggerType !== curr.triggerType}
              >
                {({ getFieldValue }) =>
                  getFieldValue('triggerType') === 'cron' && (
                    <>
                      <Form.Item name="cronExpression" label="Cron 表达式">
                        <Input placeholder="0 18 * * *" />
                      </Form.Item>
                      <Form.Item name="timezone" label="时区">
                        <Select>
                          <Select.Option value="Asia/Shanghai">Asia/Shanghai</Select.Option>
                          <Select.Option value="UTC">UTC</Select.Option>
                          <Select.Option value="America/New_York">America/New_York</Select.Option>
                        </Select>
                      </Form.Item>
                    </>
                  )
                }
              </Form.Item>
            </>
          )}

          {nodeType === 'aiTask' && (
            <>
              <Form.Item name="model" label="模型">
                <Select>
                  <Select.Option value="gpt-4o">GPT-4o</Select.Option>
                  <Select.Option value="gpt-4o-mini">GPT-4o Mini</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="prompt" label="提示词">
                <Input.TextArea rows={4} placeholder="输入你的提示词..." />
              </Form.Item>
              <Form.Item name="temperature" label="Temperature">
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              <Form.Item name="maxTokens" label="最大 Token 数">
                <InputNumber min={100} max={32000} step={100} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="outputVariable" label="输出变量名">
                <Input placeholder="如: result" />
              </Form.Item>
            </>
          )}

          {nodeType === 'tool' && (
            <>
              <Form.Item name="toolType" label="工具类型">
                <Select>
                  <Select.Option value="feishu_message">飞书消息</Select.Option>
                  <Select.Option value="feishu_doc">飞书文档</Select.Option>
                  <Select.Option value="http_request">HTTP 请求</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item
                noStyle
                shouldUpdate={(prev, curr) => prev.toolType !== curr.toolType}
              >
                {({ getFieldValue }) => {
                  const toolType = getFieldValue('toolType');
                  if (toolType === 'feishu_message') {
                    return (
                      <>
                        <Form.Item name={['config', 'messageType']} label="消息类型">
                          <Select>
                            <Select.Option value="text">文本</Select.Option>
                            <Select.Option value="post">富文本</Select.Option>
                          </Select>
                        </Form.Item>
                        <Form.Item name={['config', 'content']} label="消息内容">
                          <Input.TextArea
                            rows={3}
                            placeholder="使用 {{变量名}} 引用变量"
                          />
                        </Form.Item>
                      </>
                    );
                  }
                  if (toolType === 'http_request') {
                    return (
                      <>
                        <Form.Item name={['config', 'method']} label="请求方法">
                          <Select>
                            <Select.Option value="GET">GET</Select.Option>
                            <Select.Option value="POST">POST</Select.Option>
                            <Select.Option value="PUT">PUT</Select.Option>
                            <Select.Option value="DELETE">DELETE</Select.Option>
                          </Select>
                        </Form.Item>
                        <Form.Item name={['config', 'url']} label="请求 URL">
                          <Input placeholder="https://api.example.com" />
                        </Form.Item>
                        <Form.Item name={['config', 'body']} label="请求体">
                          <Input.TextArea rows={3} placeholder="JSON 格式" />
                        </Form.Item>
                      </>
                    );
                  }
                  return null;
                }}
              </Form.Item>
            </>
          )}

          {nodeType === 'condition' && (
            <>
              <Form.Item name="expression" label="条件表达式">
                <Input.TextArea
                  rows={2}
                  placeholder="如: {{result}} > 10"
                />
              </Form.Item>
            </>
          )}
        </Form>
      </div>
    </div>
  );
};

export default NodeConfigPanel;