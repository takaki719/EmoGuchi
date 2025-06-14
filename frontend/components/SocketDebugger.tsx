import React, { useEffect, useState } from 'react';
import { useSocket } from '@/hooks/useSocket';

export const SocketDebugger: React.FC = () => {
  const { socket, isConnected } = useSocket();
  const [events, setEvents] = useState<Array<{ timestamp: string; event: string; data: any }>>([]);

  useEffect(() => {
    if (!socket) return;

    const handleAnyEvent = (eventName: string, ...args: any[]) => {
      setEvents(prev => [...prev.slice(-9), {
        timestamp: new Date().toLocaleTimeString(),
        event: eventName,
        data: args
      }]);
    };

    socket.onAny(handleAnyEvent);

    return () => {
      socket.offAny(handleAnyEvent);
    };
  }, [socket]);

  const testAudioSend = () => {
    console.log('🧪 Testing audio_send event - Start');
    console.log('Socket available:', !!socket);
    console.log('Socket connected:', socket?.connected);
    console.log('Socket ID:', socket?.id);
    
    if (socket && socket.connected) {
      console.log('🧪 Sending test audio_send event');
      const testData = new ArrayBuffer(1024); // 1KB test data
      console.log('Test data created, size:', testData.byteLength);
      
      try {
        socket.emit('audio_send', { audio: testData });
        console.log('✅ Test audio_send emitted successfully');
      } catch (error) {
        console.error('❌ Error emitting audio_send:', error);
      }
    } else {
      console.error('❌ Socket not available or not connected');
      console.log('Available socket methods:', socket ? Object.getOwnPropertyNames(socket) : 'No socket');
    }
  };

  return (
    <div className="fixed bottom-4 right-4 w-80 h-64 bg-black bg-opacity-90 text-white p-2 rounded text-xs overflow-hidden">
      <div className="flex justify-between items-center mb-2">
        <span>Socket Debug</span>
        <div className="flex space-x-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
          <button 
            onClick={testAudioSend}
            className="bg-blue-600 px-2 py-1 rounded text-xs"
          >
            Test Audio
          </button>
        </div>
      </div>
      <div className="overflow-y-auto h-48">
        {events.map((event, i) => (
          <div key={i} className="mb-1">
            <span className="text-gray-400">{event.timestamp}</span> 
            <span className="text-yellow-400 ml-2">{event.event}</span>
            <div className="text-gray-300 pl-4 break-all">
              {JSON.stringify(event.data, null, 1).slice(0, 100)}...
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};