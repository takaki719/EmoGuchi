"""
SQLAlchemyデータベースモデル定義
DB.mdの設計に基づいた実装
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Mode(Base):
    """ゲームモード（basic/advanced等）"""
    __tablename__ = "modes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)  # "basic", "advanced"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    chat_sessions = relationship("ChatSession", back_populates="mode")

class EmotionType(Base):
    """感情タイプ（喜び、怒り等）"""
    __tablename__ = "emotion_types"
    
    id = Column(String(50), primary_key=True)  # "joy", "anger", etc.
    name_ja = Column(String(50), nullable=False)  # "喜び"
    name_en = Column(String(50), nullable=False)  # "joy"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    rounds = relationship("Round", back_populates="emotion")
    emotion_votes = relationship("EmotionVote", back_populates="selected_emotion")
    solo_sessions = relationship("SoloSession", foreign_keys="[SoloSession.target_emotion_id]", back_populates="target_emotion")

class ChatSession(Base):
    """1プレイ全体をまとめる単位（マルチプレイ）"""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_code = Column(String(20), nullable=False)
    mode_id = Column(String(36), ForeignKey("modes.id"), nullable=False)
    max_players = Column(Integer, default=8)
    status = Column(Enum('waiting', 'playing', 'finished', name='chat_session_status'), default="waiting")
    current_speaker_index = Column(Integer, default=0)  # スピーカーローテーション用インデックス
    host_token = Column(String(36), nullable=True)  # ホスト認証トークン
    # Room configuration fields
    vote_type = Column(String(20), default="4choice")  # 4choice, 8choice, wheel
    speaker_order = Column(String(20), default="sequential")  # sequential, random
    max_rounds = Column(Integer, default=1)
    hard_mode = Column(Boolean, default=False)
    vote_timeout = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    mode = relationship("Mode", back_populates="chat_sessions")
    rounds = relationship("Round", back_populates="chat_session")
    participants = relationship("RoomParticipant", back_populates="chat_session")

class RoomParticipant(Base):
    """ルーム参加者管理"""
    __tablename__ = "room_participants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    session_id = Column(String(36), nullable=False)  # localStorage UUID
    player_name = Column(String(100), nullable=False)
    is_host = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    chat_session = relationship("ChatSession", back_populates="participants")

class Round(Base):
    """ラウンド（1セリフ・1スピーカー単位）"""
    __tablename__ = "rounds"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    speaker_session_id = Column(String(36), nullable=False)  # 発話者のセッションID
    prompt_text = Column(Text, nullable=False)  # GPT生成セリフ
    emotion_id = Column(String(50), ForeignKey("emotion_types.id"), nullable=False)  # 正解感情
    round_number = Column(Integer, nullable=False)
    eligible_voters = Column(Text, nullable=True)  # JSON string of eligible voter IDs
    voting_started_at = Column(DateTime(timezone=True), nullable=True)  # 投票開始時刻
    vote_timeout_seconds = Column(Integer, default=30)  # 投票制限時間
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    chat_session = relationship("ChatSession", back_populates="rounds")
    emotion = relationship("EmotionType", back_populates="rounds")
    recordings = relationship("Recording", back_populates="round")
    emotion_votes = relationship("EmotionVote", back_populates="round")
    scores = relationship("Score", back_populates="round")

class Recording(Base):
    """録音された音声"""
    __tablename__ = "recordings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    round_id = Column(String(36), ForeignKey("rounds.id"), nullable=True)  # マルチプレイ用
    solo_session_id = Column(String(36), ForeignKey("solo_sessions.id"), nullable=True)  # ソロ用
    session_id = Column(String(100), nullable=False)  # 録音者ID
    audio_url = Column(Text, nullable=False)  # 音声ファイルURL
    duration = Column(Float, nullable=True)  # 音声長（秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    round = relationship("Round", back_populates="recordings")
    solo_session = relationship("SoloSession", back_populates="recording")

class EmotionVote(Base):
    """感情当て投票（マルチプレイ）"""
    __tablename__ = "emotion_votes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    round_id = Column(String(36), ForeignKey("rounds.id"), nullable=False)
    voter_session_id = Column(String(36), nullable=False)  # 投票者ID
    selected_emotion_id = Column(String(50), ForeignKey("emotion_types.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    round = relationship("Round", back_populates="emotion_votes")
    selected_emotion = relationship("EmotionType", back_populates="emotion_votes")

class Score(Base):
    """得点履歴"""
    __tablename__ = "scores"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(100), nullable=False)
    round_id = Column(String(36), ForeignKey("rounds.id"), nullable=True)
    solo_session_id = Column(String(36), ForeignKey("solo_sessions.id"), nullable=True)
    points = Column(Integer, nullable=False)
    score_type = Column(Enum('listener', 'speaker', 'solo', name='score_type_enum'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    round = relationship("Round", back_populates="scores")
    solo_session = relationship("SoloSession", back_populates="score")

class SoloSession(Base):
    """ソロプレイセッション"""
    __tablename__ = "solo_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False)  # localStorage UUID
    target_emotion_id = Column(String(50), ForeignKey("emotion_types.id"), nullable=False)
    prompt_text = Column(Text, nullable=False)  # 演技用セリフ
    ai_predicted_emotion_id = Column(String(50), ForeignKey("emotion_types.id"), nullable=True)
    ai_confidence = Column(Float, nullable=True)  # AI予測信頼度
    is_correct = Column(Boolean, nullable=False)
    base_score = Column(Integer, nullable=False)  # ベーススコア
    bonus_score = Column(Integer, default=0)  # ボーナススコア
    final_score = Column(Integer, nullable=False)  # 最終スコア
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    target_emotion = relationship("EmotionType", back_populates="solo_sessions", foreign_keys=[target_emotion_id])
    ai_predicted_emotion = relationship("EmotionType", foreign_keys=[ai_predicted_emotion_id])
    recording = relationship("Recording", back_populates="solo_session", uselist=False)
    score = relationship("Score", back_populates="solo_session", uselist=False)