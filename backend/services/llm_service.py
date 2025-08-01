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

    
    async def generate_phrase_with_emotion(self, mode: str = "basic", vote_type: str = None) -> Tuple[str, str]:
        """Generate a phrase and select an emotion from available pool"""
        try:
            # Use the full emotion pool from emotion models for more variety
            from models.emotion import get_emotions_for_mode
            emotions_dict = get_emotions_for_mode(mode, vote_type)
            
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
            length_choice = random.choices(
            ["very_short","short", "mid", "long"], weights=[4,4, 1, 1], k=1
            )[0]
            prompt = f"""
            あなたは日本語の台詞生成AIです。
            以下の手順で**事前に一切公表せず**内部でランダム抽選を行ってください。
            
            1. 日常シチュエーションを1つ選ぶ  
               例: 朝の通勤電車 / コンビニで会計 / 友人とのLINE / 雨の日の帰宅 / ゲームのVC など10種以上を内部リスト化し、その中から無作為抽選
            
            2. 感情を1つ選ぶ  
               例: 喜び・怒り・悲しみ・驚き・焦り・困惑・照れ・感謝・不安・ワクワク などから無作為抽選
            
            3. “同じ言葉でも状況で意味が変わる”効果が出るよう、**二重の意味合い**をもつワードや語尾を活かす
            
            - 台詞長カテゴリ: **{length_choice}**
                - very_short → 2〜5文字
                - short → 5〜10文字
                - mid   → 15〜30文字
                - long  → 70〜120文字
            - 台詞のみ（かっこなし・説明文なし・改行なし）を出力し、説明禁止
            - 条件を満たさなければ再生成して最終的に条件を満たす台詞を返す
            セリフのみを出力してください
            """


            
            response = await self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "あなたは日本語の台詞生成の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=1.2,
                timeout=10.0,  # 10 second timeout
                frequency_penalty = 0.3,
                presence_penalty = 0.3,
                top_p = 0.9,
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
    
    async def generate_batch_phrases(self, count: int = 5, mode: str = "basic", vote_type: str = None) -> List[Tuple[str, str]]:
        """Generate multiple phrases with emotions"""
        phrases = []
        for _ in range(count):
            phrase, emotion = await self.generate_phrase_with_emotion(mode, vote_type)
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