import React, { useEffect, useState } from 'react';
import { useSocket } from '@/hooks/useSocket';

export const ConnectionDebugger: React.FC = () => {
  console.log('🔍 ConnectionDebugger component rendering...');
  
  let socket, isConnected;
  try {
    console.log('🔍 About to call useSocket()...');
    const hookResult = useSocket();
    socket = hookResult.socket;
    isConnected = hookResult.isConnected;
    console.log('🔍 useSocket() completed successfully');
    console.log('🔍 Hook result:', { socket: !!socket, isConnected });
  } catch (error) {
    console.error('❌ useSocket() failed:', error);
    socket = null;
    isConnected = false;
  }
  const [details, setDetails] = useState<any>({});

  useEffect(() => {
    const updateDetails = () => {
      setDetails({
        socket: !!socket,
        connected: socket?.connected,
        id: socket?.id,
        transport: socket?.io?.engine?.transport?.name,
        url: socket?.io?.uri,
        readyState: socket?.io?.engine?.readyState,
        events: socket ? Object.getOwnPropertyNames(socket) : []
      });
    };

    updateDetails();
    const interval = setInterval(updateDetails, 1000);
    return () => clearInterval(interval);
  }, [socket]);

  const testConnection = () => {
    console.log('🔍 ======================');
    console.log('🔍 CONNECTION TEST START');
    console.log('🔍 ======================');
    console.log('🔍 testConnection function called successfully');
    
    // Basic checks
    console.log('1. Socket exists:', !!socket);
    console.log('2. IsConnected hook:', isConnected);
    console.log('3. Socket.connected:', socket?.connected);
    console.log('4. Socket ID:', socket?.id);
    console.log('5. Socket emit function type:', typeof socket?.emit);
    
    // Detailed socket info
    if (socket) {
      console.log('6. Socket properties:', Object.getOwnPropertyNames(socket));
      console.log('7. Socket.io exists:', !!socket.io);
      console.log('8. Socket.io.engine exists:', !!socket.io?.engine);
      console.log('9. Engine ready state:', socket.io?.engine?.readyState);
      console.log('10. Transport:', socket.io?.engine?.transport?.name);
      console.log('11. Socket URL:', socket.io?.uri);
      
      try {
        console.log('12. Testing basic emit...');
        const result = socket.emit('test_event', { test: 'data' });
        console.log('13. Emit result:', result);
        console.log('✅ Emit succeeded');
      } catch (error) {
        console.error('❌ Emit failed:', error);
      }
    } else {
      console.error('❌ No socket available for testing');
    }
    
    console.log('🔍 CONNECTION TEST END');
    console.log('🔍 ====================');
  };

  return (
    <div className="fixed top-4 right-4 w-80 bg-white border-2 border-gray-300 p-3 rounded text-xs shadow-lg">
      <div className="flex justify-between items-center mb-2">
        <span className="font-bold">Connection Debug</span>
        <button 
          onClick={() => {
            console.log('🔴 TEST BUTTON CLICKED - Starting test...');
            console.log('🔴 Button onClick handler executing...');
            try {
              testConnection();
            } catch (error) {
              console.error('❌ testConnection failed:', error);
            }
          }}
          className="bg-blue-500 text-white px-2 py-1 rounded text-xs"
        >
          Test
        </button>
      </div>
      
      <div className="space-y-1">
        <div>Socket: <span className={details.socket ? 'text-green-600' : 'text-red-600'}>{details.socket ? 'YES' : 'NO'}</span></div>
        <div>Connected: <span className={details.connected ? 'text-green-600' : 'text-red-600'}>{details.connected ? 'YES' : 'NO'}</span></div>
        <div>ID: <span className="text-blue-600">{details.id || 'None'}</span></div>
        <div>Transport: <span className="text-purple-600">{details.transport || 'None'}</span></div>
        <div>URL: <span className="text-gray-600 break-all">{details.url || 'None'}</span></div>
        <div>Ready State: <span className="text-orange-600">{details.readyState}</span></div>
        <div>Emit Function: <span className={socket?.emit ? 'text-green-600' : 'text-red-600'}>{socket?.emit ? 'Available' : 'Missing'}</span></div>
      </div>
    </div>
  );
};