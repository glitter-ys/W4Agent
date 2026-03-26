export type TaskStatus = 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export interface TaskConfig {
  max_depth: number;
  max_pages: number;
  wcag_level: string;
  include_patterns: string[];
  exclude_patterns: string[];
  viewport_width: number;
  viewport_height: number;
  enable_ai_detection: boolean;
  enable_screenshots: boolean;
}

export interface Task {
  id: string;
  project_id: string;
  name: string;
  target_url: string;
  status: TaskStatus;
  config: TaskConfig | null;
  pages_discovered: number;
  pages_tested: number;
  issues_found: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  project_id: string;
  name: string;
  target_url: string;
  config?: Partial<TaskConfig>;
}

export interface TaskProgress {
  task_id: string;
  status: TaskStatus;
  pages_discovered: number;
  pages_tested: number;
  issues_found: number;
  current_url?: string;
  current_action?: string;
  agent_reasoning?: string;
}
