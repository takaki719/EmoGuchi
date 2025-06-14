// ブラウザのコンソールで直接実行するテスト
console.log('🟡 Manual Debug Test Starting...');

// Test 1: Basic JavaScript
console.log('✅ JavaScript working');

// Test 2: Check if modules are available
try {
  console.log('Testing require function...');
  console.log('Require available:', typeof require);
} catch (error) {
  console.log('Require not available (normal in browser)');
}

// Test 3: Check global objects
console.log('Window object:', typeof window);
console.log('React available:', typeof React);
console.log('Next.js router:', typeof window.next);

// Test 4: Check if Socket.IO is loaded
console.log('io function available:', typeof io);

console.log('🟡 Manual Debug Test Complete');