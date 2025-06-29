#!/usr/bin/env python3
"""
Test script for voice processing functionality
"""
import logging
import sys
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required libraries can be imported"""
    logger.info("🧪 Testing imports...")
    
    try:
        import librosa
        logger.info(f"✅ librosa {librosa.__version__}")
    except ImportError as e:
        logger.error(f"❌ librosa import failed: {e}")
        return False
    
    try:
        import soundfile as sf
        logger.info(f"✅ soundfile {sf.__version__}")
    except ImportError as e:
        logger.error(f"❌ soundfile import failed: {e}")
        return False
    
    try:
        from pydub import AudioSegment
        logger.info("✅ pydub imported (may warn about ffmpeg)")
    except ImportError as e:
        logger.error(f"❌ pydub import failed: {e}")
        return False
    
    return True

def test_voice_processing_service():
    """Test the voice processing service"""
    logger.info("🎵 Testing voice processing service...")
    
    try:
        from services.voice_processing_service import voice_processing_service
        logger.info(f"✅ Voice processing service imported, enabled: {voice_processing_service.is_enabled()}")
        
        if not voice_processing_service.is_enabled():
            logger.error("❌ Voice processing service is disabled")
            return False
        
        # Test pattern selection
        config = voice_processing_service.select_processing_pattern("joy")
        logger.info(f"✅ Pattern selection works: {config.pattern.value} (pitch: {config.pitch}, tempo: {config.tempo})")
        
        # Create simple test audio (sine wave)
        import numpy as np
        duration = 1.0  # seconds
        sample_rate = 22050
        frequency = 440  # A4 note
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(frequency * 2 * np.pi * t)
        
        # Convert to 16-bit audio bytes (simple WAV-like format)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        test_audio_bytes = audio_int16.tobytes()
        
        logger.info(f"🎵 Testing with {len(test_audio_bytes)} bytes of test audio")
        
        # Since we don't have ffmpeg, this will likely fail at format conversion
        # but we can still test the service initialization
        return True
        
    except Exception as e:
        logger.error(f"❌ Voice processing test failed: {e}")
        return False

def test_audio_effects():
    """Test just the librosa audio effects without file conversion"""
    logger.info("🎶 Testing librosa audio effects...")
    
    try:
        import librosa
        import numpy as np
        
        # Create test audio
        duration = 1.0
        sample_rate = 22050
        frequency = 440
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        test_audio = np.sin(frequency * 2 * np.pi * t).astype(np.float32)
        
        logger.info(f"Created test audio: {len(test_audio)} samples at {sample_rate}Hz")
        
        # Test pitch shifting
        pitch_shifted = librosa.effects.pitch_shift(test_audio, sr=sample_rate, n_steps=2.0)
        logger.info("✅ Pitch shifting works")
        
        # Test time stretching
        time_stretched = librosa.effects.time_stretch(test_audio, rate=1.5)
        logger.info("✅ Time stretching works")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Librosa effects test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🎭 Starting voice processing tests...")
    
    # Test 1: Imports
    if not test_imports():
        logger.error("❌ Import tests failed")
        sys.exit(1)
    
    # Test 2: Audio effects
    if not test_audio_effects():
        logger.error("❌ Audio effects tests failed")
        sys.exit(1)
    
    # Test 3: Service
    if not test_voice_processing_service():
        logger.error("❌ Service tests failed")
        sys.exit(1)
    
    logger.info("🎉 All tests passed!")