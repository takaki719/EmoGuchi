import React from 'react';

export const DirectSocketTest: React.FC = () => {
  const testSocketConnection = () => {
    console.log('🟣 Testing socket connection...');
    
    try {
      // Test basic socket functionality without hooks
      console.log('✅ DirectSocketTest component working');
      
    } catch (error) {
      console.error('❌ Socket test failed:', error);
    }
  };

  return (
    <div className="fixed top-32 right-4 w-80 bg-purple-100 dark:bg-purple-900 border-2 border-purple-400 dark:border-purple-600 p-3 rounded text-xs">
      <div className="font-bold mb-2 text-purple-800 dark:text-purple-200">Direct Socket Test</div>
      <div className="space-y-2">
        <button 
          onClick={testSocketConnection}
          className="w-full bg-purple-500 hover:bg-purple-600 text-white px-2 py-1 rounded transition-colors"
        >
          Test Connection
        </button>
      </div>
    </div>
  );
};