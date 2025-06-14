import React, { useState } from 'react';
import { io } from 'socket.io-client';

export const ManualSocketTest: React.FC = () => {
  const [status, setStatus] = useState<string>('Not started');
  const [socket, setSocket] = useState<any>(null);

  const testDirectConnection = () => {
    console.log('🧪 Manual Socket Test Starting...');
    setStatus('Starting...');

    try {
      const url = 'http://localhost:8000';
      console.log('🧪 Creating socket to:', url);
      
      const testSocket = io(url, {
        transports: ['polling', 'websocket'],
        autoConnect: true,
        timeout: 5000,
      });

      testSocket.on('connect', () => {
        console.log('✅ Manual socket connected!');
        setStatus('Connected!');
        setSocket(testSocket);
      });

      testSocket.on('connect_error', (error) => {
        console.error('❌ Manual socket connection error:', error);
        setStatus(`Error: ${error.message}`);
      });

      testSocket.on('disconnect', () => {
        console.log('🔌 Manual socket disconnected');
        setStatus('Disconnected');
      });

    } catch (error) {
      console.error('❌ Failed to create socket:', error);
      setStatus(`Failed: ${error}`);
    }
  };

  const testEmit = () => {
    if (socket && socket.connected) {
      console.log('🧪 Testing emit on manual socket...');
      socket.emit('test_event', { test: 'manual data' });
      console.log('✅ Manual emit completed');
    } else {
      console.log('❌ Manual socket not available');
    }
  };

  const disconnect = () => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
      setStatus('Manually disconnected');
    }
  };

  return (
    <div className="fixed bottom-4 left-4 w-80 bg-yellow-100 border-2 border-yellow-400 p-3 rounded text-xs">
      <div className="font-bold mb-2">Manual Socket Test</div>
      <div className="mb-2">Status: <span className="font-mono">{status}</span></div>
      <div className="space-y-2">
        <button 
          onClick={testDirectConnection}
          className="w-full bg-green-500 text-white px-2 py-1 rounded"
        >
          Connect Manually
        </button>
        <button 
          onClick={testEmit}
          disabled={!socket?.connected}
          className="w-full bg-blue-500 disabled:bg-gray-400 text-white px-2 py-1 rounded"
        >
          Test Emit
        </button>
        <button 
          onClick={disconnect}
          disabled={!socket}
          className="w-full bg-red-500 disabled:bg-gray-400 text-white px-2 py-1 rounded"
        >
          Disconnect
        </button>
      </div>
    </div>
  );
};