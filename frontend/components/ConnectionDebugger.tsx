import React, { useEffect, useState } from 'react';
import { useSocket } from '@/hooks/useSocket';

export const ConnectionDebugger: React.FC = () => {
  const { socket, isConnected } = useSocket();
  const [details, setDetails] = useState<any>({});

  useEffect(() => {
    const updateDetails = () => {
      setDetails({
        socket: !!socket,
        connected: socket?.connected,
        id: socket?.id,
        transport: socket?.io?.engine?.transport?.name,
        url: 'hidden', // socket?.io?.uri is private
        readyState: socket?.io?.engine?.readyState,
      });
    };

    updateDetails();
    const interval = setInterval(updateDetails, 1000);
    return () => clearInterval(interval);
  }, [socket]);

  const testConnection = () => {
    console.log('🔍 Connection Test');
    console.log('Socket exists:', !!socket);
    console.log('IsConnected hook:', isConnected);
    console.log('Socket.connected:', socket?.connected);
    console.log('Socket ID:', socket?.id);
    
    if (socket) {
      console.log('Transport:', socket.io?.engine?.transport?.name);
      console.log('Socket URL:', 'hidden'); // socket.io.uri is private
    }
  };

  return (
    <div className="fixed top-4 right-4 w-80 bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 p-3 rounded text-xs shadow-lg">
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold text-gray-800 dark:text-white">Connection Debug</span>
        <button 
          onClick={testConnection}
          className="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs transition-colors"
        >
          Test
        </button>
      </div>
      
      <div className="space-y-1 text-gray-700 dark:text-gray-300">
        <div>Socket: <span className={details.socket ? 'text-green-600' : 'text-red-600'}>{details.socket ? 'YES' : 'NO'}</span></div>
        <div>Connected: <span className={details.connected ? 'text-green-600' : 'text-red-600'}>{details.connected ? 'YES' : 'NO'}</span></div>
        <div>ID: <span className="text-blue-600">{details.id || 'None'}</span></div>
        <div>Transport: <span className="text-purple-600">{details.transport || 'None'}</span></div>
        <div>URL: <span className="text-gray-600 break-all">{details.url || 'None'}</span></div>
        <div>Ready State: <span className="text-orange-600">{details.readyState}</span></div>
      </div>
    </div>
  );
};