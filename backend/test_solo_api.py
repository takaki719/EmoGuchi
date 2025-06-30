#!/usr/bin/env python3
"""
ソロ感情演技モードAPIのテストスクリプト
"""

import requests
import tempfile
import wave
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_audio(duration=2.0, sample_rate=16000, frequency=440):
    """テスト用の音声ファイルを作成"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
    
    # 16bit PCMに変換
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    # WAVファイルとして保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # モノラル
            wav_file.setsampwidth(2)  # 16bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return temp_file.name

def test_health_endpoint():
    """ヘルスチェックエンドポイントのテスト"""
    logger.info("🏥 ヘルスチェックAPIをテスト中...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/solo/health")
        logger.info(f"ステータスコード: {response.status_code}")
        logger.info(f"レスポンス: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return False

def test_predict_endpoint():
    """推論エンドポイントのテスト"""
    logger.info("🤖 推論APIをテスト中...")
    
    try:
        # テスト音声ファイル作成
        test_audio_path = create_test_audio(duration=3.0, frequency=440)
        logger.info(f"テスト音声ファイル作成: {test_audio_path}")
        
        # APIリクエスト
        with open(test_audio_path, 'rb') as audio_file:
            files = {'file': ('test.wav', audio_file, 'audio/wav')}
            data = {'target_emotion': 1}  # 喜び
            
            response = requests.post(
                "http://localhost:8000/predict",
                files=files,
                data=data
            )
        
        logger.info(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("🎉 推論成功!")
            logger.info(f"推論された感情: {result['emotion']}")
            logger.info(f"スコア: {result['score']}点")
            logger.info(f"正解: {result['is_correct']}")
            logger.info(f"メッセージ: {result['message']}")
            return True
        else:
            logger.error(f"推論失敗: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"推論テストエラー: {e}")
        return False
    finally:
        # テスト音声ファイル削除
        try:
            import os
            os.unlink(test_audio_path)
        except:
            pass

def main():
    """メインテスト実行"""
    logger.info("🧪 ソロ感情演技モードAPIテスト開始")
    
    # 1. ヘルスチェックテスト
    health_ok = test_health_endpoint()
    
    if not health_ok:
        logger.error("❌ ヘルスチェックに失敗しました。サーバーが起動していることを確認してください。")
        return
    
    # 2. 推論エンドポイントテスト
    predict_ok = test_predict_endpoint()
    
    if predict_ok:
        logger.info("🎉 全てのテストが成功しました！")
    else:
        logger.error("❌ 推論テストに失敗しました。")

if __name__ == "__main__":
    main()