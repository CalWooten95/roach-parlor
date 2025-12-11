import { io, Socket } from 'socket.io-client';
import { WebSocketEvents } from '@/types';

class SocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(token?: string): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io('/', {
      auth: {
        token: token || localStorage.getItem('authToken'),
      },
      transports: ['websocket', 'polling'],
      upgrade: true,
    });

    this.setupEventListeners();
    return this.socket;
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  emit<K extends keyof WebSocketEvents>(
    event: K,
    data: WebSocketEvents[K]
  ): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  on<K extends keyof WebSocketEvents>(
    event: K,
    callback: (data: WebSocketEvents[K]) => void
  ): void {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off<K extends keyof WebSocketEvents>(
    event: K,
    callback?: (data: WebSocketEvents[K]) => void
  ): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect automatically
        return;
      }

      // Attempt to reconnect
      this.attemptReconnect();
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.attemptReconnect();
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.socket?.connect();
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
}

// Export singleton instance
export const socketService = new SocketService();
export default socketService;