"""
Knowledge Graph Service - Manages learning topics and their relationships
"""
import json
import os
from typing import Dict, List, Optional
from collections import defaultdict


class KnowledgeGraph:
    """
    Knowledge Graph for managing learning topics and their relationships.
    Supports prerequisite detection, learning path generation, and topic recommendations.
    """
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.topics: Dict[str, dict] = {}
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)  # topic -> prerequisites
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)  # topic -> dependent topics
        
        if knowledge_base_path and os.path.exists(knowledge_base_path):
            self.load_from_file(knowledge_base_path)
    
    def load_from_file(self, path: str):
        """Load knowledge base from JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for topic in data.get('topics', []):
            self.add_topic(topic)
    
    def add_topic(self, topic_data: dict):
        """Add a topic to the knowledge graph"""
        topic_id = topic_data['id']
        self.topics[topic_id] = topic_data
        
        # Build adjacency lists for prerequisites
        prerequisites = topic_data.get('prerequisites', [])
        self.adjacency_list[topic_id] = prerequisites
        
        for prereq in prerequisites:
            self.reverse_adjacency[prereq].append(topic_id)
    
    def get_topic(self, topic_id: str) -> Optional[dict]:
        """Get topic by ID"""
        return self.topics.get(topic_id)
    
    def get_all_topics(self) -> List[dict]:
        """Get all topics"""
        return list(self.topics.values())
    
    def get_topics_by_category(self, category: str) -> List[dict]:
        """Get all topics in a category"""
        return [t for t in self.topics.values() if t.get('category') == category]
    
    def get_prerequisites(self, topic_id: str) -> List[dict]:
        """Get all prerequisites for a topic"""
        prereq_ids = self.adjacency_list.get(topic_id, [])
        return [self.topics[pid] for pid in prereq_ids if pid in self.topics]
    
    def get_dependent_topics(self, topic_id: str) -> List[dict]:
        """Get topics that depend on this topic"""
        dependent_ids = self.reverse_adjacency.get(topic_id, [])
        return [self.topics[did] for did in dependent_ids if did in self.topics]
    
    def get_learning_path(self, target_topic_id: str, completed_topics: List[str] = None) -> List[dict]:
        """
        Generate an optimal learning path to reach the target topic.
        Uses topological sort to respect prerequisites.
        """
        completed = set(completed_topics or [])
        
        # Find all required topics using BFS
        required_topics = set()
        queue = [target_topic_id]
        
        while queue:
            current = queue.pop(0)
            if current in required_topics or current in completed:
                continue
            
            required_topics.add(current)
            prereqs = self.adjacency_list.get(current, [])
            queue.extend(prereqs)
        
        # Topological sort
        in_degree = defaultdict(int)
        for topic_id in required_topics:
            for prereq in self.adjacency_list.get(topic_id, []):
                if prereq in required_topics:
                    in_degree[topic_id] += 1
        
        # Start with topics that have no prerequisites (or prerequisites already completed)
        queue = [t for t in required_topics if in_degree[t] == 0]
        sorted_path = []
        
        while queue:
            # Sort by difficulty level
            queue.sort(key=lambda t: self.topics.get(t, {}).get('difficulty_level', 1))
            current = queue.pop(0)
            sorted_path.append(self.topics[current])
            
            for dependent in self.reverse_adjacency.get(current, []):
                if dependent in required_topics:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        return sorted_path
    
    def recommend_next_topics(self, completed_topics: List[str], 
                              weak_topics: List[str] = None,
                              max_recommendations: int = 5) -> List[dict]:
        """
        Recommend next topics based on completed topics and weaknesses.
        Prioritizes reviewing weak topics and unlocking new content.
        """
        completed = set(completed_topics or [])
        weak = set(weak_topics or [])
        
        recommendations = []
        
        # First, recommend reviewing weak topics
        for topic_id in weak:
            if topic_id in self.topics:
                topic = self.topics[topic_id].copy()
                topic['recommendation_reason'] = 'Review recommended due to weakness'
                recommendations.append(topic)
        
        # Find topics whose prerequisites are all completed
        for topic_id, topic in self.topics.items():
            if topic_id in completed:
                continue
            
            prereqs = set(self.adjacency_list.get(topic_id, []))
            if prereqs.issubset(completed):
                topic_copy = topic.copy()
                topic_copy['recommendation_reason'] = 'Prerequisites completed'
                recommendations.append(topic_copy)
        
        # Sort by difficulty and limit
        recommendations.sort(key=lambda t: t.get('difficulty_level', 1))
        return recommendations[:max_recommendations]
    
    def get_topic_depth(self, topic_id: str) -> int:
        """Get the depth of a topic in the knowledge graph (number of prerequisite levels)"""
        if topic_id not in self.topics:
            return 0
        
        max_depth = 0
        prereqs = self.adjacency_list.get(topic_id, [])
        
        for prereq in prereqs:
            depth = self.get_topic_depth(prereq) + 1
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def find_gaps(self, completed_topics: List[str], target_topic: str) -> List[dict]:
        """Find knowledge gaps between current progress and target topic"""
        required_path = self.get_learning_path(target_topic, completed_topics)
        completed = set(completed_topics or [])
        
        gaps = []
        for topic in required_path:
            if topic['id'] not in completed:
                gaps.append(topic)
        
        return gaps
