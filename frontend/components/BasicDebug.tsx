import React from 'react';

export const BasicDebug: React.FC = () => {
  console.log('🟡 BasicDebug component rendering...');

  const testBasicFunctionality = () => {
    console.log('🟡 Basic test function called');
    
    // Test 1: Basic JavaScript
    console.log('✅ JavaScript working');
    
    // Test 2: React state
    console.log('✅ React component working');
    
    // Test 3: Import system
    try {
      console.log('Testing imports...');
      const gameStore = require('@/stores/gameStore');
      console.log('✅ Game store import working');
    } catch (error) {
      console.error('❌ Game store import failed:', error);
    }

    // Test 4: Socket.IO client
    try {
      console.log('Testing socket.io-client import...');
      const io = require('socket.io-client');
      console.log('✅ Socket.IO client import working:', typeof io);
    } catch (error) {
      console.error('❌ Socket.IO client import failed:', error);
    }

    // Test 5: useSocket import
    try {
      console.log('Testing useSocket import...');
      const useSocketModule = require('@/hooks/useSocket');
      console.log('✅ useSocket import working:', typeof useSocketModule.useSocket);
    } catch (error) {
      console.error('❌ useSocket import failed:', error);
    }
  };

  return (
    <div className="fixed top-16 right-4 w-80 bg-orange-100 border-2 border-orange-400 p-3 rounded text-xs">
      <div className="font-bold mb-2">Basic Debug</div>
      <button 
        onClick={testBasicFunctionality}
        className="w-full bg-orange-500 text-white px-2 py-1 rounded"
      >
        Test Basic Functionality
      </button>
      <div className="mt-2 text-xs">
        Check console for detailed results
      </div>
    </div>
  );
};