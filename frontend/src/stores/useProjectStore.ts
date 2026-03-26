import { create } from 'zustand';
import type { Project } from '../types/project';
import * as api from '../api/projects';

interface ProjectState {
  projects: Project[];
  total: number;
  loading: boolean;
  currentProject: Project | null;
  fetchProjects: (skip?: number, limit?: number) => Promise<void>;
  fetchProject: (id: string) => Promise<void>;
  addProject: (data: { name: string; description?: string; base_url: string }) => Promise<Project>;
  removeProject: (id: string) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  total: 0,
  loading: false,
  currentProject: null,

  fetchProjects: async (skip = 0, limit = 20) => {
    set({ loading: true });
    try {
      const data = await api.getProjects(skip, limit);
      set({ projects: data.items, total: data.total });
    } finally {
      set({ loading: false });
    }
  },

  fetchProject: async (id: string) => {
    set({ loading: true });
    try {
      const project = await api.getProject(id);
      set({ currentProject: project });
    } finally {
      set({ loading: false });
    }
  },

  addProject: async (data) => {
    const project = await api.createProject(data);
    set((state) => ({ projects: [project, ...state.projects], total: state.total + 1 }));
    return project;
  },

  removeProject: async (id: string) => {
    await api.deleteProject(id);
    set((state) => ({
      projects: state.projects.filter((p) => p.id !== id),
      total: state.total - 1,
    }));
  },
}));
