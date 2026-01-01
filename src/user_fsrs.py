
from dataclasses import dataclass

from src.fsrs_queue import FsrsQueue
from src.queue_type import QueueType


@dataclass
class UserFsrs:
    user_id: str
    queues: list[FsrsQueue]

    @staticmethod 
    def new_fsrs(user_id: str) -> 'UserFsrs':
        return UserFsrs(
            user_id, [
                FsrsQueue(QueueType.NEW, False, 0, 10),
                FsrsQueue(QueueType.LEARNING, False, 0, 10),
                FsrsQueue(QueueType.DUE, False, 0, 10),
                FsrsQueue(QueueType.NEW, True, 0, 10),
                FsrsQueue(QueueType.LEARNING, True, 0, 10),
                FsrsQueue(QueueType.DUE, True, 0, 10),
            ],
        )
    
    def get_available_queues(self) -> list[FsrsQueue]:
        for queue in self.queues:
            if queue.is_available():
                yield queue

    def update_queue(self, queue: FsrsQueue):
        for i in range(len(self.queues)):
            if self.queues[i].type == queue.type:
                self.queues[i] = queue
                return 
                
        raise ValueError(f"Queue {queue.type} not found")