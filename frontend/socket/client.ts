import { io, Socket } from 'socket.io-client';
import { SocketEvents } from '@/types/game';

class SocketClient {
  private socket: Socket | null = null;
  private url: string;

  constructor(url: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
    this.url = url;
  }

  connect(): Socket<SocketEvents> {
    if (this.socket?.connected) {
      return this.socket as Socket<SocketEvents>;
    }

    this.socket = io(this.url, {
      transports: ['websocket'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('Connected to server');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
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