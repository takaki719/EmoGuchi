"""
データベースサービス
SQLAlchemy async操作とコネクション管理
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_
from datetime import datetime

from config import settings
from models.database import Base, SoloSession, EmotionType, Recording, Score, Mode

logger = logging.getLogger(__name__)

class DatabaseService:
    """データベース操作サービス"""
    
    def __init__(self):
        self.engine = None
        self.session_maker = None
        self._initialized = False
    
    async def initialize(self):
        """データベース初期化"""
        if self._initialized:
            return
            
        try:
            database_url = settings.DATABASE_URL
            logger.info(f"📊 データベース接続中: {settings.DATABASE_TYPE}")
            
            # エンジン作成
            engine_kwargs = {
                "echo": False,  # SQLログを出力する場合はTrue
                "future": True,
                "pool_pre_ping": True,  # 接続確認
                "pool_recycle": 3600,   # 1時間でコネクション再利用
            }
            
            # PostgreSQL用の追加設定
            if settings.DATABASE_TYPE == "postgresql":
                engine_kwargs.update({
                    "pool_size": 10,        # コネクションプールサイズ
                    "max_overflow": 20,     # 最大オーバーフロー
                    "pool_timeout": 30,     # タイムアウト
                    "connect_args": {
                        "command_timeout": 60,
                        "server_settings": {
                            "jit": "off",  # JITを無効化（小さなクエリでのオーバーヘッド回避）
                            "timezone": "UTC",  # タイムゾーンをUTCに設定
                        }
                    }
                })
            
            self.engine = create_async_engine(database_url, **engine_kwargs)
            
            # セッションメーカー作成
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # テーブル作成
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # 初期データ投入
            await self._insert_initial_data()
            
            self._initialized = True
            logger.info("✅ データベース初期化完了")
            
        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """データベースセッション取得"""
        if not self._initialized:
            await self.initialize()
            
        async with self.session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def _insert_initial_data(self):
        """初期データ投入（感情タイプ等）"""
        async with self.session_maker() as session:
            try:
                # 感情タイプが既に存在するかチェック
                result = await session.execute(select(EmotionType))
                existing_emotions = result.scalars().first()
                
                if existing_emotions is None:
                    logger.info("🎭 初期感情データを投入中...")
                    
                    # 基本感情セット
                    basic_emotions = [
                        ("neutral", "中立", "neutral"),
                        ("joy", "喜び", "joy"),
                        ("anger", "怒り", "anger"),
                        ("sadness", "悲しみ", "sadness"),
                        ("surprise", "驚き", "surprise"),
                        ("fear", "恐れ", "fear"),
                        ("disgust", "嫌悪", "disgust"),
                        ("trust", "信頼", "trust"),
                        ("anticipation", "期待", "anticipation")
                    ]
                    
                    for emotion_id, name_ja, name_en in basic_emotions:
                        emotion = EmotionType(
                            id=emotion_id,
                            name_ja=name_ja,
                            name_en=name_en
                        )
                        session.add(emotion)
                    
                    # ゲームモード投入
                    modes = [
                        ("basic", "基本モード（8感情選択）"),
                        ("advanced", "上級モード（感情の輪）"),
                        ("solo", "ソロ練習モード")
                    ]
                    
                    for mode_name, description in modes:
                        mode = Mode(name=mode_name, description=description)
                        session.add(mode)
                    
                    await session.commit()
                    logger.info("✅ 初期データ投入完了")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ 初期データ投入エラー: {e}")
                raise
    
    async def save_solo_session(self, session_data: Dict[str, Any]) -> str:
        """ソロセッションデータ保存"""
        logger.info(f"🔍 Starting save_solo_session with data: {session_data}")
        async with self.session_maker() as session:
            try:
                # ソロセッション作成
                solo_session = SoloSession(
                    session_id=session_data["session_id"],
                    target_emotion_id=session_data["target_emotion_id"],
                    prompt_text=session_data["prompt_text"],
                    ai_predicted_emotion_id=session_data.get("ai_predicted_emotion_id"),
                    ai_confidence=session_data.get("ai_confidence"),
                    is_correct=session_data["is_correct"],
                    base_score=session_data["base_score"],
                    bonus_score=session_data.get("bonus_score", 0),
                    final_score=session_data["final_score"]
                )
                session.add(solo_session)
                await session.flush()  # IDを取得するため
                
                # 録音データ保存
                if "audio_url" in session_data:
                    recording = Recording(
                        solo_session_id=solo_session.id,
                        session_id=session_data["session_id"],
                        audio_url=session_data["audio_url"],
                        duration=session_data.get("duration")
                    )
                    session.add(recording)
                
                # スコア保存
                score = Score(
                    session_id=session_data["session_id"],
                    solo_session_id=solo_session.id,
                    points=session_data["final_score"],
                    score_type="solo"
                )
                session.add(score)
                
                await session.commit()
                
                logger.info(f"💾 ソロセッション保存完了: {solo_session.id}")
                return str(solo_session.id)
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ ソロセッション保存エラー: {e}")
                raise
    
    async def get_solo_stats(self, session_id: str) -> Dict[str, Any]:
        """ソロプレイ統計取得"""
        async with self.session_maker() as session:
            try:
                # 基本統計クエリ
                result = await session.execute(
                    select(
                        func.count(SoloSession.id).label("total_plays"),
                        func.sum(func.cast(SoloSession.is_correct, float)).label("correct_count"),
                        func.avg(SoloSession.final_score).label("avg_score"),
                        func.max(SoloSession.final_score).label("best_score")
                    ).where(SoloSession.session_id == session_id)
                )
                stats = result.first()
                
                # 感情別正答率
                emotion_stats = await session.execute(
                    select(
                        EmotionType.name_ja,
                        func.count(SoloSession.id).label("total"),
                        func.sum(func.cast(SoloSession.is_correct, float)).label("correct")
                    )
                    .join(SoloSession, SoloSession.target_emotion_id == EmotionType.id)
                    .where(SoloSession.session_id == session_id)
                    .group_by(EmotionType.id, EmotionType.name_ja)
                )
                
                emotion_breakdown = []
                for row in emotion_stats:
                    accuracy = (row.correct / row.total * 100) if row.total > 0 else 0
                    emotion_breakdown.append({
                        "emotion": row.name_ja,
                        "accuracy": round(accuracy, 1),
                        "total_plays": int(row.total)
                    })
                
                return {
                    "total_plays": int(stats.total_plays or 0),
                    "correct_count": int(stats.correct_count or 0),
                    "accuracy": round((stats.correct_count / stats.total_plays * 100) if stats.total_plays > 0 else 0, 1),
                    "average_score": round(float(stats.avg_score or 0), 1),
                    "best_score": int(stats.best_score or 0),
                    "emotion_breakdown": emotion_breakdown
                }
                
            except Exception as e:
                logger.error(f"❌ 統計取得エラー: {e}")
                return {
                    "total_plays": 0,
                    "correct_count": 0,
                    "accuracy": 0,
                    "average_score": 0,
                    "best_score": 0,
                    "emotion_breakdown": []
                }
    
    async def get_recent_solo_sessions(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """最近のソロセッション履歴取得"""
        async with self.session_maker() as session:
            try:
                result = await session.execute(
                    select(SoloSession)
                    .options(
                        selectinload(SoloSession.target_emotion),
                        selectinload(SoloSession.ai_predicted_emotion),
                        selectinload(SoloSession.recording)
                    )
                    .where(SoloSession.session_id == session_id)
                    .order_by(SoloSession.created_at.desc())
                    .limit(limit)
                )
                
                sessions = result.scalars().all()
                
                history = []
                for s in sessions:
                    history.append({
                        "id": str(s.id),
                        "target_emotion": s.target_emotion.name_ja,
                        "predicted_emotion": s.ai_predicted_emotion.name_ja if s.ai_predicted_emotion else None,
                        "is_correct": s.is_correct,
                        "final_score": s.final_score,
                        "confidence": s.ai_confidence,
                        "audio_url": s.recording.audio_url if s.recording else None,
                        "created_at": s.created_at.isoformat()
                    })
                
                return history
                
            except Exception as e:
                logger.error(f"❌ 履歴取得エラー: {e}")
                return []

# グローバルインスタンス
_db_service = None

async def get_database_service() -> DatabaseService:
    """データベースサービスのシングルトンインスタンス取得"""
    global _db_service
    if _db_service is None:
        logger.info("🔧 Initializing database service for the first time")
        _db_service = DatabaseService()
        await _db_service.initialize()
        logger.info("✅ Database service initialized successfully")
    return _db_service