"""
Quiz Generator Service - Creates personalized quizzes and diagnostic tests
"""
import random
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Question:
    """Represents a quiz question"""
    id: str
    topic_id: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    question_text: str
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str = ""
    explanation: str = ""
    concept_tags: List[str] = None  # For weakness detection
    points: int = 1
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class QuizConfig:
    """Configuration for quiz generation"""
    topic_ids: List[str]
    num_questions: int = 10
    difficulty_distribution: Dict[str, float] = None  # e.g., {"easy": 0.3, "medium": 0.5, "hard": 0.2}
    question_types: List[QuestionType] = None
    time_limit_minutes: Optional[int] = None
    is_diagnostic: bool = False
    focus_on_weaknesses: bool = False
    weak_concepts: List[str] = None


@dataclass
class QuizResult:
    """Result of a completed quiz"""
    quiz_id: str
    user_id: int
    score: float
    total_questions: int
    correct_count: int
    time_taken_seconds: int
    question_results: List[Dict]
    weak_concepts: List[str]
    recommendations: List[str]


class QuizGenerator:
    """
    Generates personalized quizzes based on user progress and learning goals.
    Supports diagnostic tests, practice quizzes, and spaced repetition reviews.
    """
    
    def __init__(self, question_bank: Dict[str, List[dict]] = None):
        """
        Initialize with a question bank.
        question_bank: Dict mapping topic_id to list of question dicts
        """
        self.question_bank = question_bank or {}
        self.generated_quizzes: Dict[str, dict] = {}
    
    def load_questions_from_file(self, path: str):
        """Load questions from a JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.question_bank = data.get('questions', {})
    
    def add_questions(self, topic_id: str, questions: List[dict]):
        """Add questions to the bank for a topic"""
        if topic_id not in self.question_bank:
            self.question_bank[topic_id] = []
        self.question_bank[topic_id].extend(questions)
    
    def generate_quiz(self, config: QuizConfig) -> Dict[str, Any]:
        """
        Generate a quiz based on configuration.
        
        Returns:
            Quiz dictionary with questions and metadata
        """
        quiz_id = f"quiz_{random.randint(10000, 99999)}"
        
        # Default difficulty distribution
        if config.difficulty_distribution is None:
            if config.is_diagnostic:
                config.difficulty_distribution = {"easy": 0.33, "medium": 0.34, "hard": 0.33}
            else:
                config.difficulty_distribution = {"easy": 0.2, "medium": 0.6, "hard": 0.2}
        
        # Collect available questions
        available_questions = []
        for topic_id in config.topic_ids:
            if topic_id in self.question_bank:
                for q in self.question_bank[topic_id]:
                    q_copy = q.copy()
                    q_copy['topic_id'] = topic_id
                    available_questions.append(q_copy)
        
        # If focusing on weaknesses, prioritize those questions
        if config.focus_on_weaknesses and config.weak_concepts:
            weak_questions = [
                q for q in available_questions 
                if any(concept in q.get('concept_tags', []) for concept in config.weak_concepts)
            ]
            # Include at least 50% weak concept questions
            weak_count = min(len(weak_questions), config.num_questions // 2)
            selected_weak = random.sample(weak_questions, weak_count) if weak_questions else []
            remaining_count = config.num_questions - len(selected_weak)
            other_questions = [q for q in available_questions if q not in selected_weak]
            selected_other = random.sample(other_questions, min(remaining_count, len(other_questions)))
            selected_questions = selected_weak + selected_other
        else:
            # Select by difficulty distribution
            selected_questions = self._select_by_difficulty(
                available_questions, 
                config.num_questions,
                config.difficulty_distribution
            )
        
        # Filter by question types if specified
        if config.question_types:
            type_values = [qt.value for qt in config.question_types]
            selected_questions = [
                q for q in selected_questions 
                if q.get('question_type') in type_values
            ]
        
        # Shuffle and trim to requested number
        random.shuffle(selected_questions)
        selected_questions = selected_questions[:config.num_questions]
        
        # Build quiz structure
        quiz = {
            "id": quiz_id,
            "topic_ids": config.topic_ids,
            "is_diagnostic": config.is_diagnostic,
            "time_limit_minutes": config.time_limit_minutes,
            "total_points": sum(q.get('points', 1) for q in selected_questions),
            "questions": selected_questions,
            "created_at": None  # Will be set by API
        }
        
        self.generated_quizzes[quiz_id] = quiz
        return quiz
    
    def _select_by_difficulty(self, questions: List[dict], 
                              num_questions: int,
                              distribution: Dict[str, float]) -> List[dict]:
        """Select questions according to difficulty distribution"""
        # Group by difficulty
        by_difficulty = {"easy": [], "medium": [], "hard": []}
        for q in questions:
            diff = q.get('difficulty', 'medium')
            if diff in by_difficulty:
                by_difficulty[diff].append(q)
        
        selected = []
        for diff, ratio in distribution.items():
            count = int(num_questions * ratio)
            available = by_difficulty.get(diff, [])
            selected.extend(random.sample(available, min(count, len(available))))
        
        return selected
    
    def generate_diagnostic_quiz(self, topic_ids: List[str], 
                                  user_level: str = "beginner") -> Dict[str, Any]:
        """
        Generate a diagnostic quiz to assess user's current knowledge level.
        Covers a broad range of concepts and difficulties.
        """
        # Adjust question count based on level
        num_questions = {"beginner": 15, "intermediate": 20, "advanced": 25}.get(user_level, 15)
        
        config = QuizConfig(
            topic_ids=topic_ids,
            num_questions=num_questions,
            is_diagnostic=True,
            time_limit_minutes=num_questions * 2  # 2 minutes per question
        )
        
        return self.generate_quiz(config)
    
    def grade_quiz(self, quiz_id: str, user_answers: List[Dict]) -> QuizResult:
        """
        Grade a completed quiz and analyze weaknesses.
        
        Args:
            quiz_id: ID of the quiz
            user_answers: List of {question_id, answer, time_seconds}
        
        Returns:
            QuizResult with score and analysis
        """
        quiz = self.generated_quizzes.get(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")
        
        questions_by_id = {q['id']: q for q in quiz['questions']}
        
        correct_count = 0
        total_time = 0
        question_results = []
        weak_concepts = []
        
        for answer in user_answers:
            q_id = answer['question_id']
            question = questions_by_id.get(q_id)
            
            if not question:
                continue
            
            is_correct = self._check_answer(question, answer['answer'])
            if is_correct:
                correct_count += 1
            else:
                # Track weak concepts
                weak_concepts.extend(question.get('concept_tags', []))
            
            total_time += answer.get('time_seconds', 0)
            
            question_results.append({
                'question_id': q_id,
                'correct': is_correct,
                'user_answer': answer['answer'],
                'correct_answer': question['correct_answer'],
                'time_seconds': answer.get('time_seconds', 0),
                'explanation': question.get('explanation', '')
            })
        
        # Calculate score
        total_questions = len(quiz['questions'])
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Deduplicate and rank weak concepts
        weak_concepts = list(set(weak_concepts))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(score, weak_concepts)
        
        return QuizResult(
            quiz_id=quiz_id,
            user_id=0,  # Will be set by API
            score=score,
            total_questions=total_questions,
            correct_count=correct_count,
            time_taken_seconds=total_time,
            question_results=question_results,
            weak_concepts=weak_concepts,
            recommendations=recommendations
        )
    
    def _check_answer(self, question: dict, user_answer: str) -> bool:
        """Check if user's answer is correct"""
        correct = question.get('correct_answer', '').strip().lower()
        user = str(user_answer).strip().lower()
        
        # For multiple choice, compare directly
        if question.get('question_type') == 'multiple_choice':
            return user == correct
        
        # For true/false
        if question.get('question_type') == 'true_false':
            return user == correct
        
        # For fill in blank, allow some flexibility
        if question.get('question_type') == 'fill_blank':
            # Check if answer contains the key terms
            return correct in user or user in correct
        
        # Default exact match
        return user == correct
    
    def _generate_recommendations(self, score: float, weak_concepts: List[str]) -> List[str]:
        """Generate study recommendations based on quiz performance"""
        recommendations = []
        
        if score < 40:
            recommendations.append("Consider reviewing the fundamentals of these topics")
            recommendations.append("Try starting with easier practice questions")
        elif score < 70:
            recommendations.append("Good progress! Focus on the concepts you struggled with")
            recommendations.append("Practice more questions at medium difficulty")
        elif score < 90:
            recommendations.append("Great job! You're almost there")
            recommendations.append("Challenge yourself with harder questions")
        else:
            recommendations.append("Excellent mastery! Consider moving to advanced topics")
        
        if weak_concepts:
            recommendations.append(f"Focus on these concepts: {', '.join(weak_concepts[:5])}")
        
        return recommendations


# Sample question templates for different subjects
SAMPLE_QUESTION_TEMPLATES = {
    "programming": {
        "multiple_choice": {
            "template": "What is the output of the following code?\n```{code}```",
            "generate_options": lambda correct: [correct, "Error", "None", "undefined"]
        },
        "true_false": {
            "template": "True or False: {statement}",
        },
        "fill_blank": {
            "template": "Complete the code: {code_with_blank}",
        }
    },
    "math": {
        "multiple_choice": {
            "template": "Solve: {equation}",
        },
        "true_false": {
            "template": "True or False: {statement}",
        }
    }
}
