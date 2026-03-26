export type WSMessageType =
  | 'task_progress'
  | 'page_discovered'
  | 'page_tested'
  | 'issue_found'
  | 'agent_reasoning'
  | 'event_detected'
  | 'task_completed'
  | 'task_failed'
  | 'error'
  | 'pong';

export interface WSMessage {
  type: WSMessageType;
  task_id: string;
  data: Record<string, unknown>;
  timestamp?: string;
}
