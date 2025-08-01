import { io, Socket } from 'socket.io-client';
import { SocketEvents } from '@/types/game';
import { getApiUrl } from '@/utils/api';

class SocketClient {
  private socket: Socket | null = null;
  private url: string;

  constructor(url: string = typeof window !== 'undefined' ? getApiUrl() : 'http://localhost:8000') {
    this.url = url;
  }

  connect(): Socket<SocketEvents> {
    if (this.socket?.connected) {
      return this.socket as Socket<SocketEvents>;
    }

    console.log('🔌 Creating socket connection to:', this.url);
    
    this.socket = io(this.url, {
      transports: ['polling', 'websocket'],
      autoConnect: true,
      timeout: 20000,
      forceNew: true,
      // Enhanced retry configuration
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      // Upgrade handling
      upgrade: true,
      forceBase64: false,
    });

    console.log('🔌 Socket created:', this.socket);

    this.socket.on('connect', () => {
      console.log('✅ Connected to server');
    });

    this.socket.on('disconnect', (reason: string) => {
      console.log('❌ Disconnected from server:', reason);
    });

    this.socket.on('connect_error', (error: any) => {
      console.error('🔥 Connection error:', error);
    });

    this.socket.on('reconnect', (attemptNumber: number) => {
      console.log('🔄 Reconnected to server after', attemptNumber, 'attempts');
    });

    this.socket.on('reconnect_attempt', (attemptNumber: number) => {
      console.log('🔄 Reconnection attempt', attemptNumber);
    });

    this.socket.on('reconnect_error', (error: any) => {
      console.error('🔥 Reconnection error:', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('❌ Reconnection failed after all attempts');
    });

    return this.socket as Socket<SocketEvents>;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  getSocket(): Socket<SocketEvents> | null {
    return this.socket as Socket<SocketEvents> | null;
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const socketClient = new SocketClient();