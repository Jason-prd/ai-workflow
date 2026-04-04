// ==================== Workflow Types ====================

export type TriggerType = 'manual' | 'cron';
export type WorkflowStatus = 'draft' | 'published';
export type NodeType = 'trigger' | 'aiTask' | 'tool' | 'condition';
export type ToolType = 'feishu_message' | 'feishu_doc' | 'http_request';
export type ExecutionStatus = 'success' | 'failed' | 'running';

// ==================== Trigger ====================

export interface TriggerConfig {
  type: TriggerType;
  cronExpression?: string;
  timezone?: string;
}

// ==================== Trigger Node ====================

export interface TriggerNodeData {
  label: string;
  triggerType: TriggerType;
  cronExpression?: string;
  timezone?: string;
  [key: string]: unknown;
}

// ==================== AI Task Node ====================

export interface AITaskNodeData {
  label: string;
  model: 'gpt-4o' | 'gpt-4o-mini';
  prompt: string;
  inputVariables: string[];
  outputVariable: string;
  temperature: number;
  maxTokens: number;
  [key: string]: unknown;
}

// ==================== Tool Node ====================

export interface FeishuMessageConfig {
  chatId: string;
  message: string;
  [key: string]: unknown;
}

export interface FeishuDocConfig {
  title: string;
  content: string;
  [key: string]: unknown;
}

export interface HttpRequestConfig {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: string;
  timeout?: number;
  [key: string]: unknown;
}

export interface ToolNodeData {
  label: string;
  toolType: ToolType;
  config: FeishuMessageConfig | FeishuDocConfig | HttpRequestConfig;
  [key: string]: unknown;
}

// ==================== Condition Node ====================

export interface ConditionNodeData {
  label: string;
  expression: string;
  description?: string;
  [key: string]: unknown;
}

// ==================== Union Node Data ====================

export type WorkflowNodeData = TriggerNodeData | AITaskNodeData | ToolNodeData | ConditionNodeData;

// ==================== Workflow Node ====================

export interface WorkflowNode {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  data: WorkflowNodeData;
}

// ==================== Edge ====================

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

// ==================== Workflow ====================

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  status: WorkflowStatus;
  trigger: TriggerConfig;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  createdAt: string;
  updatedAt: string;
}

// ==================== Node Execution ====================

export interface NodeExecution {
  nodeId: string;
  nodeName: string;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
}

// ==================== Execution Log ====================

export interface ExecutionLog {
  id: string;
  workflowId: string;
  workflowName: string;
  triggerType: TriggerType;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  nodeExecutions: NodeExecution[];
  errorMessage?: string;
}

// ==================== User ====================

export interface User {
  id: string;
  name: string;
  email: string;
}

// ==================== API Types ====================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}
