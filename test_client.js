const io = require('socket.io-client');

// Connect to the server
const socket = io('http://localhost:8000', {
  transports: ['websocket']
});

socket.on('connect', () => {
  console.log('✅ Connected to server');
  
  // Test joining a room
  socket.emit('join_room', {
    roomId: 'cf1a9c2a-239d-46b9-801a-3572135a3980',
    playerName: 'TestPlayer'
  });
});

socket.on('connected', (data) => {
  console.log('📨 Server message:', data.message);
});

socket.on('room_state', (data) => {
  console.log('🏠 Room state:', data);
});

socket.on('player_joined', (data) => {
  console.log('👥 Player joined:', data);
});

socket.on('round_start', (data) => {
  console.log('🎯 Round started:', data);
});

socket.on('speaker_emotion', (data) => {
  console.log('😄 Speaker emotion:', data);
});

socket.on('error', (data) => {
  console.log('❌ Error:', data);
});

socket.on('disconnect', () => {
  console.log('❌ Disconnected from server');
});

// Keep the client running for testing
setTimeout(() => {
  console.log('🔄 Test completed');
  process.exit(0);
}, 5000);