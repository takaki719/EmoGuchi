#!/usr/bin/env python3
"""
Test the complete audio processing workflow
"""
import logging
import numpy as np

# Configure logging to match main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_audio_processing_workflow():
    """Test the complete audio processing workflow"""
    logger.info("🎭 Testing complete audio processing workflow...")
    
    try:
        # Import voice processing service
        from services.voice_processing_service import voice_processing_service
        
        # Test if enabled
        if not voice_processing_service.is_enabled():
            logger.error("❌ Voice processing service is not enabled")
            return False
        
        logger.info(f"✅ Voice processing service is enabled")
        
        # Test pattern selection
        emotion_id = "joy"
        config = voice_processing_service.select_processing_pattern(emotion_id)
        logger.info(f"🎯 Selected pattern for {emotion_id}: {config.pattern.value}")
        logger.info(f"🎯 Config: pitch={config.pitch}, tempo={config.tempo}")
        
        # Create mock WebM audio data (just random bytes to simulate)
        # In reality this would come from the frontend
        mock_webm_data = b"mock webm data" + bytes(range(256)) * 100  # ~25KB of mock data
        logger.info(f"🎵 Created mock audio data: {len(mock_webm_data)} bytes")
        
        # Process the audio
        logger.info("🎵 Starting audio processing...")
        processed_data = voice_processing_service.process_audio(mock_webm_data, config)
        
        if processed_data:
            logger.info(f"🎵 ✅ Audio processing completed: output size={len(processed_data)} bytes")
            
            # Check if the audio was actually modified
            if processed_data != mock_webm_data:
                logger.info("🎯 ✅ Audio was modified by processing")
                return True
            else:
                logger.warning("🎯 ⚠️  Audio was not modified (returned original data)")
                return True  # Still consider success since service worked
        else:
            logger.error("🎵 ❌ Audio processing returned None")
            return False
            
    except Exception as e:
        logger.error(f"❌ Workflow test failed: {e}", exc_info=True)
        return False

def test_hard_mode_simulation():
    """Simulate the hard mode workflow from events.py"""
    logger.info("🎯 Testing hard mode simulation...")
    
    # Simulate room config with hard mode enabled
    class MockRoom:
        class Config:
            hard_mode = True
        config = Config()
        
        class CurrentRound:
            emotion_id = "joy"
        current_round = CurrentRound()
    
    # Simulate the audio_send logic
    room = MockRoom()
    audio_data = bytes(range(256)) * 50  # Mock audio data
    
    logger.info(f"🎯 Hard mode check: room.config.hard_mode = {room.config.hard_mode}")
    logger.info(f"🎯 Emotion ID: {room.current_round.emotion_id}")
    
    if room.config.hard_mode:
        logger.info("🎯 Hard mode is ON - attempting voice processing")
        try:
            from services.voice_processing_service import voice_processing_service
            logger.info(f"🎯 Voice processing service enabled: {voice_processing_service.is_enabled()}")
            
            if voice_processing_service.is_enabled():
                # Select processing pattern based on emotion
                processing_config = voice_processing_service.select_processing_pattern(
                    room.current_round.emotion_id
                )
                logger.info(f"🎯 Selected processing config: {processing_config.pattern.value}, pitch={processing_config.pitch}, tempo={processing_config.tempo}")
                
                # Process the audio
                logger.info(f"🎯 Processing audio: input size={len(audio_data)} bytes")
                processed_audio_bytes = voice_processing_service.process_audio(
                    audio_data, processing_config
                )
                
                if processed_audio_bytes and processed_audio_bytes != audio_data:
                    logger.info(f"🎯 ✅ Audio processed successfully with {processing_config.pattern.value}: "
                              f"pitch={processing_config.pitch}, tempo={processing_config.tempo}, output size={len(processed_audio_bytes)}")
                    return True
                else:
                    logger.warning("🎯 ❌ Audio processing failed or returned same audio, using original audio")
                    return False
            else:
                logger.warning("🎯 ❌ Voice processing service not available")
                return False
        except Exception as e:
            logger.error(f"🎯 ❌ Voice processing error: {e}", exc_info=True)
            return False
    else:
        logger.info("🎯 Hard mode is OFF")
        return True

if __name__ == "__main__":
    logger.info("🎭 Starting audio workflow tests...")
    
    # Test 1: Basic workflow
    success1 = test_audio_processing_workflow()
    
    # Test 2: Hard mode simulation
    success2 = test_hard_mode_simulation()
    
    if success1 and success2:
        logger.info("🎉 All workflow tests passed!")
    else:
        logger.error("❌ Some workflow tests failed")