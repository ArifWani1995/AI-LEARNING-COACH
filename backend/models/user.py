"""
User and Learning Profile Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Base


class User(Base):
    """User model for storing learner information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Learning preferences
    current_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    learning_speed = Column(String(20), default="medium")  # slow, medium, fast
    learning_goal = Column(Text, nullable=True)
    preferred_topics = Column(JSON, default=list)
    
    # Relationships
    progress = relationship("LearningProgress", back_populates="user")
    quiz_results = relationship("QuizResult", back_populates="user")
    study_sessions = relationship("StudySession", back_populates="user")
    
    
class LearningProgress(Base):
    """Track learning progress for each topic"""
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(String(50), index=True)
    topic_name = Column(String(200))
    
    # Progress metrics
    mastery_level = Column(Float, default=0.0)  # 0-100%
    time_spent_minutes = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)
    
    # Spaced repetition data
    next_review_date = Column(DateTime, nullable=True)
    ease_factor = Column(Float, default=2.5)  # SM-2 algorithm factor
    interval_days = Column(Integer, default=1)
    repetition_count = Column(Integer, default=0)
    
    # Weakness detection
    weakness_score = Column(Float, default=0.0)  # 0-1, higher = weaker
    last_quiz_score = Column(Float, nullable=True)
    
    last_studied = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="progress")


class QuizResult(Base):
    """Store quiz results for analytics"""
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(String(50), index=True)
    quiz_type = Column(String(50))  # diagnostic, practice, review
    
    score = Column(Float)
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    time_taken_seconds = Column(Integer)
    
    # Detailed results
    question_results = Column(JSON, default=list)  # [{question_id, correct, time}]
    weak_concepts = Column(JSON, default=list)  # Concepts the user struggled with
    
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="quiz_results")


class StudySession(Base):
    """Track study sessions for analytics"""
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(String(50))
    
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    
    activities = Column(JSON, default=list)  # [{type, timestamp, details}]
    notes = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="study_sessions")


class Topic(Base):
    """Knowledge graph topics"""
    __tablename__ = "topics"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200))
    description = Column(Text)
    category = Column(String(100))
    difficulty_level = Column(Integer, default=1)  # 1-5
    
    # Knowledge graph relationships
    prerequisites = Column(JSON, default=list)  # [topic_ids]
    related_topics = Column(JSON, default=list)
    
    # Content
    content = Column(Text)
    resources = Column(JSON, default=list)  # [{type, url, title}]
    
    # Quiz questions pool
    questions = Column(JSON, default=list)


class StudyPlan(Base):
    """Personalized study plans"""
    __tablename__ = "study_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    plan_type = Column(String(20))  # short_term, long_term
    title = Column(String(200))
    description = Column(Text)
    
    # Plan details
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    topics = Column(JSON)  # [{topic_id, order, estimated_hours, deadline}]
    milestones = Column(JSON, default=list)  # [{title, date, completed}]
    
    # Progress
    progress_percentage = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
