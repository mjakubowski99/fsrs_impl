from datetime import datetime
from datetime import timezone
from src.flashcard import Flashcard
from src.fsrs_queue import FsrsQueue
from src.fsrs_queue_mapper import FsrsQueueMapper
from dataclasses import dataclass
from src.fsrs_algorithm import FsrsParams
from src.fsrs_flashcard import FsrsFlashcard
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.fsrs_model import FlashcardModel, FsrsModel
from src.queue_type import QueueType
from src.rating import Rating
from src.state import State
from datetime import timedelta
from copy import copy
from sqlalchemy import or_

engine = create_engine('sqlite:///db.db')

Session = sessionmaker(bind=engine)

FRESHNESS_SCORE_RATIO = 1000000

@dataclass
class FsrsRepository:
    queue_mapper: FsrsQueueMapper

    def get_next_card(self, user_id: str, available_queues: list[FsrsQueue], skip_blocked: bool = True, delay_seconds: int|None = None) -> FsrsFlashcard|None:
        session = Session()

        now = datetime.now(timezone.utc)

        if delay_seconds is not None:
            now_with_delay = copy(now) - timedelta(seconds=delay_seconds)
        else:
            now_with_delay = None

        query = (
            session.query(FlashcardModel, FsrsModel)
                .outerjoin(FsrsModel, FlashcardModel.id == FsrsModel.flashcard_id)
                .filter(or_(FlashcardModel.user_id == user_id, FsrsModel.user_id == user_id))
                .filter(self.queue_mapper.to_filters(available_queues, now))
                .order_by(*self.queue_mapper.to_orders(available_queues, now))
        )

        if skip_blocked:
            query = query.filter(or_(FsrsModel.blocked_until <= now.timestamp(), FsrsModel.blocked_until.is_(None)))

        if now_with_delay is not None:
            query = query.filter(or_(FsrsModel.last_review <= now_with_delay.timestamp(), FsrsModel.last_review.is_(None)))

        result = query.limit(1).first()

        if result is None:
            return None 

        return self._map_fsrs_flashcard(result, user_id, available_queues)

    def get_card_out_of_schedule(self, user_id: str, skip_blocked: bool = True, delay_seconds: int|None = None) -> FsrsParams:
        session = Session()

        now = datetime.now(timezone.utc)

        query = (
            session.query(FlashcardModel, FsrsModel)
                .outerjoin(FsrsModel, FlashcardModel.id == FsrsModel.flashcard_id)
                .filter(or_(FlashcardModel.user_id == user_id, FsrsModel.user_id == user_id))
                .order_by(
                    FsrsModel.freshness_score.desc().nullslast()
                )
        )

        if skip_blocked:
            query = query.filter(or_(FsrsModel.blocked_until <= now.timestamp(), FsrsModel.blocked_until.is_(None)))

        result = query.limit(1).first()

        if result is None:
            return None 

        return self._map_params(result, user_id)

    def save(self, fsrs: FsrsParams):
        with Session() as session:
            model = (
                session.query(FsrsModel)
                .filter(FsrsModel.flashcard_id == fsrs.flashcard_id, FsrsModel.user_id == fsrs.user_id)
                .one_or_none()
            )

            if model is not None:
                model = self.update(model,fsrs)
            else:
                model = self._to_db(fsrs)

            session.add(model)
            session.commit()

    def update_freshness_score(self, user_id: str, flashcard: Flashcard, freshness_score: float):
        with Session() as session:
            session.query(FsrsModel)\
                .filter(FsrsModel.user_id == user_id)\
                .filter(FsrsModel.flashcard_id == flashcard.id)\
                .update({
                    "freshness_score": freshness_score,
                    "updated_at": datetime.now(timezone.utc),
                }, synchronize_session=False)
            session.commit()

    def update(self, row: FsrsModel, fsrs: FsrsParams) -> FsrsModel:
        row.difficulty = fsrs.difficulty
        row.stability = fsrs.stability
        row.state = fsrs.state.value
        row.due = fsrs.due.timestamp() if fsrs.due else None
        row.reviews_count = fsrs.reviews_count
        row.last_rating = fsrs.last_rating.value if fsrs.last_rating else None
        row.is_pending = fsrs.is_pending
        row.last_review = fsrs.last_review.timestamp() if fsrs.last_review else None
        row.step = fsrs.step
        row.freshness_score = int(fsrs.freshness_score * FRESHNESS_SCORE_RATIO)
        row.updated_at = fsrs.updated_at
        return row 

    def _to_db(self, fsrs: FsrsParams) -> FsrsModel:
        return FsrsModel(
            flashcard_id=fsrs.flashcard_id,
            user_id=fsrs.user_id,
            difficulty=fsrs.difficulty,
            stability=fsrs.stability,
            state=fsrs.state.value,
            due=fsrs.due.timestamp() if fsrs.due else None,
            reviews_count=fsrs.reviews_count,
            last_rating=fsrs.last_rating.value if fsrs.last_rating else None,
            is_pending=fsrs.is_pending,
            last_review=fsrs.last_review.timestamp() if fsrs.last_review else None,
            step=fsrs.step,
            freshness_score=int(fsrs.freshness_score * FRESHNESS_SCORE_RATIO),
            updated_at=fsrs.updated_at,
        )

    def _map_fsrs_flashcard(self, result: tuple[FlashcardModel, FsrsModel], user_id: str, available_queues: list[FsrsQueue]) -> FsrsFlashcard:
        new_queue_available = any([queue for queue in available_queues if queue.type == QueueType.NEW])

        fsrs = self._map_params(result, user_id)

        queue_type = self.queue_mapper.get_queue_type(fsrs, new_queue_available)

        current_queue = next((queue for queue in available_queues if queue.type == queue_type and queue.is_pending == fsrs.is_pending), None)

        if current_queue is None:
            current_queue = next((queue for queue in available_queues if queue.type == queue_type), None)

        if current_queue is None:
            raise Exception(f"No matching queue found for type {queue_type} and is_pending={fsrs.is_pending}")

        if new_queue_available and fsrs.is_pending:
            current_queue.transform_to_not_pending = True

        return FsrsFlashcard(
            fsrs=fsrs,
            flashcard=self._map_flashcard(result),
            current_queue=current_queue,
        )

    def _map_flashcard(self, row: tuple[FlashcardModel, FsrsModel]) -> Flashcard:
        flashcard = row[0]
        return Flashcard(
            id=flashcard.id,
            content=flashcard.content,
        )

    def _map_params(self, row: tuple[FlashcardModel, FsrsModel], user_id: str) -> FsrsParams:
        flashcard = row[0]
        fsrs_data = row[1]

        if fsrs_data is None:
            return FsrsParams.new_fsrs(flashcard_id=flashcard.id, user_id=user_id)

        return FsrsParams(
            flashcard_id=flashcard.id,
            user_id=fsrs_data.user_id,
            difficulty=float(fsrs_data.difficulty) if fsrs_data.difficulty is not None else None,
            stability=float(fsrs_data.stability) if fsrs_data.stability is not None else None,
            due=datetime.fromtimestamp(float(fsrs_data.due), tz=timezone.utc) if fsrs_data.due else None,
            state=State(int(fsrs_data.state)),
            reviews_count=fsrs_data.reviews_count,
            last_rating=Rating(int(fsrs_data.last_rating)) if fsrs_data.last_rating else None,
            is_pending=fsrs_data.is_pending,
            last_review=datetime.fromtimestamp(fsrs_data.last_review, tz=timezone.utc) if fsrs_data.last_review else None,
            step=fsrs_data.step,
            freshness_score=float(fsrs_data.freshness_score) / FRESHNESS_SCORE_RATIO if fsrs_data.freshness_score != 0 else 0.0,
            updated_at=fsrs_data.updated_at,
        )


        