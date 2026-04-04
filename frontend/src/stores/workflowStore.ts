import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  Workflow,
  WorkflowNode,
  WorkflowNodeData,
} from '../types';
import { workflowApi, mapWorkflowResponse, toBackendWorkflow } from '../services/api';
import type { WorkflowResponse } from '../services/api';

function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

// Mock initial workflows (fallback when API unavailable)
const mockWorkflows: Workflow[] = [
  {
    id: 'wf-001',
    name: '周报自动生成器',
    description: '每周五自动汇总数据生成周报并发送到飞书群',
    status: 'published',
    trigger: { type: 'cron', cronExpression: '0 9 * * 5', timezone: 'Asia/Shanghai' },
    nodes: [
      {
        id: 'node-1',
        type: 'trigger',
        position: { x: 250, y: 50 },
        data: {
          label: '定时触发',
          triggerType: 'cron',
          cronExpression: '0 9 * * 5',
          timezone: 'Asia/Shanghai',
        } as any,
      },
      {
        id: 'node-2',
        type: 'aiTask',
        position: { x: 250, y: 180 },
        data: {
          label: '生成周报',
          model: 'gpt-4o',
          prompt: '请根据以下数据生成一份周报：{{input_data}}',
          inputVariables: ['input_data'],
          outputVariable: 'weekly_report',
          temperature: 0.7,
          maxTokens: 2000,
        } as any,
      },
      {
        id: 'node-3',
        type: 'tool',
        position: { x: 250, y: 310 },
        data: {
          label: '发送飞书消息',
          toolType: 'feishu_message',
          config: { chatId: 'oc_feishu_group_001', message: '{{weekly_report}}' },
        } as any,
      },
    ],
    edges: [
      { id: 'edge-1', source: 'node-1', target: 'node-2' },
      { id: 'edge-2', source: 'node-2', target: 'node-3' },
    ],
    createdAt: '2026-03-20T08:00:00+08:00',
    updatedAt: '2026-03-23T10:00:00+08:00',
  },
  {
    id: 'wf-002',
    name: '简历初筛助手',
    description: '自动筛选简历并对符合条件的候选人发送面试邀请',
    status: 'draft',
    trigger: { type: 'manual' },
    nodes: [
      {
        id: 'node-1',
        type: 'trigger',
        position: { x: 250, y: 50 },
        data: {
          label: '手动触发',
          triggerType: 'manual',
        } as any,
      },
      {
        id: 'node-2',
        type: 'aiTask',
        position: { x: 250, y: 180 },
        data: {
          label: 'AI简历分析',
          model: 'gpt-4o-mini',
          prompt: '请分析以下简历，判断是否符合岗位要求：{{resume}}。岗位要求：{{requirements}}',
          inputVariables: ['resume', 'requirements'],
          outputVariable: 'analysis_result',
          temperature: 0.5,
          maxTokens: 1000,
        } as any,
      },
    ],
    edges: [
      { id: 'edge-1', source: 'node-1', target: 'node-2' },
    ],
    createdAt: '2026-03-22T14:00:00+08:00',
    updatedAt: '2026-03-22T14:00:00+08:00',
  },
];

interface WorkflowState {
  workflows: Workflow[];
  currentWorkflow: Workflow | null;
  selectedNodeId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadWorkflows: () => Promise<void>;
  createWorkflow: (name: string, description?: string) => Workflow;
  updateWorkflow: (id: string, updates: Partial<Workflow>) => void;
  deleteWorkflow: (id: string) => Promise<void>;
  setCurrentWorkflow: (workflow: Workflow | null) => void;
  selectNode: (nodeId: string | null) => void;

  // Node operations
  addNode: (node: Omit<WorkflowNode, 'id'>) => WorkflowNode;
  updateNode: (nodeId: string, data: Partial<WorkflowNodeData>) => void;
  removeNode: (nodeId: string) => void;
  updateNodePosition: (nodeId: string, position: { x: number; y: number }) => void;

  // Edge operations
  addEdge: (source: string, target: string) => void;
  removeEdge: (edgeId: string) => void;

  // Save
  saveCurrentWorkflow: () => Promise<void>;
}

// Convert backend WorkflowResponse to frontend Workflow format
function fromBackend(wf: WorkflowResponse): Workflow {
  return mapWorkflowResponse(wf);
}

export const useWorkflowStore = create<WorkflowState>()(
  persist(
    (set, get) => ({
      workflows: [],
      currentWorkflow: null,
      selectedNodeId: null,
      isLoading: false,
      error: null,

      loadWorkflows: async () => {
        set({ isLoading: true, error: null });
        try {
          const data = await workflowApi.list();
          const workflows = data.items.map(fromBackend);
          set({ workflows, isLoading: false });
        } catch {
          // Fallback to mock data when API is unavailable
          set({ workflows: mockWorkflows, isLoading: false });
        }
      },

      createWorkflow: (name, description) => {
        const newWorkflow: Workflow = {
          id: `wf-${generateId()}`,
          name,
          description,
          status: 'draft',
          trigger: { type: 'manual' },
          nodes: [],
          edges: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        set((state) => ({
          workflows: [...state.workflows, newWorkflow],
        }));
        return newWorkflow;
      },

      updateWorkflow: (id, updates) => {
        set((state) => ({
          workflows: state.workflows.map((w) =>
            w.id === id
              ? { ...w, ...updates, updatedAt: new Date().toISOString() }
              : w
          ),
          currentWorkflow:
            state.currentWorkflow?.id === id
              ? { ...state.currentWorkflow, ...updates, updatedAt: new Date().toISOString() }
              : state.currentWorkflow,
        }));
      },

      deleteWorkflow: async (id: string) => {
        try {
          await workflowApi.delete(id);
        } catch {
          // Continue with local delete even if API fails
        }
        set((state) => ({
          workflows: state.workflows.filter((w) => w.id !== id),
          currentWorkflow: state.currentWorkflow?.id === id ? null : state.currentWorkflow,
        }));
      },

      setCurrentWorkflow: (workflow) => {
        set({ currentWorkflow: workflow, selectedNodeId: null });
      },

      selectNode: (nodeId) => {
        set({ selectedNodeId: nodeId });
      },

      addNode: (nodeData) => {
        const id = `node-${generateId()}`;
        const newNode: WorkflowNode = { ...nodeData, id };
        const { currentWorkflow } = get();
        if (!currentWorkflow) return newNode;

        const updated = {
          ...currentWorkflow,
          nodes: [...currentWorkflow.nodes, newNode],
          updatedAt: new Date().toISOString(),
        };
        set({ currentWorkflow: updated });
        get().updateWorkflow(currentWorkflow.id, { nodes: updated.nodes });
        return newNode;
      },

      updateNode: (nodeId, data) => {
        const { currentWorkflow } = get();
        if (!currentWorkflow) return;

        const updated = {
          ...currentWorkflow,
          nodes: currentWorkflow.nodes.map((n) =>
            n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n
          ),
          updatedAt: new Date().toISOString(),
        };
        set({ currentWorkflow: updated });
        get().updateWorkflow(currentWorkflow.id, { nodes: updated.nodes });
      },

      removeNode: (nodeId) => {
        const { currentWorkflow, selectedNodeId } = get();
        if (!currentWorkflow) return;

        const updated = {
          ...currentWorkflow,
          nodes: currentWorkflow.nodes.filter((n) => n.id !== nodeId),
          edges: currentWorkflow.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
          updatedAt: new Date().toISOString(),
        };
        set({
          currentWorkflow: updated,
          selectedNodeId: selectedNodeId === nodeId ? null : selectedNodeId,
        });
        get().updateWorkflow(currentWorkflow.id, { nodes: updated.nodes, edges: updated.edges });
      },

      updateNodePosition: (nodeId, position) => {
        const { currentWorkflow } = get();
        if (!currentWorkflow) return;

        const updated = {
          ...currentWorkflow,
          nodes: currentWorkflow.nodes.map((n) =>
            n.id === nodeId ? { ...n, position } : n
          ),
        };
        set({ currentWorkflow: updated });
        get().updateWorkflow(currentWorkflow.id, { nodes: updated.nodes });
      },

      addEdge: (source, target) => {
        const { currentWorkflow } = get();
        if (!currentWorkflow) return;

        // Prevent duplicate edges
        const exists = currentWorkflow.edges.some(
          (e) => e.source === source && e.target === target
        );
        if (exists) return;

        const edgeId = `edge-${generateId()}`;
        const updated = {
          ...currentWorkflow,
          edges: [...currentWorkflow.edges, { id: edgeId, source, target }],
          updatedAt: new Date().toISOString(),
        };
        set({ currentWorkflow: updated });
        get().updateWorkflow(currentWorkflow.id, { edges: updated.edges });
      },

      removeEdge: (edgeId) => {
        const { currentWorkflow } = get();
        if (!currentWorkflow) return;

        const updated = {
          ...currentWorkflow,
          edges: currentWorkflow.edges.filter((e) => e.id !== edgeId),
          updatedAt: new Date().toISOString(),
        };
        set({ currentWorkflow: updated });
        get().updateWorkflow(currentWorkflow.id, { edges: updated.edges });
      },

      saveCurrentWorkflow: async () => {
        const { currentWorkflow, workflows } = get();
        if (!currentWorkflow) return;

        const updated = { ...currentWorkflow, updatedAt: new Date().toISOString() };
        const backendData = toBackendWorkflow(updated);
        const isLocalWorkflow = currentWorkflow.id.startsWith('wf-');

        try {
          if (isLocalWorkflow) {
            // Create new workflow on backend
            const created = await workflowApi.create(backendData);
            const mapped = mapWorkflowResponse(created);
            // Merge: use updated fields but take id and nodes from backend response
            const withRealId: Workflow = {
              ...updated,
              id: mapped.id,
              name: mapped.name || updated.name,
              description: mapped.description ?? updated.description,
              status: mapped.status || updated.status,
              trigger: mapped.trigger || updated.trigger,
              nodes: mapped.nodes || updated.nodes,
              edges: updated.edges,
              createdAt: mapped.createdAt || updated.createdAt,
              updatedAt: mapped.updatedAt || updated.updatedAt,
            };
            set({
              workflows: workflows.map((w) => (w.id === updated.id ? withRealId : w)),
              currentWorkflow: withRealId,
            });
          } else {
            // Update existing workflow on backend
            await workflowApi.update(updated.id, backendData);
            set({
              workflows: workflows.map((w) => (w.id === updated.id ? updated : w)),
              currentWorkflow: updated,
            });
          }
        } catch {
          // Save locally even if API fails
          set({
            workflows: workflows.map((w) => (w.id === updated.id ? updated : w)),
            currentWorkflow: updated,
          });
        }
      },
    }),
    {
      name: 'workflow-storage',
      partialize: (state) => ({ workflows: state.workflows }),
      onRehydrateStorage: () => (state) => {
        if (state && state.workflows.length === 0) {
          state.loadWorkflows();
        }
      },
    }
  )
);
