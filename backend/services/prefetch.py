import os
import asyncio
from typing import List

import openai

# Fallback phrases used when the OpenAI request fails or times out
FALLBACK_PHRASES = [
    "よろしくお願いします！",
    "さあ、始めましょう。",
    "今日はいい天気ですね。",
    "準備はできていますか？",
    "これが予備のセリフです。",
]

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")


async def prefetch_phrases(batch_size: int) -> List[str]:
    """Fetch phrases from OpenAI with timeout and fallback."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return FALLBACK_PHRASES[: batch_size]

    prompt = (
        f"次のゲーム用に短いセリフを{batch_size}個日本語で生成してください。"
        "箇条書きで出力してください。"
    )
    try:
        response = await asyncio.wait_for(
            openai.ChatCompletion.acreate(
                api_key=api_key,
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "あなたはセリフ生成ボットです。"},
                    {"role": "user", "content": prompt},
                ],
            ),
            timeout=3,
        )
        text = response.choices[0].message.content
        phrases = [line.lstrip("-• ").strip() for line in text.splitlines() if line.strip()]
        if len(phrases) >= batch_size:
            return phrases[:batch_size]
        return phrases or FALLBACK_PHRASES[: batch_size]
    except Exception:
        return FALLBACK_PHRASES[: batch_size]
