"""Simple audio handling without complex authentication"""
import socketio
import logging

logger = logging.getLogger(__name__)

def setup_simple_audio_events(sio: socketio.AsyncServer):
    """Setup simple audio events without complex session checking"""
    
    @sio.event
    async def audio_send(sid, data):
        """Simple audio relay - just forward to all other clients"""
        logger.info(f"✅ Simple audio_send received from {sid}")
        
        if 'audio' in data:
            logger.info(f"✅ Broadcasting audio to all other clients")
            
            # Simple broadcast to all connected clients except sender
            await sio.emit('audio_received', {
                'audio': data['audio'],
                'speaker_name': 'Speaker'  # Simple name
            }, skip_sid=sid)
            
            logger.info(f"✅ Audio broadcast complete")
        else:
            logger.warning(f"❌ No audio data in event from {sid}")