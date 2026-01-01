
from src.fsrs import FsrsParams
from src.fsrs_queue import FsrsQueue
from src.queue_type import QueueType
from datetime import datetime
from src.fsrs_model import FsrsModel
from datetime import timezone
from sqlalchemy import BinaryExpression, case
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy import and_, or_


class FsrsQueueMapper:

    def to_orders(self, queues: list[FsrsQueue]) -> list[ColumnElement]:
        whens = []

        for idx, queue in enumerate(queues, start=1):
            condition = self.queue_condition(queue)
            whens.append((condition, idx))

        order_case = case(
            *whens,
            else_=None  # albo 999, zależnie od potrzeb
        )

        return [order_case.asc()]

    def to_filters(self, queues: list[FsrsQueue]) -> list[BinaryExpression]:
        conditions = [self.queue_condition(queue) for queue in queues]
        return [or_(*conditions)]

    def queue_condition(queue: FsrsQueue):
        now = datetime.now(timezone.utc)

        base = []
        if queue.is_pending:
            base.append(FsrsModel.is_pending.is_(True))
        else:
            base.append(FsrsModel.is_pending.is_(False))

        if queue.type == QueueType.DUE:
            base.extend([
                FsrsModel.stability > 3,
                FsrsModel.next_review_date <= now,
            ])

        elif queue.type == QueueType.LEARNING:
            base.append(FsrsModel.stability <= 3)

        elif queue.type == QueueType.NEW:
            base.append(FsrsModel.reviews_count == 0)

        else:
            raise ValueError(f"Invalid queue type: {queue.type}")

        return and_(*base)
        
        
    def get_queue_type(self, fsrs: FsrsParams) -> QueueType:
        if fsrs.stability is None:
            return QueueType.NEW
        elif fsrs.stability > 3 and fsrs.next_review_date <= datetime.now():
            return QueueType.DUE
        elif fsrs.stability <= 3:
            return QueueType.LEARNING
        else:
            return QueueType.NEW
    
