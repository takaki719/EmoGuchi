import React from 'react';
import { socketClient } from '@/socket/client';

export const DirectAudioTest: React.FC = () => {
  const testDirectAudioSend = () => {
    console.log('🧪 Direct Audio Test Starting...');
    
    try {
      const socket = socketClient.getSocket();
      console.log('Socket available:', !!socket);
      console.log('Socket connected:', socket?.connected);
      console.log('Socket ID:', socket?.id);
      
      if (socket && socket.connected) {
        // Create fake audio data
        const fakeAudioData = new ArrayBuffer(1024);
        const fakeAudioView = new Uint8Array(fakeAudioData);
        for (let i = 0; i < 1024; i++) {
          fakeAudioView[i] = Math.floor(Math.random() * 256);
        }
        
        console.log('🧪 Created fake audio data, size:', fakeAudioData.byteLength);
        console.log('🧪 Fake audio preview:', fakeAudioView.slice(0, 10));
        
        // Send audio_send event directly
        console.log('🧪 Emitting audio_send event...');
        socket.emit('audio_send', { audio: fakeAudioData });
        console.log('✅ Direct audio_send emitted');
        
        // Check for any error events
        socket.once('error', (error) => {
          console.error('❌ Socket error received:', error);
        });
        
        // Check for any response
        setTimeout(() => {
          console.log('🧪 Checking for any response after 3 seconds...');
        }, 3000);
        
      } else {
        console.error('❌ Socket not available for direct test');
      }
      
    } catch (error) {
      console.error('❌ Direct audio test failed:', error);
    }
  };

  return (
    <div className="fixed top-48 right-4 w-80 bg-red-100 border-2 border-red-400 p-3 rounded text-xs">
      <div className="font-bold mb-2">Direct Audio Test</div>
      <button 
        onClick={testDirectAudioSend}
        className="w-full bg-red-500 text-white px-2 py-1 rounded"
      >
        Test Direct Audio Send
      </button>
      <div className="mt-2 text-xs">
        Sends fake audio data directly via socket
      </div>
    </div>
  );
};