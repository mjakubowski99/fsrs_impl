
from datetime import timezone
from src.fsrs_algorithm import FsrsParams
from src.fsrs_queue import FsrsQueue
from src.queue_type import QueueType
from datetime import datetime
from src.fsrs_model import FsrsModel
from sqlalchemy import BinaryExpression, case
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy import and_, or_
from src.state import State


class FsrsQueueMapper:

    def to_orders(self, queues: list[FsrsQueue], now: datetime) -> list[ColumnElement]:
        whens = []

        for idx, queue in enumerate(queues, start=1):
            condition = self.queue_condition(queue, now)
            whens.append((condition, idx))

        order_case = case(
            *whens,
            else_=None  # albo 999, zależnie od potrzeb
        )

        return [order_case.asc()]

    def to_filters(self, queues: list[FsrsQueue], now: datetime) -> BinaryExpression:
        conditions = [self.queue_condition(queue, now) for queue in queues]
        return or_(*conditions)

    def queue_condition(self, queue: FsrsQueue, now: datetime):
        conditions = []

        if queue.type == QueueType.DUE:
            conditions.extend(and_(*[
                FsrsModel.is_pending.is_(queue.is_pending),
                FsrsModel.state == State.REVIEW.value,
                FsrsModel.due <= now.timestamp(),
            ]))

        elif queue.type == QueueType.LEARNING:
            conditions.extend(and_(*[
                FsrsModel.is_pending.is_(queue.is_pending),
                FsrsModel.state.in_([State.LEARNING.value, State.RELEARNING.value]),
                FsrsModel.due <= now.timestamp(),
            ]))

        elif queue.type == QueueType.NEW:

            if not queue.is_pending:
                conditions.append(
                    or_(
                        and_(
                            FsrsModel.is_pending.is_(True),
                            FsrsModel.due <= now.timestamp(),
                        ),
                        FsrsModel.due.is_(None),
                    )
                )
            else:
                conditions.append(
                    FsrsModel.due.is_(None),
                )

        else:
            raise ValueError(f"Invalid queue type: {queue.type}")

        return and_(*conditions)
        
    def get_queue_type(self, fsrs: FsrsParams, new_queue_available: bool) -> QueueType:
        now = datetime.now(timezone.utc)

        if fsrs.newly_created or (new_queue_available and fsrs.is_pending and fsrs.due <= now):
            return QueueType.NEW
        elif fsrs.state.value == State.REVIEW.value and fsrs.due <= now:
            return QueueType.DUE
        elif fsrs.state.value in [State.LEARNING.value, State.RELEARNING.value]:
            return QueueType.LEARNING
        else:
            return QueueType.NEW
    
