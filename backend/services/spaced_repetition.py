"""
Spaced Repetition Service - Implements SM-2 algorithm for optimal review scheduling
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ReviewItem:
    """Represents an item to be reviewed"""
    topic_id: str
    topic_name: str
    ease_factor: float = 2.5
    interval_days: int = 1
    repetition_count: int = 0
    next_review_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None


class SpacedRepetitionService:
    """
    Implements the SM-2 (SuperMemo 2) algorithm for spaced repetition.
    
    The algorithm calculates optimal review intervals based on:
    - Quality of recall (0-5 rating)
    - Ease factor (individual difficulty rating)
    - Number of successful repetitions
    """
    
    MIN_EASE_FACTOR = 1.3
    INITIAL_EASE_FACTOR = 2.5
    
    def __init__(self):
        self.items: Dict[str, ReviewItem] = {}
    
    def calculate_next_review(self, item: ReviewItem, quality: int) -> ReviewItem:
        """
        Calculate the next review date using SM-2 algorithm.
        
        Args:
            item: The review item
            quality: Quality of recall (0-5)
                0 - Complete blackout
                1 - Incorrect, remembered after seeing answer
                2 - Incorrect, seemed easy after seeing answer
                3 - Correct with serious difficulty
                4 - Correct with some hesitation
                5 - Perfect response
        
        Returns:
            Updated ReviewItem with new interval and review date
        """
        # Update ease factor based on quality
        new_ease = item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ease = max(self.MIN_EASE_FACTOR, new_ease)
        
        # Calculate new interval
        if quality < 3:
            # Failed recall - reset to beginning
            new_interval = 1
            new_repetition = 0
        else:
            # Successful recall
            new_repetition = item.repetition_count + 1
            
            if new_repetition == 1:
                new_interval = 1
            elif new_repetition == 2:
                new_interval = 6
            else:
                new_interval = round(item.interval_days * new_ease)
        
        # Calculate next review date
        next_review = datetime.now() + timedelta(days=new_interval)
        
        return ReviewItem(
            topic_id=item.topic_id,
            topic_name=item.topic_name,
            ease_factor=new_ease,
            interval_days=new_interval,
            repetition_count=new_repetition,
            next_review_date=next_review,
            last_review_date=datetime.now()
        )
    
    def get_items_due_for_review(self, items: List[ReviewItem], 
                                  include_new: bool = True,
                                  limit: int = 20) -> List[ReviewItem]:
        """
        Get items that are due for review.
        
        Args:
            items: List of all review items
            include_new: Include items never reviewed
            limit: Maximum number of items to return
        """
        now = datetime.now()
        due_items = []
        new_items = []
        
        for item in items:
            if item.next_review_date is None:
                if include_new:
                    new_items.append(item)
            elif item.next_review_date <= now:
                due_items.append(item)
        
        # Sort due items by overdue time (most overdue first)
        due_items.sort(key=lambda x: x.next_review_date or now)
        
        # Combine due items with new items
        result = due_items + new_items
        return result[:limit]
    
    def calculate_retention_score(self, items: List[ReviewItem]) -> float:
        """
        Calculate overall retention score based on current state of all items.
        Returns a percentage (0-100).
        """
        if not items:
            return 0.0
        
        now = datetime.now()
        total_score = 0
        
        for item in items:
            if item.next_review_date is None:
                # New item, no retention yet
                total_score += 0
            elif item.next_review_date > now:
                # Not due yet - calculate retention based on how far from review
                days_until_review = (item.next_review_date - now).days
                # Higher interval = better retention estimation
                retention = min(100, 50 + (item.interval_days * 5))
                total_score += retention * (1 - days_until_review / max(item.interval_days, 1) * 0.1)
            else:
                # Overdue - decay retention
                days_overdue = (now - item.next_review_date).days
                decay = min(50, days_overdue * 5)
                total_score += max(0, 50 - decay)
        
        return total_score / len(items)
    
    def get_study_schedule(self, items: List[ReviewItem], days: int = 7) -> Dict[str, List[ReviewItem]]:
        """
        Generate a study schedule for the next N days.
        
        Returns:
            Dict mapping date strings to lists of items to review
        """
        schedule = {}
        now = datetime.now()
        
        for day_offset in range(days):
            date = now + timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")
            schedule[date_str] = []
        
        for item in items:
            if item.next_review_date:
                date_str = item.next_review_date.strftime("%Y-%m-%d")
                if date_str in schedule:
                    schedule[date_str].append(item)
        
        return schedule
    
    def optimize_daily_load(self, items: List[ReviewItem], 
                            max_per_day: int = 20,
                            days_ahead: int = 14) -> List[ReviewItem]:
        """
        Redistribute review load to prevent overwhelming days.
        Returns items with adjusted review dates.
        """
        schedule = self.get_study_schedule(items, days_ahead)
        adjusted_items = []
        overflow = []
        
        for date_str in sorted(schedule.keys()):
            daily_items = schedule[date_str] + overflow
            overflow = []
            
            if len(daily_items) <= max_per_day:
                adjusted_items.extend(daily_items)
            else:
                # Keep the most urgent items for today
                daily_items.sort(key=lambda x: x.interval_days)
                adjusted_items.extend(daily_items[:max_per_day])
                overflow = daily_items[max_per_day:]
        
        # Any remaining overflow goes to the last day
        adjusted_items.extend(overflow)
        
        return adjusted_items


def convert_score_to_quality(score_percentage: float) -> int:
    """
    Convert a quiz/test score (0-100) to SM-2 quality rating (0-5).
    """
    if score_percentage >= 95:
        return 5
    elif score_percentage >= 80:
        return 4
    elif score_percentage >= 60:
        return 3
    elif score_percentage >= 40:
        return 2
    elif score_percentage >= 20:
        return 1
    else:
        return 0
