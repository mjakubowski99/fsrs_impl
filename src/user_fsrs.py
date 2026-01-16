
from dataclasses import dataclass
from datetime import datetime

from src.fsrs_queue import FsrsQueue
from src.queue_type import QueueType
from datetime import timezone

@dataclass
class UserFsrs:
    id: int|None
    user_id: str
    queues: list[FsrsQueue]
    updated_at: datetime

    @staticmethod 
    def new_fsrs(user_id: str) -> 'UserFsrs':
        return UserFsrs(
            id=None,
            user_id=user_id, 
            queues=[
                FsrsQueue(QueueType.DUE, False, 0, 10),
                FsrsQueue(QueueType.LEARNING, False, 0, 10),
                FsrsQueue(QueueType.NEW, False, 0, 10),
                FsrsQueue(QueueType.DUE, True, 0, 10),
                FsrsQueue(QueueType.LEARNING, True, 0, 10),
                FsrsQueue(QueueType.NEW, True, 0, 10),
            ],
            updated_at=datetime.now(timezone.utc),
        )
    
    def get_available_queues(self) -> list[FsrsQueue]:
        for queue in self.queues:
            if queue.is_available():
                yield queue

    def update_queue(self, queue: FsrsQueue):
        for i in range(len(self.queues)):
            if self.queues[i].type == queue.type and self.queues[i].is_pending == queue.is_pending:
                self.queues[i] = queue
                return 
                
        raise ValueError(f"Queue {queue.type} not found")