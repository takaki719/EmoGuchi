import React, { useState } from 'react';

export const BackendTester: React.FC = () => {
  const [testResult, setTestResult] = useState<string>('');

  const testBackendAudioEndpoint = async () => {
    console.log('🧪 Testing backend audio_send event handling...');
    setTestResult('Testing...');

    try {
      // Test if backend is responding to Socket.IO events
      const response = await fetch('http://localhost:8000/health');
      const health = await response.json();
      console.log('✅ Backend health check:', health);
      
      // Test Socket.IO endpoint specifically
      const socketResponse = await fetch('http://localhost:8000/socket.io/', {
        method: 'GET'
      });
      
      console.log('Socket.IO endpoint status:', socketResponse.status);
      console.log('Socket.IO endpoint headers:', Array.from(socketResponse.headers.entries()));
      
      if (socketResponse.status === 200) {
        setTestResult('✅ Backend and Socket.IO responding');
      } else {
        setTestResult(`❌ Socket.IO issue: ${socketResponse.status}`);
      }
      
    } catch (error) {
      console.error('❌ Backend test failed:', error);
      setTestResult(`❌ Backend error: ${error}`);
    }
  };

  const checkCurrentRoom = () => {
    console.log('🧪 Checking current room state...');
    
    // Get current room info from URL
    const path = window.location.pathname;
    const roomMatch = path.match(/\/room\/([^\/]+)/);
    const roomId = roomMatch ? decodeURIComponent(roomMatch[1]) : null;
    
    console.log('Current room ID:', roomId);
    console.log('Current URL:', window.location.href);
    
    setTestResult(`Room ID: ${roomId || 'Not found'}`);
  };

  return (
    <div className="fixed bottom-64 left-4 w-80 bg-blue-100 border-2 border-blue-400 p-3 rounded text-xs">
      <div className="font-bold mb-2">Backend Tester</div>
      <div className="mb-2 text-xs bg-gray-200 p-2 rounded">
        Result: {testResult || 'No test run yet'}
      </div>
      <div className="space-y-2">
        <button 
          onClick={testBackendAudioEndpoint}
          className="w-full bg-blue-500 text-white px-2 py-1 rounded"
        >
          Test Backend Health
        </button>
        <button 
          onClick={checkCurrentRoom}
          className="w-full bg-green-500 text-white px-2 py-1 rounded"
        >
          Check Room State
        </button>
      </div>
    </div>
  );
};