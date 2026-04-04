import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Zap, Brain, Wrench, GitBranch } from 'lucide-react';
import type { TriggerNodeData, AITaskNodeData, ToolNodeData, ConditionNodeData } from '../../types';

// Trigger Node
export const TriggerNode = ({ data, selected }: NodeProps) => {
  const nodeData = data as unknown as TriggerNodeData;
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] ${
        selected ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
      }`}
    >
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-purple-100 rounded-md">
          <Zap size={16} className="text-purple-600" />
        </div>
        <div>
          <div className="font-medium text-gray-800 text-sm">{nodeData.label}</div>
          <div className="text-xs text-gray-500">
            {nodeData.triggerType === 'manual' ? '手动触发' : '定时触发'}
          </div>
        </div>
      </div>
    </div>
  );
};

// AI Task Node
export const AITaskNode = ({ data, selected }: NodeProps) => {
  const nodeData = data as unknown as AITaskNodeData;
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[200px] ${
        selected ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-green-100 rounded-md">
          <Brain size={16} className="text-green-600" />
        </div>
        <div>
          <div className="font-medium text-gray-800 text-sm">{nodeData.label}</div>
          <div className="text-xs text-gray-500">
            {nodeData.model === 'gpt-4o' ? 'GPT-4o' : 'GPT-4o Mini'}
          </div>
        </div>
      </div>
    </div>
  );
};

// Tool Node
export const ToolNode = ({ data, selected }: NodeProps) => {
  const nodeData = data as unknown as ToolNodeData;
  const toolLabels: Record<string, string> = {
    feishu_message: '飞书消息',
    feishu_doc: '飞书文档',
    http_request: 'HTTP 请求',
  };
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] ${
        selected ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-orange-100 rounded-md">
          <Wrench size={16} className="text-orange-600" />
        </div>
        <div>
          <div className="font-medium text-gray-800 text-sm">{nodeData.label}</div>
          <div className="text-xs text-gray-500">
            {toolLabels[nodeData.toolType] || nodeData.toolType}
          </div>
        </div>
      </div>
    </div>
  );
};

// Condition Node
export const ConditionNode = ({ data, selected }: NodeProps) => {
  const nodeData = data as unknown as ConditionNodeData;
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] ${
        selected ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <Handle type="source" position={Position.Bottom} id="true" className="!bg-green-500" />
      <Handle type="source" position={Position.Bottom} id="false" className="!bg-red-500" style={{ left: '80%' }} />
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-blue-100 rounded-md">
          <GitBranch size={16} className="text-blue-600" />
        </div>
        <div>
          <div className="font-medium text-gray-800 text-sm">{nodeData.label}</div>
          <div className="text-xs text-gray-500">条件分支</div>
        </div>
      </div>
    </div>
  );
};

export const nodeTypes = {
  trigger: TriggerNode,
  aiTask: AITaskNode,
  tool: ToolNode,
  condition: ConditionNode,
};