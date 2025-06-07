from openai import AsyncOpenAI
from typing import List, Tuple
import random
from config import settings
# Emotion mappings are now handled directly in this service

class LLMService:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Fallback phrases for when LLM is unavailable
        self.fallback_phrases = [
            "今日はとても良い天気ですね。",
            "この料理は本当に美味しいです。",
            "明日の会議の準備はできていますか？",
            "最近読んだ本がとても面白かったです。",
            "週末は家族と過ごす予定です。",
            "新しいプロジェクトが始まりました。",
            "電車が遅れているようですね。",
            "コーヒーを飲みに行きませんか？",
            "今度の休暇の計画は立てましたか？",
            "この映画は感動的でした。"
        ]
    
    async def generate_phrase_with_emotion(self, mode: str = "basic", vote_type: str = "4choice") -> Tuple[str, str]:
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
            emotion_name = selected_emotion['name_ja']
            emotion_name_en = selected_emotion['name_en']
            
            # Generate phrase with LLM
            if self.client:
                phrase = await self._generate_phrase_with_openai(emotion_name, emotion_name_en)
            else:
                phrase = random.choice(self.fallback_phrases)
            
            return phrase, emotion_id
            
        except Exception as e:
            print(f"Error generating phrase: {e}")
            # Fallback to basic emotions
            phrase = random.choice(self.fallback_phrases)
            fallback_emotions = ['joy', 'anger', 'sadness', 'surprise', 'fear', 'disgust', 'trust', 'anticipation']
            emotion_id = random.choice(fallback_emotions)
            return phrase, emotion_id
    
    async def _generate_phrase_with_openai(self, emotion_ja: str, emotion_en: str) -> str:
        """Generate phrase using OpenAI API"""
        try:
            prompt = f"""
あなたは日本語の台詞生成AIです。指定された感情を表現する自然な日常会話の台詞を1つ生成してください。

感情: {emotion_ja} ({emotion_en})

要件:
- 日常的なシチュエーションでの台詞
- 5-15文字程度
- 自然で演技しやすい表現
- 感情が分かりやすい台詞
- 敬語・タメ口どちらでも可

台詞のみを出力してください:
"""
            
            if not self.client:
                return random.choice(self.fallback_phrases)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは日本語の台詞生成の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8,
                timeout=3.0  # 3 second timeout
            )
            
            phrase = response.choices[0].message.content.strip()
            
            # Validate phrase length
            if len(phrase) > 50 or len(phrase) < 5:
                return random.choice(self.fallback_phrases)
            
            return phrase
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return random.choice(self.fallback_phrases)
    
    async def generate_batch_phrases(self, count: int = 5, mode: str = "basic") -> List[Tuple[str, str]]:
        """Generate multiple phrases with emotions"""
        phrases = []
        for _ in range(count):
            phrase, emotion = await self.generate_phrase_with_emotion(mode)
            phrases.append((phrase, emotion))
        return phrases

# Global instance
llm_service = LLMService()