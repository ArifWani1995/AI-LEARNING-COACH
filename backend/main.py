"""
AI Learning Coach - FastAPI Backend
Main application entry point with all API endpoints
"""
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import get_db, init_db, engine, Base
from models.user import User, LearningProgress, QuizResult as QuizResultModel, StudySession, StudyPlan, Topic
from services.knowledge_graph import KnowledgeGraph
from services.spaced_repetition import SpacedRepetitionService, ReviewItem, convert_score_to_quality
from services.quiz_generator import QuizGenerator, QuizConfig
from services.weakness_detector import WeaknessDetector, PerformanceRecord
from services.pdf_generator import PDFReportGenerator

# Initialize FastAPI app
app = FastAPI(
    title="AI Learning Coach",
    description="Personal AI-powered learning assistant with adaptive learning paths",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
knowledge_graph = KnowledgeGraph(os.path.join(DATA_DIR, "knowledge_base.json"))
spaced_rep = SpacedRepetitionService()
quiz_gen = QuizGenerator()
weakness_detector = WeaknessDetector()
pdf_gen = PDFReportGenerator()

# Load questions into quiz generator
with open(os.path.join(DATA_DIR, "knowledge_base.json"), 'r') as f:
    kb_data = json.load(f)
    for topic in kb_data.get('topics', []):
        quiz_gen.add_questions(topic['id'], topic.get('questions', []))

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: str
    current_level: str = "beginner"
    learning_speed: str = "medium"
    learning_goal: Optional[str] = None

class UserUpdate(BaseModel):
    current_level: Optional[str] = None
    learning_speed: Optional[str] = None
    learning_goal: Optional[str] = None
    preferred_topics: Optional[List[str]] = None

class QuizSubmission(BaseModel):
    quiz_id: str
    answers: List[Dict[str, Any]]

class DiagnosticAnswer(BaseModel):
    question_id: str
    answer: str

class ProgressUpdate(BaseModel):
    topic_id: str
    mastery_level: float
    time_spent_minutes: int

# Startup event
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

# ==================== USER ENDPOINTS ====================

@app.post("/api/users", response_model=Dict)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username, email=user.email,
        current_level=user.current_level, learning_speed=user.learning_speed,
        learning_goal=user.learning_goal
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "username": db_user.username, "message": "User created successfully"}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "email": user.email,
            "current_level": user.current_level, "learning_speed": user.learning_speed,
            "learning_goal": user.learning_goal, "preferred_topics": user.preferred_topics or []}

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    return {"message": "User updated successfully"}

# ==================== TOPICS ENDPOINTS ====================

@app.get("/api/topics")
async def get_all_topics():
    return {"topics": knowledge_graph.get_all_topics()}

@app.get("/api/topics/{topic_id}")
async def get_topic(topic_id: str):
    topic = knowledge_graph.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic

@app.get("/api/topics/{topic_id}/learning-path")
async def get_learning_path(topic_id: str, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    completed = []
    if user_id:
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id, LearningProgress.mastery_level >= 70
        ).all()
        completed = [p.topic_id for p in progress]
    path = knowledge_graph.get_learning_path(topic_id, completed)
    return {"learning_path": path, "total_topics": len(path)}

@app.get("/api/users/{user_id}/recommendations")
async def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).all()
    completed = [p.topic_id for p in progress if p.mastery_level >= 70]
    weak = [p.topic_id for p in progress if p.weakness_score and p.weakness_score > 0.4]
    recommendations = knowledge_graph.recommend_next_topics(completed, weak)
    return {"recommendations": recommendations}

# ==================== QUIZ ENDPOINTS ====================

@app.post("/api/quiz/diagnostic")
async def generate_diagnostic_quiz(user_id: int, topic_ids: List[str], db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    level = user.current_level if user else "beginner"
    quiz = quiz_gen.generate_diagnostic_quiz(topic_ids, level)
    quiz['created_at'] = datetime.now().isoformat()
    return quiz

@app.post("/api/quiz/practice")
async def generate_practice_quiz(user_id: int, topic_ids: List[str], num_questions: int = 10,
                                  focus_weaknesses: bool = False, db: Session = Depends(get_db)):
    weak_concepts = []
    if focus_weaknesses:
        analysis = weakness_detector.analyze_weaknesses(user_id)
        weak_concepts = [c['concept'] for c in analysis.weak_concepts]
    config = QuizConfig(topic_ids=topic_ids, num_questions=num_questions,
                        focus_on_weaknesses=focus_weaknesses, weak_concepts=weak_concepts)
    quiz = quiz_gen.generate_quiz(config)
    quiz['created_at'] = datetime.now().isoformat()
    return quiz

@app.post("/api/quiz/submit")
async def submit_quiz(user_id: int, submission: QuizSubmission, db: Session = Depends(get_db)):
    result = quiz_gen.grade_quiz(submission.quiz_id, submission.answers)
    # Save to DB
    quiz_result = QuizResultModel(
        user_id=user_id, topic_id=submission.quiz_id, quiz_type="practice",
        score=result.score, total_questions=result.total_questions,
        correct_answers=result.correct_count, time_taken_seconds=result.time_taken_seconds,
        question_results=result.question_results, weak_concepts=result.weak_concepts
    )
    db.add(quiz_result)
    db.commit()
    # Update spaced repetition
    for q_result in result.question_results:
        topic_id = q_result.get('topic_id', submission.quiz_id)
        quality = convert_score_to_quality(100 if q_result['correct'] else 0)
        record = PerformanceRecord(
            topic_id=topic_id, concept=q_result.get('concept', 'general'),
            correct=q_result['correct'], timestamp=datetime.now(),
            difficulty=q_result.get('difficulty', 'medium'), time_taken_seconds=q_result.get('time_seconds', 0)
        )
        weakness_detector.add_performance_record(user_id, record)
    return {"score": result.score, "correct": result.correct_count, "total": result.total_questions,
            "weak_concepts": result.weak_concepts, "recommendations": result.recommendations,
            "question_results": result.question_results}

# ==================== PROGRESS ENDPOINTS ====================

@app.get("/api/users/{user_id}/progress")
async def get_user_progress(user_id: int, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).all()
    return {"progress": [{"topic_id": p.topic_id, "topic_name": p.topic_name, "mastery_level": p.mastery_level,
                          "time_spent_minutes": p.time_spent_minutes, "next_review": p.next_review_date.isoformat() if p.next_review_date else None,
                          "weakness_score": p.weakness_score} for p in progress]}

@app.post("/api/users/{user_id}/progress")
async def update_progress(user_id: int, update: ProgressUpdate, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id, LearningProgress.topic_id == update.topic_id
    ).first()
    topic = knowledge_graph.get_topic(update.topic_id)
    if not progress:
        progress = LearningProgress(user_id=user_id, topic_id=update.topic_id,
                                     topic_name=topic['name'] if topic else update.topic_id)
        db.add(progress)
    progress.mastery_level = update.mastery_level
    progress.time_spent_minutes += update.time_spent_minutes
    progress.last_studied = datetime.now()
    # Update spaced repetition
    quality = convert_score_to_quality(update.mastery_level)
    review_item = ReviewItem(topic_id=update.topic_id, topic_name=progress.topic_name,
                              ease_factor=progress.ease_factor, interval_days=progress.interval_days,
                              repetition_count=progress.repetition_count)
    updated = spaced_rep.calculate_next_review(review_item, quality)
    progress.ease_factor = updated.ease_factor
    progress.interval_days = updated.interval_days
    progress.repetition_count = updated.repetition_count
    progress.next_review_date = updated.next_review_date
    db.commit()
    return {"message": "Progress updated", "next_review": updated.next_review_date.isoformat() if updated.next_review_date else None}

@app.get("/api/users/{user_id}/review-schedule")
async def get_review_schedule(user_id: int, days: int = 7, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).all()
    items = [ReviewItem(topic_id=p.topic_id, topic_name=p.topic_name, ease_factor=p.ease_factor,
                        interval_days=p.interval_days, repetition_count=p.repetition_count,
                        next_review_date=p.next_review_date) for p in progress]
    schedule = spaced_rep.get_study_schedule(items, days)
    return {"schedule": {k: [{"topic_id": i.topic_id, "topic_name": i.topic_name} for i in v] for k, v in schedule.items()}}

# ==================== WEAKNESS ANALYSIS ====================

@app.get("/api/users/{user_id}/weaknesses")
async def analyze_weaknesses(user_id: int):
    analysis = weakness_detector.analyze_weaknesses(user_id)
    return {"weak_topics": analysis.weak_topics, "weak_concepts": analysis.weak_concepts,
            "trends": analysis.improvement_trends, "recommendations": analysis.recommendations,
            "overall_score": analysis.overall_score}

# ==================== STUDY PLAN ====================

@app.post("/api/users/{user_id}/study-plan")
async def create_study_plan(user_id: int, target_topic: str, plan_type: str = "short_term",
                             hours_per_day: float = 2, db: Session = Depends(get_db)):
    progress = db.query(LearningProgress).filter(LearningProgress.user_id == user_id, LearningProgress.mastery_level >= 70).all()
    completed = [p.topic_id for p in progress]
    path = knowledge_graph.get_learning_path(target_topic, completed)
    total_hours = len(path) * 3
    days_needed = int(total_hours / hours_per_day) + 1
    topics_schedule = []
    current_date = datetime.now()
    for i, topic in enumerate(path):
        deadline = current_date + timedelta(days=int((i+1) * days_needed / len(path)))
        topics_schedule.append({"topic_id": topic['id'], "order": i+1, "estimated_hours": 3, "deadline": deadline.isoformat()})
    plan = StudyPlan(
        user_id=user_id, plan_type=plan_type, title=f"Path to {target_topic}",
        description=f"Learn {target_topic} in {days_needed} days",
        start_date=datetime.now(), end_date=current_date + timedelta(days=days_needed),
        topics=topics_schedule
    )
    db.add(plan)
    db.commit()
    return {"plan_id": plan.id, "title": plan.title, "days": days_needed, "topics": topics_schedule}

@app.get("/api/users/{user_id}/study-plans")
async def get_study_plans(user_id: int, db: Session = Depends(get_db)):
    plans = db.query(StudyPlan).filter(StudyPlan.user_id == user_id, StudyPlan.is_active == True).all()
    return {"plans": [{"id": p.id, "title": p.title, "progress": p.progress_percentage, "end_date": p.end_date.isoformat()} for p in plans]}

# ==================== PDF REPORT ====================

@app.get("/api/users/{user_id}/report")
async def generate_report(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    progress = db.query(LearningProgress).filter(LearningProgress.user_id == user_id).all()
    quiz_results = db.query(QuizResultModel).filter(QuizResultModel.user_id == user_id).order_by(QuizResultModel.completed_at.desc()).limit(10).all()
    user_data = {"username": user.username, "current_level": user.current_level,
                 "learning_goal": user.learning_goal, "learning_speed": user.learning_speed}
    progress_data = [{"topic_name": p.topic_name, "mastery_level": p.mastery_level, "time_spent_minutes": p.time_spent_minutes} for p in progress]
    quiz_data = [{"score": q.score, "total": q.total_questions} for q in quiz_results]
    pdf_bytes = pdf_gen.generate_progress_report(user_data, progress_data, quiz_data)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=progress_report_{user_id}.pdf"})

# ==================== DIAGNOSTIC QUESTIONS ====================

@app.get("/api/diagnostic-questions")
async def get_diagnostic_questions():
    return {"questions": [
        {"id": "d1", "text": "What is your primary learning goal?", "type": "text"},
        {"id": "d2", "text": "How much time can you dedicate daily?", "type": "choice", "options": ["30 min", "1 hour", "2 hours", "3+ hours"]},
        {"id": "d3", "text": "What is your current experience level?", "type": "choice", "options": ["Complete beginner", "Some basics", "Intermediate", "Advanced"]},
        {"id": "d4", "text": "What topics interest you most?", "type": "multi", "options": ["Programming", "Data Science", "Web Dev", "AI/ML", "Mobile Dev"]},
        {"id": "d5", "text": "Preferred learning style?", "type": "choice", "options": ["Videos", "Reading", "Hands-on", "Mixed"]}
    ]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
