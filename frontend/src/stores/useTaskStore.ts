import { create } from 'zustand';
import type { Task, TaskCreate, TaskProgress } from '../types/task';
import type { Issue } from '../types/a11y';
import * as api from '../api/tasks';

interface TaskState {
  tasks: Task[];
  total: number;
  loading: boolean;
  currentTask: Task | null;
  taskProgress: TaskProgress | null;
  issues: Issue[];
  issuesTotal: number;
  agentLogs: Array<{ agent: string; reasoning: string; timestamp: string }>;

  fetchTasks: (params?: { project_id?: string; status?: string }) => Promise<void>;
  fetchTask: (id: string) => Promise<void>;
  addTask: (data: TaskCreate) => Promise<Task>;
  startTask: (id: string) => Promise<void>;
  stopTask: (id: string) => Promise<void>;
  removeTask: (id: string) => Promise<void>;
  fetchIssues: (taskId: string, params?: { severity?: string; status?: string; skip?: number; limit?: number }) => Promise<void>;
  updateProgress: (progress: TaskProgress) => void;
  addAgentLog: (log: { agent: string; reasoning: string; timestamp: string }) => void;
  clearLogs: () => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  total: 0,
  loading: false,
  currentTask: null,
  taskProgress: null,
  issues: [],
  issuesTotal: 0,
  agentLogs: [],

  fetchTasks: async (params) => {
    set({ loading: true });
    try {
      const data = await api.getTasks(params);
      set({ tasks: data.items, total: data.total });
    } finally {
      set({ loading: false });
    }
  },

  fetchTask: async (id: string) => {
    set({ loading: true });
    try {
      const task = await api.getTask(id);
      set({ currentTask: task });
    } finally {
      set({ loading: false });
    }
  },

  addTask: async (data) => {
    const task = await api.createTask(data);
    set((state) => ({ tasks: [task, ...state.tasks], total: state.total + 1 }));
    return task;
  },

  startTask: async (id: string) => {
    const task = await api.startTask(id);
    set((state) => ({
      currentTask: task,
      tasks: state.tasks.map((t) => (t.id === id ? task : t)),
    }));
  },

  stopTask: async (id: string) => {
    const task = await api.stopTask(id);
    set((state) => ({
      currentTask: task,
      tasks: state.tasks.map((t) => (t.id === id ? task : t)),
    }));
  },

  removeTask: async (id: string) => {
    await api.deleteTask(id);
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== id),
      total: state.total - 1,
    }));
  },

  fetchIssues: async (taskId, params) => {
    const data = await api.getTaskIssues(taskId, params);
    set({ issues: data.items, issuesTotal: data.total });
  },

  updateProgress: (progress) => {
    set({ taskProgress: progress });
  },

  addAgentLog: (log) => {
    set((state) => ({
      agentLogs: [...state.agentLogs.slice(-99), log],
    }));
  },

  clearLogs: () => set({ agentLogs: [] }),
}));
