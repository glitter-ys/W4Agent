import type { WSMessage } from '../types/ws';

export class TaskWebSocket {
  private ws: WebSocket | null = null;
  private taskId: string;
  private onMessage: (msg: WSMessage) => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(taskId: string, onMessage: (msg: WSMessage) => void) {
    this.taskId = taskId;
    this.onMessage = onMessage;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.ws = new WebSocket(`${protocol}//${host}/ws/task/${this.taskId}`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      console.log(`WebSocket connected for task ${this.taskId}`);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        this.onMessage(msg);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        setTimeout(() => this.connect(), delay);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
