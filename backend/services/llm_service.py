from openai import AsyncOpenAI
from typing import List, Tuple
import random
from config import settings
# Emotion mappings are now handled directly in this service

class LLMService:
    def __init__(self):
        self.client = None
        # Fallback phrases for when LLM is unavailable
        self.fallback_phrases = [
            "はぁ…",
            "うそでしょ…",
            "なんで…",
            "まじか",
            "やばい！",
            "えっ！？",
            "なんでよ！",
            "あーあ…",
            "なるほどね",
            "ふーん"
        ]
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available"""
        try:
            print(f"Starting OpenAI client initialization...")
            print(f"API key present: {bool(settings.OPENAI_API_KEY)}")
            
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
                print(f"Creating AsyncOpenAI client...")
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                print(f"OpenAI client initialized successfully")
            else:
                print("No OpenAI API key found, using fallback phrases only")
                self.client = None
        except Exception as e:
            print(f"Exception during OpenAI client initialization: {e}")
            import traceback
            traceback.print_exc()
            self.client = None
    
    def set_api_key(self, api_key: str):
        """Dynamically set the OpenAI API key"""
        settings.OPENAI_API_KEY = api_key
        self.client = None  # Clear existing client
        self._initialize_client()

    
    async def generate_phrase_with_emotion(self, mode: str = "basic") -> Tuple[str, str]:
        """Generate a phrase and select an emotion from available pool"""
        try:
            # Use the full emotion pool from emotion models for more variety
            from models.emotion import get_emotions_for_mode
            emotions_dict = get_emotions_for_mode(mode)
            
            # Convert to list for random selection
            available_emotions = []
            for emotion_info in emotions_dict.values():
                available_emotions.append({
                    'id': emotion_info.id,
                    'name_ja': emotion_info.name_ja,
                    'name_en': emotion_info.name_en
                })
            
            # Select random emotion from the full pool
            selected_emotion = random.choice(available_emotions)
            
            emotion_id = selected_emotion['id']
            
            # Generate phrase with LLM
            if self.client:
                try:
                    phrase = await self._generate_phrase_with_openai()
                except Exception as openai_error:
                    print(f"OpenAI API error in generate_phrase_with_emotion: {openai_error}")
                    phrase = random.choice(self.fallback_phrases)
            else:
                phrase = random.choice(self.fallback_phrases)
            
            return phrase, emotion_id
            
        except Exception as e:
            print(f"Error generating phrase: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to basic emotions
            phrase = random.choice(self.fallback_phrases)
            fallback_emotions = ['joy', 'anger', 'sadness', 'surprise', 'fear', 'disgust', 'trust', 'anticipation']
            emotion_id = random.choice(fallback_emotions)
            return phrase, emotion_id
    
    async def _generate_phrase_with_openai(self) -> str:
        """Generate phrase using OpenAI API"""
        try:
            if not self.client:
                print("OpenAI client not initialized")
                return random.choice(self.fallback_phrases)
            
            prompt = """
あなたは日本語の台詞生成AIです。同じ言葉でも感情や状況によって意味が異なる自然な日常会話の台詞を1つ生成してください。

要件:
- 日常的なシチュエーションでの台詞
- 同じ言葉でも感情や状況によって意味が異なる台詞
- 3-15文字程度
- 短い一言で日常的に使われるものでお願いします。
- 敬語・タメ口どちらでも可

台詞のみを出力してください:
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは日本語の台詞生成の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8,
                timeout=10.0  # 10 second timeout
            )
            
            if not response or not response.choices:
                print("No response from OpenAI API")
                return random.choice(self.fallback_phrases)
            
            phrase = response.choices[0].message.content
            if not phrase:
                print("Empty content from OpenAI API")
                return random.choice(self.fallback_phrases)
                
            phrase = phrase.strip()
            
            # Validate phrase length
            if len(phrase) > 50 or len(phrase) < 2:
                print(f"Invalid phrase length: {len(phrase)}")
                return random.choice(self.fallback_phrases)
            
            return phrase
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            import traceback
            traceback.print_exc()
            return random.choice(self.fallback_phrases)
    
    async def generate_batch_phrases(self, count: int = 5, mode: str = "basic") -> List[Tuple[str, str]]:
        """Generate multiple phrases with emotions"""
        phrases = []
        for _ in range(count):
            phrase, emotion = await self.generate_phrase_with_emotion(mode)
            phrases.append((phrase, emotion))
        return phrases

# Global instance
llm_service = None

def get_llm_service():
    """Get or create the global LLM service instance"""
    global llm_service
    if llm_service is None:
        print("Creating LLM service instance...")
        llm_service = LLMService()
        print("LLM service instance created successfully")
    return llm_service

# Initialize immediately to avoid any proxy issues
llm_service = get_llm_service()