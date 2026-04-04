import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ExecutionLog, NodeExecution, ExecutionStatus, TriggerType } from '../types';
import { executionApi, mapExecutionResponse, workflowApi } from '../services/api';

function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

// Mock execution logs
const mockLogs: ExecutionLog[] = [
  {
    id: 'exec-001',
    workflowId: 'wf-001',
    workflowName: '周报自动生成器',
    triggerType: 'cron',
    status: 'success',
    startTime: '2026-03-23T09:00:00+08:00',
    endTime: '2026-03-23T09:00:12+08:00',
    duration: 12,
    nodeExecutions: [
      {
        nodeId: 'node-1',
        nodeName: '定时触发',
        status: 'success',
        startTime: '2026-03-23T09:00:00+08:00',
        endTime: '2026-03-23T09:00:00.1+08:00',
        duration: 0.1,
        input: { trigger_time: '2026-03-23T09:00:00' },
        output: { triggered: true },
      },
      {
        nodeId: 'node-2',
        nodeName: '生成周报',
        status: 'success',
        startTime: '2026-03-23T09:00:00.1+08:00',
        endTime: '2026-03-23T09:00:10.6+08:00',
        duration: 10.5,
        input: { prompt: '请根据以下数据生成周报：...', data: '本周GMV...' },
        output: { weekly_report: '本周GMV增长5%，新增用户200人...' },
      },
      {
        nodeId: 'node-3',
        nodeName: '发送飞书消息',
        status: 'success',
        startTime: '2026-03-23T09:00:10.6+08:00',
        endTime: '2026-03-23T09:00:11.8+08:00',
        duration: 1.2,
        input: { chatId: 'oc_feishu_group_001', message: '本周GMV增长5%...' },
        output: { message_id: 'om_abc123' },
      },
    ],
  },
  {
    id: 'exec-002',
    workflowId: 'wf-001',
    workflowName: '周报自动生成器',
    triggerType: 'cron',
    status: 'success',
    startTime: '2026-03-22T09:00:00+08:00',
    endTime: '2026-03-22T09:00:15+08:00',
    duration: 15,
    nodeExecutions: [
      {
        nodeId: 'node-1',
        nodeName: '定时触发',
        status: 'success',
        startTime: '2026-03-22T09:00:00+08:00',
        endTime: '2026-03-22T09:00:00.1+08:00',
        duration: 0.1,
        input: { trigger_time: '2026-03-22T09:00:00' },
        output: { triggered: true },
      },
      {
        nodeId: 'node-2',
        nodeName: '生成周报',
        status: 'success',
        startTime: '2026-03-22T09:00:00.1+08:00',
        endTime: '2026-03-22T09:00:13+08:00',
        duration: 12.9,
        input: { prompt: '请根据以下数据生成周报：...', data: '本周GMV...' },
        output: { weekly_report: '本周GMV持平...' },
      },
      {
        nodeId: 'node-3',
        nodeName: '发送飞书消息',
        status: 'success',
        startTime: '2026-03-22T09:00:13+08:00',
        endTime: '2026-03-22T09:00:14.8+08:00',
        duration: 1.8,
        input: { chatId: 'oc_feishu_group_001', message: '本周GMV持平...' },
        output: { message_id: 'om_def456' },
      },
    ],
  },
  {
    id: 'exec-003',
    workflowId: 'wf-001',
    workflowName: '周报自动生成器',
    triggerType: 'cron',
    status: 'failed',
    startTime: '2026-03-21T09:00:00+08:00',
    endTime: '2026-03-21T09:00:03+08:00',
    duration: 3,
    nodeExecutions: [
      {
        nodeId: 'node-1',
        nodeName: '定时触发',
        status: 'success',
        startTime: '2026-03-21T09:00:00+08:00',
        endTime: '2026-03-21T09:00:00.1+08:00',
        duration: 0.1,
        input: { trigger_time: '2026-03-21T09:00:00' },
        output: { triggered: true },
      },
      {
        nodeId: 'node-2',
        nodeName: '生成周报',
        status: 'failed',
        startTime: '2026-03-21T09:00:00.1+08:00',
        endTime: '2026-03-21T09:00:03+08:00',
        duration: 2.9,
        input: { prompt: '请根据以下数据生成周报：...', data: '' },
        output: {},
        error: 'OpenAI API rate limit exceeded',
      },
    ],
  },
];

interface ExecutionState {
  logs: ExecutionLog[];
  currentLog: ExecutionLog | null;
  isLoading: boolean;

  // Actions
  loadLogs: (workflowId?: string) => Promise<void>;
  getLog: (logId: string) => ExecutionLog | null;
  setCurrentLog: (log: ExecutionLog | null) => void;
  runWorkflow: (workflowId: string) => Promise<ExecutionLog>;
}

export const useExecutionStore = create<ExecutionState>()(
  persist(
    (set, get) => ({
      logs: mockLogs,
      currentLog: null,
      isLoading: false,

      loadLogs: async (workflowId?: string) => {
        // If no workflowId provided, keep mock/demo logs
        if (!workflowId) {
          set({ isLoading: false });
          return;
        }

        set({ isLoading: true });
        try {
          const data = await executionApi.list(workflowId);
          const mappedLogs = data.items.map((item) => mapExecutionResponse(item));
          set({ logs: [...mappedLogs, ...get().logs.filter((l) => l.id.startsWith('exec-'))], isLoading: false });
        } catch {
          // Keep existing mock data when API is unavailable
          set({ isLoading: false });
        }
      },

      getLog: (logId) => {
        return get().logs.find((l) => l.id === logId) || null;
      },

      setCurrentLog: (log) => {
        set({ currentLog: log });
      },

      runWorkflow: async (workflowId: string) => {
        set({ isLoading: true });
        try {
          // Call backend to run workflow
          await workflowApi.run(workflowId);
          // Reload logs after run
          const data = await executionApi.list(workflowId);
          const newLogs = data.items.map((item) => mapExecutionResponse(item));
          set((state) => ({
            logs: [...newLogs, ...state.logs.filter((l) => l.workflowId !== workflowId)],
            isLoading: false,
          }));
          return newLogs[0] || get().logs[0];
        } catch {
          // Simulate execution result when API is unavailable
          await new Promise((resolve) => setTimeout(resolve, 2000));

          const isSuccess = Math.random() > 0.2;
          const nodeExecutions: NodeExecution[] = [
            {
              nodeId: 'node-1',
              nodeName: '触发器',
              status: 'success' as ExecutionStatus,
              startTime: new Date().toISOString(),
              endTime: new Date(Date.now() + 100).toISOString(),
              duration: 0.1,
              input: { manual: true },
              output: { triggered: true },
            },
            {
              nodeId: 'node-2',
              nodeName: 'AI任务',
              status: isSuccess ? 'success' : 'failed' as ExecutionStatus,
              startTime: new Date(Date.now() + 100).toISOString(),
              endTime: new Date(Date.now() + 3000).toISOString(),
              duration: isSuccess ? 2.9 : 2.5,
              input: { prompt: 'Generate report' },
              output: isSuccess ? { result: 'Report generated successfully' } : undefined,
              error: isSuccess ? undefined : 'API timeout',
            },
          ];

          const workflow = get().logs.find((l) => l.workflowId === workflowId)?.workflowName || '工作流';
          const newLog: ExecutionLog = {
            id: `exec-${generateId()}`,
            workflowId,
            workflowName: workflow,
            triggerType: 'manual' as TriggerType,
            status: (isSuccess ? 'success' : 'failed') as ExecutionStatus,
            startTime: new Date(Date.now() - 3000).toISOString(),
            endTime: new Date().toISOString(),
            duration: isSuccess ? 3.0 : 2.6,
            nodeExecutions,
          };

          set((state) => ({
            logs: [newLog, ...state.logs],
            isLoading: false,
          }));

          return newLog;
        }
      },
    }),
    {
      name: 'execution-storage',
      partialize: (state) => ({ logs: state.logs }),
    }
  )
);
