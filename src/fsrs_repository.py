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

engine = create_engine('sqlite:///db.db')

Session = sessionmaker(bind=engine)

@dataclass
class FsrsRepository:
    queue_mapper: FsrsQueueMapper

    def get_next_card(self, user_id: str, available_queues: list[FsrsQueue]) -> FsrsFlashcard:
        session = Session()

        now = datetime.now(timezone.utc)

        query = (
            session.query(FlashcardModel, FsrsModel)
                .outerjoin(FsrsModel, FlashcardModel.id == FsrsModel.flashcard_id)
                .filter(FlashcardModel.user_id == user_id)
                .filter(self.queue_mapper.to_filters(available_queues, now))
                .order_by(*self.queue_mapper.to_orders(available_queues, now))
                .limit(1)
        )
        result = query.first()

        if result is None:
            raise Exception("No card found")

        flashcard = result[0]
        fsrs_data = result[1]

        if flashcard is None:
            raise Exception("No card found")

        only_pending_queues = all([queue for queue in available_queues if queue.is_pending])
        new_queue_available = any([queue for queue in available_queues if queue.type == QueueType.NEW])

        fsrs = FsrsParams(
            difficulty=float(fsrs_data.difficulty) if fsrs_data.difficulty is not None else None,
            stability=float(fsrs_data.stability) if fsrs_data.stability is not None else None,
            due=datetime.fromtimestamp(float(fsrs_data.due), tz=timezone.utc) if fsrs_data.due else None,
            state=State(int(fsrs_data.state)),
            reviews_count=fsrs_data.reviews_count,
            last_rating=Rating(int(fsrs_data.last_rating)) if fsrs_data.last_rating else None,
            is_pending=fsrs_data.is_pending,
        ) if fsrs_data is not None else FsrsParams.new_fsrs(only_pending_queues)

        queue_type = self.queue_mapper.get_queue_type(fsrs, new_queue_available)

        current_queue = next((queue for queue in available_queues if queue.type == queue_type and queue.is_pending == fsrs.is_pending), None)

        if current_queue is None:
            current_queue = next((queue for queue in available_queues if queue.type == queue_type), None)

        if current_queue is None:
            raise Exception(f"No matching queue found for type {queue_type} and is_pending={fsrs.is_pending}")

        if new_queue_available and fsrs.is_pending:
            current_queue.transform_to_not_pending = True
    
        flashcard = Flashcard(
            content=flashcard.content,
        )

        return FsrsFlashcard(
            fsrs=fsrs,
            flashcard=flashcard,
            current_queue=current_queue,
        )

    def save(self, fsrs: FsrsParams, flashcard_id: int):
        model = FsrsModel(
            flashcard_id=flashcard_id,
            difficulty=fsrs.difficulty,
            stability=fsrs.stability,
            state=fsrs.state.value,
            due=fsrs.due.timestamp() if fsrs.due else None,
            reviews_count=fsrs.reviews_count,
            last_rating=fsrs.last_rating.value if fsrs.last_rating else None,
        )

        if fsrs.id is not None:
            model.id = fsrs.id

        session = Session()
        session.add(model)
        session.commit()