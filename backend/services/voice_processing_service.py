import io
import wave
import logging
import numpy as np
from typing import Optional, Tuple
from models.voice_processing import (
    VoiceProcessingConfig, 
    VoiceProcessingPattern,
    VOICE_PROCESSING_PATTERNS,
    get_voice_processing_config_for_emotion,
    get_random_voice_processing_config
)

logger = logging.getLogger(__name__)

# Add startup log to verify service is being loaded
logger.info("🎵 Voice Processing Service module loaded")

class VoiceProcessingService:
    """
    Voice processing service using librosa for pitch and tempo modifications.
    Implements the 4 basic patterns and emotion reversal as specified in requirements.
    """
    
    def __init__(self):
        self.enabled = True
        logger.info("🎵 Initializing Voice Processing Service...")
        try:
            # Try to import librosa and soundfile
            import librosa
            import soundfile as sf
            from pydub import AudioSegment
            self.librosa = librosa
            self.sf = sf
            self.AudioSegment = AudioSegment
            logger.info("🎵 ✅ Librosa audio processing initialized successfully")
        except ImportError as e:
            logger.error(f"🎵 ❌ Audio processing libraries not available: {e} - voice processing disabled")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if voice processing is available"""
        return self.enabled
    
    def select_processing_pattern(self, emotion_id: str) -> VoiceProcessingConfig:
        """
        Select voice processing pattern with equal probability:
        - 20% chance for each of the 4 basic patterns
        - 20% chance for emotion reversal
        """
        import random
        
        # Equal probability selection (20% each)
        pattern_choice = random.choice([
            'fast_high', 'slow_low', 'pitch_up', 'tempo_up', 'emotion_reverse'
        ])
        
        if pattern_choice == 'emotion_reverse':
            return get_voice_processing_config_for_emotion(emotion_id)
        else:
            pattern_enum = VoiceProcessingPattern(pattern_choice)
            return VOICE_PROCESSING_PATTERNS[pattern_enum]
    
    def process_audio(self, audio_data: bytes, config: VoiceProcessingConfig) -> Optional[bytes]:
        """
        Process audio with specified pitch and tempo modifications using librosa.
        
        Args:
            audio_data: Input audio data as bytes
            config: Voice processing configuration
            
        Returns:
            Processed audio data as bytes, or None if processing fails
        """
        if not self.enabled:
            logger.warning("🎵 Voice processing not available - returning original audio")
            return audio_data
        
        try:
            logger.info(f"🎵 Starting audio processing: input size={len(audio_data)} bytes")
            logger.info(f"🎵 Config: {config.pattern.value} (pitch: {config.pitch}, tempo: {config.tempo})")
            
            # Try pydub conversion first (requires ffmpeg)
            try:
                import tempfile
                import os
                
                # Create temporary files
                with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_input:
                    temp_input.write(audio_data)
                    temp_input_path = temp_input.name
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_converted:
                    temp_converted_path = temp_converted.name
                    
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                    temp_output_path = temp_output.name
                
                try:
                    # Convert WebM to WAV using pydub
                    logger.info("🎵 Converting input audio to WAV format (requires ffmpeg)")
                    audio_segment = self.AudioSegment.from_file(temp_input_path)
                    audio_segment.export(temp_converted_path, format="wav")
                    
                    # Load converted WAV with librosa
                    logger.info("🎵 Loading audio with librosa")
                    y, sr = self.librosa.load(temp_converted_path, sr=None)
                    logger.info(f"🎵 Loaded audio: length={len(y)} samples, sr={sr}Hz")
                    
                    # Apply pitch and tempo modifications
                    logger.info(f"🎵 Applying effects: pitch={config.pitch}, tempo={config.tempo}")
                    processed_audio = self._apply_librosa_effects(y, sr, config.pitch, config.tempo)
                    logger.info(f"🎵 Effects applied: output length={len(processed_audio)} samples")
                    
                    # Save processed audio as WAV (fallback format)
                    logger.info("🎵 Saving processed audio as WAV")
                    self.sf.write(temp_output_path, processed_audio, sr)
                    
                    # Read processed audio back as bytes (WAV format)
                    with open(temp_output_path, 'rb') as f:
                        processed_bytes = f.read()
                    
                    logger.info(f"🎵 ✅ Audio processing complete: output size={len(processed_bytes)} bytes (WAV)")
                    return processed_bytes
                    
                finally:
                    # Clean up temporary files
                    for path in [temp_input_path, temp_converted_path, temp_output_path]:
                        try:
                            os.unlink(path)
                        except:
                            pass
            
            except Exception as format_error:
                logger.warning(f"🎵 ⚠️  Audio format conversion failed (likely missing ffmpeg): {format_error}")
                logger.info("🎵 🔄 Falling back to raw audio processing...")
                
                # Fallback: Try to process as raw audio data
                try:
                    # Assume input is raw PCM data and try to process it directly
                    import numpy as np
                    
                    # Convert bytes to numpy array (assuming 16-bit PCM)
                    audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                    # Normalize to [-1, 1] range
                    audio_normalized = audio_array / 32768.0
                    
                    # Use default sample rate for processing
                    sr = 22050
                    logger.info(f"🎵 Processing raw audio: {len(audio_normalized)} samples at {sr}Hz")
                    
                    # Apply effects
                    processed_audio = self._apply_librosa_effects(audio_normalized, sr, config.pitch, config.tempo)
                    
                    # Convert back to 16-bit PCM
                    processed_int16 = (processed_audio * 32767).astype(np.int16)
                    processed_bytes = processed_int16.tobytes()
                    
                    logger.info(f"🎵 ✅ Raw audio processing complete: output size={len(processed_bytes)} bytes")
                    return processed_bytes
                    
                except Exception as raw_error:
                    logger.error(f"🎵 ❌ Raw audio processing also failed: {raw_error}")
                    # Return original audio as last resort
                    return audio_data
            
        except Exception as e:
            logger.error(f"🎵 ❌ Voice processing failed completely: {e}", exc_info=True)
            # Return original audio on error
            return audio_data
    
    def _apply_librosa_effects(self, y: np.ndarray, sr: int, pitch: float, tempo: float) -> np.ndarray:
        """
        Apply pitch and tempo modifications using librosa.
        
        Args:
            y: Input audio as numpy array
            sr: Sample rate in Hz
            pitch: Pitch shift in semitones (-12 to +12)
            tempo: Tempo multiplier (0.5 to 2.0)
            
        Returns:
            Processed audio as numpy array
        """
        try:
            processed_audio = y.copy()
            
            # Apply pitch shifting if needed
            if abs(pitch) > 0.1:  # Only apply if pitch change is significant
                processed_audio = self.librosa.effects.pitch_shift(
                    processed_audio, 
                    sr=sr, 
                    n_steps=pitch,
                    bins_per_octave=12
                )
                logger.debug(f"Applied pitch shift: {pitch} semitones")
            
            # Apply tempo change if needed
            if abs(tempo - 1.0) > 0.05:  # Only apply if tempo change is significant
                processed_audio = self.librosa.effects.time_stretch(
                    processed_audio, 
                    rate=tempo
                )
                logger.debug(f"Applied tempo change: {tempo}x")
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Librosa audio processing failed: {e}")
            # Return original audio on error
            return y
    
    def get_processing_info(self, emotion_id: str) -> str:
        """Get description of what processing will be applied"""
        config = self.select_processing_pattern(emotion_id)
        return f"{config.description} (pitch: {config.pitch:+.1f}, tempo: {config.tempo:.1f}x)"

# Global instance
voice_processing_service = VoiceProcessingService()