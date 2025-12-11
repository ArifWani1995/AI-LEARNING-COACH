"""
Weakness Detection Service - ML-powered analysis of learning gaps
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class PerformanceRecord:
    topic_id: str
    concept: str
    correct: bool
    timestamp: datetime
    difficulty: str
    time_taken_seconds: int


@dataclass
class WeaknessAnalysis:
    weak_topics: List[Dict]
    weak_concepts: List[Dict]
    improvement_trends: Dict[str, str]
    recommendations: List[str]
    overall_score: float


class WeaknessDetector:
    def __init__(self):
        self.performance_history: Dict[int, List[PerformanceRecord]] = defaultdict(list)
        self.topic_stats: Dict[int, Dict[str, dict]] = defaultdict(dict)
    
    def add_performance_record(self, user_id: int, record: PerformanceRecord):
        self.performance_history[user_id].append(record)
        self._update_stats(user_id, record)
    
    def _update_stats(self, user_id: int, record: PerformanceRecord):
        topic_id = record.topic_id
        if topic_id not in self.topic_stats[user_id]:
            self.topic_stats[user_id][topic_id] = {
                'total_attempts': 0, 'correct_attempts': 0, 'total_time': 0,
                'by_difficulty': {'easy': [0,0], 'medium': [0,0], 'hard': [0,0]},
                'by_concept': defaultdict(lambda: [0,0]), 'recent_performance': []
            }
        stats = self.topic_stats[user_id][topic_id]
        stats['total_attempts'] += 1
        stats['correct_attempts'] += 1 if record.correct else 0
        diff = record.difficulty.lower()
        if diff in stats['by_difficulty']:
            stats['by_difficulty'][diff][0] += 1
            stats['by_difficulty'][diff][1] += 1 if record.correct else 0
        stats['by_concept'][record.concept][0] += 1
        stats['by_concept'][record.concept][1] += 1 if record.correct else 0
        stats['recent_performance'].append((record.timestamp, record.correct))
        stats['recent_performance'] = stats['recent_performance'][-10:]
    
    def analyze_weaknesses(self, user_id: int, min_attempts: int = 3, weakness_threshold: float = 0.6) -> WeaknessAnalysis:
        weak_topics, weak_concepts, improvement_trends = [], [], {}
        user_stats = self.topic_stats.get(user_id, {})
        for topic_id, stats in user_stats.items():
            if stats['total_attempts'] < min_attempts: continue
            accuracy = stats['correct_attempts'] / stats['total_attempts']
            if accuracy < weakness_threshold:
                reasons = [f"Struggling with {d} questions" for d, (t,c) in stats['by_difficulty'].items() if t>0 and c/t<0.5]
                weak_topics.append({'topic_id': topic_id, 'weakness_score': 1-accuracy, 'accuracy': accuracy, 'reasons': reasons})
            improvement_trends[topic_id] = self._analyze_trend(stats['recent_performance'])
            for concept, (total, correct) in stats['by_concept'].items():
                if total >= 2 and correct/total < weakness_threshold:
                    weak_concepts.append({'concept': concept, 'weakness_score': 1-correct/total, 'topic_ids': [topic_id]})
        weak_topics.sort(key=lambda x: x['weakness_score'], reverse=True)
        overall = sum(s['correct_attempts'] for s in user_stats.values()) / max(1, sum(s['total_attempts'] for s in user_stats.values())) * 100 if user_stats else 0
        return WeaknessAnalysis(weak_topics, weak_concepts, improvement_trends, self._generate_recommendations(weak_topics, weak_concepts, improvement_trends), overall)
    
    def _analyze_trend(self, recent: List) -> str:
        if len(recent) < 4: return "stable"
        mid = len(recent)//2
        f = sum(1 for _,c in recent[:mid] if c)/mid
        s = sum(1 for _,c in recent[mid:] if c)/(len(recent)-mid)
        return "improving" if s-f > 0.15 else "declining" if f-s > 0.15 else "stable"
    
    def _generate_recommendations(self, weak_topics, weak_concepts, trends) -> List[str]:
        recs = []
        if weak_topics: recs.append(f"Priority: {weak_topics[0]['topic_id']}")
        declining = [t for t,tr in trends.items() if tr=="declining"]
        if declining: recs.append(f"Review needed: {', '.join(declining[:3])}")
        return recs
