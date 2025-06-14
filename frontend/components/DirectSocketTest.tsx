import React from 'react';

export const DirectSocketTest: React.FC = () => {
  const testUseSocketDirectly = () => {
    console.log('🟣 Testing useSocket directly...');
    
    try {
      // Import useSocket directly
      const { useSocket } = require('@/hooks/useSocket');
      console.log('✅ useSocket imported successfully');
      
      // Try to call it (this might fail because we're outside React component context)
      console.log('🟣 About to call useSocket...');
      const result = useSocket();
      console.log('✅ useSocket called successfully:', result);
      
    } catch (error) {
      console.error('❌ useSocket failed:', error);
      console.error('Error details:', error.message);
      console.error('Error stack:', error.stack);
    }
  };

  const testSocketClientDirectly = () => {
    console.log('🟣 Testing socketClient directly...');
    
    try {
      const { socketClient } = require('@/socket/client');
      console.log('✅ socketClient imported successfully');
      console.log('🟣 socketClient object:', socketClient);
      
      console.log('🟣 About to call socketClient.connect()...');
      const socket = socketClient.connect();
      console.log('✅ socketClient.connect() successful:', socket);
      console.log('Socket type:', typeof socket);
      console.log('Socket connected:', socket?.connected);
      console.log('Socket id:', socket?.id);
      
      // Try emit test
      if (socket) {
        console.log('🟣 Testing emit on socketClient socket...');
        socket.emit('test_event', { source: 'DirectSocketTest' });
        console.log('✅ Emit on socketClient successful');
      }
      
    } catch (error) {
      console.error('❌ socketClient failed:', error);
      console.error('Error details:', error.message);
    }
  };

  return (
    <div className="fixed top-32 right-4 w-80 bg-purple-100 border-2 border-purple-400 p-3 rounded text-xs">
      <div className="font-bold mb-2">Direct Socket Test</div>
      <div className="space-y-2">
        <button 
          onClick={testUseSocketDirectly}
          className="w-full bg-purple-500 text-white px-2 py-1 rounded"
        >
          Test useSocket Hook
        </button>
        <button 
          onClick={testSocketClientDirectly}
          className="w-full bg-purple-600 text-white px-2 py-1 rounded"
        >
          Test socketClient
        </button>
      </div>
    </div>
  );
};