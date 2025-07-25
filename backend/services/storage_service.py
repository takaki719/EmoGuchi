"""
ハイブリッドストレージサービス
開発環境: ローカルファイル
本番環境: S3
"""

import os
import logging
import uuid
from typing import Optional, Tuple
from datetime import datetime
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

class AudioStorageService:
    """音声ファイルのストレージ管理（ローカル/S3ハイブリッド）"""
    
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.local_dir = Path(settings.LOCAL_AUDIO_DIR)
        
        # ローカルストレージの初期化
        if self.storage_type == "local":
            self._init_local_storage()
        else:
            self._init_s3_storage()
    
    def _init_local_storage(self):
        """ローカルストレージディレクトリの作成"""
        try:
            self.local_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 ローカルストレージ初期化完了: {self.local_dir}")
        except Exception as e:
            logger.error(f"❌ ローカルストレージ初期化失敗: {e}")
            raise
    
    def _init_s3_storage(self):
        """S3クライアントの初期化"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # R2対応のS3互換クライアント設定
            client_config = {
                'region_name': settings.S3_REGION,
                'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
                'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY
            }
            
            # R2エンドポイントが設定されている場合
            if settings.R2_ENDPOINT_URL:
                client_config['endpoint_url'] = settings.R2_ENDPOINT_URL
            
            self.s3_client = boto3.client('s3', **client_config)
            
            # バケット存在確認
            try:
                self.s3_client.head_bucket(Bucket=settings.S3_BUCKET)
                logger.info(f"☁️ S3ストレージ初期化完了: {settings.S3_BUCKET}")
            except ClientError:
                logger.warning(f"⚠️ S3バケットが見つかりません: {settings.S3_BUCKET}")
                
        except ImportError:
            logger.error("❌ boto3がインストールされていません。pip install boto3")
            raise
        except Exception as e:
            logger.error(f"❌ S3ストレージ初期化失敗: {e}")
            raise
    
    def save_audio(self, audio_data: bytes, session_id: str, round_id: str = None) -> str:
        """
        音声データを永続化
        
        Args:
            audio_data: 音声バイナリデータ
            session_id: セッションID
            round_id: ラウンドID（オプション）
        
        Returns:
            アクセス可能なURL
        """
        try:
            # ファイル名の生成
            if round_id:
                filename = f"{session_id}_{round_id}_{uuid.uuid4().hex[:8]}.wav"
            else:
                filename = f"{session_id}_{uuid.uuid4().hex[:8]}.wav"
            
            if self.storage_type == "local":
                return self._save_local(audio_data, filename, session_id)
            else:
                return self._save_s3(audio_data, filename, session_id)
                
        except Exception as e:
            logger.error(f"❌ 音声保存エラー: {e}")
            raise
    
    def _save_local(self, audio_data: bytes, filename: str, session_id: str) -> str:
        """ローカルファイルとして保存"""
        try:
            # セッション別ディレクトリ作成
            session_dir = self.local_dir / session_id
            session_dir.mkdir(exist_ok=True)
            
            # ファイル保存
            file_path = session_dir / filename
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            # 相対URLを返す
            relative_path = f"/uploads/audio/{session_id}/{filename}"
            logger.info(f"💾 ローカル保存完了: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"❌ ローカル保存エラー: {e}")
            raise
    
    def _save_s3(self, audio_data: bytes, filename: str, session_id: str) -> str:
        """S3に保存"""
        try:
            # S3キー（パス）の生成
            s3_key = f"{session_id}/{filename}"
            
            # S3にアップロード
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=s3_key,
                Body=audio_data,
                ContentType='audio/wav'
            )
            
            # 公開URLを生成
            if settings.R2_ENDPOINT_URL:
                # R2のURLフォーマット（実際のエンドポイントから抽出）
                # settings.R2_ENDPOINT_URL = "https://{account-id}.r2.cloudflarestorage.com"
                base_url = settings.R2_ENDPOINT_URL.rstrip('/')
                s3_url = f"{base_url}/{settings.S3_BUCKET}/{s3_key}"
            else:
                # 通常のS3 URLフォーマット
                s3_url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"
            
            logger.info(f"☁️ ストレージ保存完了: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"❌ S3保存エラー: {e}")
            raise
    
    def get_audio_path(self, audio_url: str) -> str:
        """
        音声URLから実際のファイルパスを取得
        AI推論で使用するため
        """
        try:
            if self.storage_type == "local":
                # ローカルの場合: /uploads/audio/session/file.wav → ./uploads/audio/session/file.wav
                if audio_url.startswith('/uploads/'):
                    return f".{audio_url}"
                return audio_url
            else:
                # S3の場合: 一時ダウンロードが必要
                return self._download_from_s3(audio_url)
                
        except Exception as e:
            logger.error(f"❌ 音声パス取得エラー: {e}")
            raise
    
    def _download_from_s3(self, s3_url: str) -> str:
        """S3/R2から一時ファイルにダウンロード"""
        try:
            import tempfile
            
            # URLからS3キーを抽出（R2とS3の両方に対応）
            s3_key = None
            
            if settings.R2_ENDPOINT_URL and settings.R2_ENDPOINT_URL.replace('https://', '') in s3_url:
                # R2のURL形式: https://{endpoint}/{bucket}/{key}
                base_url = settings.R2_ENDPOINT_URL.rstrip('/')
                parts = s3_url.split(f"{base_url}/{settings.S3_BUCKET}/")
                if len(parts) > 1:
                    s3_key = parts[1]
            else:
                # 通常のS3 URL形式: https://{bucket}.s3.{region}.amazonaws.com/{key}
                parts = s3_url.split(f"{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/")
                if len(parts) > 1:
                    s3_key = parts[1]
            
            if not s3_key:
                raise ValueError(f"URLからS3キーを抽出できませんでした: {s3_url}")
            
            logger.info(f"📥 S3/R2からダウンロード開始: {s3_key}")
            
            # 一時ファイルにダウンロード
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                self.s3_client.download_fileobj(
                    settings.S3_BUCKET,
                    s3_key,
                    tmp_file
                )
                logger.info(f"✅ 一時ファイル作成完了: {tmp_file.name}")
                return tmp_file.name
                
        except Exception as e:
            logger.error(f"❌ S3ダウンロードエラー: {e}")
            raise
    
    def download_file(self, s3_key: str, local_path: str):
        """S3/R2から指定されたキーのファイルをローカルパスにダウンロード"""
        try:
            if self.storage_type == "local":
                raise ValueError("ローカルストレージモードではS3ダウンロードは使用できません")
            
            logger.info(f"📥 S3/R2からダウンロード開始: {s3_key} -> {local_path}")
            logger.info(f"🔧 ダウンロード詳細: バケット={settings.S3_BUCKET}, キー={s3_key}")
            logger.info(f"🔧 エンドポイント: {getattr(settings, 'R2_ENDPOINT_URL', 'NOT_SET')}")
            logger.info(f"🔧 ストレージタイプ: {self.storage_type}")
            
            # ディレクトリがない場合は作成
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # S3からダウンロード
            self.s3_client.download_file(
                settings.S3_BUCKET,
                s3_key,
                local_path
            )
            
            logger.info(f"✅ ダウンロード完了: {local_path}")
            
        except Exception as e:
            logger.error(f"❌ ファイルダウンロードエラー: {e}")
            raise
    
    def cleanup_temp_files(self, temp_paths: list):
        """一時ファイルの削除"""
        for path in temp_paths:
            try:
                if os.path.exists(path) and "/tmp/" in path:
                    os.unlink(path)
                    logger.debug(f"🗑️ 一時ファイル削除: {path}")
            except Exception as e:
                logger.warning(f"⚠️ 一時ファイル削除失敗: {e}")

# エイリアス（後方互換性のため）
StorageService = AudioStorageService

# グローバルインスタンス
_storage_service = None

def get_storage_service() -> AudioStorageService:
    """ストレージサービスのシングルトンインスタンスを取得"""
    global _storage_service
    if _storage_service is None:
        _storage_service = AudioStorageService()
    return _storage_service