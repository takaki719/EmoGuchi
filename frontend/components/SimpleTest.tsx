import React from 'react';

export const SimpleTest: React.FC = () => {
  const handleClick = () => {
    console.log('🚨 SIMPLE TEST BUTTON CLICKED');
    console.log('🚨 Time:', new Date().toISOString());
    alert('Test button clicked!');
  };

  return (
    <div className="fixed top-4 left-4 bg-red-500 text-white p-4 rounded">
      <button 
        onClick={handleClick}
        className="bg-yellow-500 text-black px-4 py-2 rounded font-bold"
      >
        SIMPLE TEST
      </button>
      <div className="mt-2 text-xs">
        Click to verify React events work
      </div>
    </div>
  );
};