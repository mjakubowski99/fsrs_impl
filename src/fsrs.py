from dataclasses import dataclass
from datetime import datetime

from src.rating import Rating

@dataclass
class FsrsParams:
    is_pending: bool
    difficulty: float|None 
    stability: int|None 
    due_date: datetime|None
    last_review_date: datetime|None
    reviews_count: int
    last_rating: Rating|None
    learning_steps: list
    step: int = 0 

    def review(self, rating: Rating):
        pass 
    