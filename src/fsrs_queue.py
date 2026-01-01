from dataclasses import dataclass

from src.queue_type import QueueType

@dataclass
class FsrsQueue:
    type: QueueType
    is_pending: bool 
    daily_count: int 
    daily_limit: int

    def is_available(self) -> bool:
        return self.daily_count < self.daily_limit

    def to_fsrs_filters(self) -> list[str]:
        if self.is_pending:
            return [
                "fsrs.is_pending is true",
            ]

        if self.type == QueueType.DUE:
            return [
                "fsrs.stability > 3",
                "fsrs.next_review_date <= NOW()",
            ]
        elif self.type == QueueType.LEARNING:
            return [
                "fsrs.stability <= 3",
            ]
        elif self.type == QueueType.NEW:
            return [
                "fsrs.reviews_count = 0",
            ]

        raise Exception(f"Invalid queue type: {self.type}")

