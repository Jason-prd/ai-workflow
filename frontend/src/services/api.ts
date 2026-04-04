import axios, { AxiosError } from 'axios';
import { useAuthStore } from '../stores/authStore';

// Use environment variable if set (VITE_API_BASE_URL), otherwise use relative URL for nginx proxy
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==================== Auth API ====================

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    name: string;
    email: string;
  };
}

export interface RegisterResponse {
  user: {
    id: string;
    name: string;
    email: string;
  };
  token: string;
  expires_in: number;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<LoginResponse>('/auth/login', { email, password }),
  register: (name: string, email: string, password: string) =>
    apiClient.post<RegisterResponse>('/auth/register', {
      username: name,
      email,
      password,
    }),
  me: () => apiClient.get<UserResponse>('/auth/me'),
};

// ==================== Workflow API ====================

// Backend node format (snake_case, uses 'config' and 'name')
export interface BackendNode {
  id: string;
  type: string; // trigger, ai_task, tool, condition
  name: string;
  config: Record<string, unknown>;
  position?: { x: number; y: number };
}

// Frontend node format (camelCase, uses 'data')
export interface FrontendNode {
  id: string;
  type: 'trigger' | 'aiTask' | 'tool' | 'condition';
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface WorkflowTriggerConfig {
  type: 'manual' | 'cron';
  expression?: string;
  timezone?: string;
}

// Backend API types
export interface WorkflowResponse {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  trigger_config?: WorkflowTriggerConfig;
  nodes?: BackendNode[];
  status: 'draft' | 'published';
  created_at: string;
  updated_at: string;
}

export interface WorkflowListResponse {
  items: WorkflowResponse[];
  total: number;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  trigger_config?: WorkflowTriggerConfig;
  nodes?: BackendNode[];
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  trigger_config?: WorkflowTriggerConfig;
  nodes?: BackendNode[];
  status?: 'draft' | 'published';
}

// Node type mapping
const backendToFrontendNodeType: Record<string, string> = {
  trigger: 'trigger',
  ai_task: 'aiTask',
  tool: 'tool',
  condition: 'condition',
};

const frontendToBackendNodeType: Record<string, string> = {
  trigger: 'trigger',
  aiTask: 'ai_task',
  tool: 'tool',
  condition: 'condition',
};

// Convert backend WorkflowResponse to frontend workflow format
export function mapWorkflowResponse(wf: WorkflowResponse) {
  return {
    id: String(wf.id),
    name: wf.name,
    description: wf.description,
    status: wf.status as 'draft' | 'published',
    trigger: wf.trigger_config
      ? {
          type: (wf.trigger_config.type || 'manual') as 'manual' | 'cron',
          cronExpression: wf.trigger_config.expression,
          timezone: wf.trigger_config.timezone,
        }
      : { type: 'manual' as const },
    nodes: (wf.nodes || []).map((n) => {
      const frontendType = backendToFrontendNodeType[n.type] || n.type;
      return {
        id: n.id,
        type: frontendType as 'trigger' | 'aiTask' | 'tool' | 'condition',
        position: n.position || { x: 0, y: 0 },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        data: { label: n.name, ...n.config } as any,
      };
    }),
    edges: [],
    createdAt: wf.created_at,
    updatedAt: wf.updated_at,
  };
}

// Convert frontend workflow to backend format
export function toBackendWorkflow(workflow: {
  name: string;
  description?: string;
  trigger: { type: string; cronExpression?: string; timezone?: string };
  nodes: FrontendNode[];
  status: string;
}): WorkflowCreate {
  return {
    name: workflow.name,
    description: workflow.description,
    trigger_config: {
      type: workflow.trigger.type as 'manual' | 'cron',
      expression: workflow.trigger.cronExpression,
      timezone: workflow.trigger.timezone,
    },
    nodes: workflow.nodes.map((n) => ({
      id: n.id,
      type: frontendToBackendNodeType[n.type] || n.type,
      name: (n.data as any)?.label || n.id,
      config: n.data,
      position: n.position,
    })),
  };
}

export const workflowApi = {
  list: () => apiClient.get<WorkflowListResponse>('/workflows').then((r) => r.data),
  get: (id: string) => apiClient.get<WorkflowResponse>(`/workflows/${id}`).then((r) => r.data),
  create: (data: WorkflowCreate) =>
    apiClient.post<WorkflowResponse>('/workflows', data).then((r) => r.data),
  update: (id: string, data: WorkflowUpdate) =>
    apiClient.patch<WorkflowResponse>(`/workflows/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/workflows/${id}`),
  publish: (id: string) =>
    apiClient.post<WorkflowResponse>(`/workflows/${id}/publish`).then((r) => r.data),
  run: (id: string) => apiClient.post(`/workflows/${id}/execute`),
};

// ==================== Execution API ====================

export interface ExecutionLogItem {
  id: number;
  execution_id: number;
  node_id: string;
  node_type: string;
  node_name?: string;
  status: 'success' | 'failed' | 'running';
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error?: string;
  duration_ms?: number;
  created_at: string;
}

export interface ExecutionResponse {
  id: number;
  workflow_id: number;
  trigger_type: string;
  status: 'success' | 'failed' | 'running';
  started_at?: string;
  ended_at?: string;
  error_message?: string;
  trigger_input?: Record<string, unknown>;
  created_at: string;
}

export interface ExecutionDetailResponse extends ExecutionResponse {
  logs: ExecutionLogItem[];
}

export interface ExecutionListResponse {
  items: ExecutionResponse[];
  total: number;
}

export function mapExecutionResponse(exec: ExecutionResponse) {
  return {
    id: String(exec.id),
    workflowId: String(exec.workflow_id),
    workflowName: '',
    triggerType: exec.trigger_type as 'manual' | 'cron',
    status: exec.status as 'success' | 'failed' | 'running',
    startTime: exec.started_at || exec.created_at,
    endTime: exec.ended_at,
    duration:
      exec.started_at && exec.ended_at
        ? (new Date(exec.ended_at).getTime() - new Date(exec.started_at).getTime()) / 1000
        : undefined,
    nodeExecutions: [],
    errorMessage: exec.error_message,
  };
}

export const executionApi = {
  list: (workflowId?: string) =>
    workflowId
      ? apiClient
          .get<ExecutionListResponse>(`/workflows/${workflowId}/executions`)
          .then((r) => r.data)
      : apiClient.get<ExecutionListResponse>('/executions').then((r) => r.data),
  get: (execId: string) =>
    apiClient
      .get<ExecutionDetailResponse>(`/executions/${execId}`)
      .then((r) => r.data),
};

// ==================== Settings API ====================

export interface SettingsDto {
  openaiApiKey?: string;
  feishuAppId?: string;
  feishuAppSecret?: string;
}

export const settingsApi = {
  get: () => apiClient.get('/settings'),
  update: (data: SettingsDto) => apiClient.put('/settings', data),
};

// ==================== Node Types API ====================

export interface NodeType {
  name: string;
  display_name: string;
  description?: string;
  icon?: string;
  config_schema?: Record<string, unknown>;
}

export interface NodeTypeListResponse {
  items: NodeType[];
  total: number;
}

export const nodeTypesApi = {
  list: () => apiClient.get<NodeTypeListResponse>('/node-types').then((r) => r.data),
  get: (nodeType: string) => apiClient.get<NodeType>(`/node-types/${nodeType}`).then((r) => r.data),
};
