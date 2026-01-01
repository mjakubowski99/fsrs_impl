
from flashcard import Flashcard
from fsrs_queue import FsrsQueue
from fsrs_queue_mapper import FsrsQueueMapper
from dataclasses import dataclass
from src.fsrs import FsrsParams
from src.fsrs_flashcard import FsrsFlashcard
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.fsrs_model import FlashcardModel, FsrsModel

engine = create_engine('sqlite:///fsrs.db')

Session = sessionmaker(bind=engine)

@dataclass
class FsrsRepository:
    queue_mapper: FsrsQueueMapper

    def get_next_card(self, user_id: str, available_queues: list[FsrsQueue]) -> FsrsFlashcard:
        session = Session()

        result = (
            session.query(FlashcardModel)
                .outerjoin(FsrsModel)
                .filter(FlashcardModel.user_id == user_id)
                .filter(self.queue_mapper.to_filters(available_queues))
                .order_by(self.queue_mapper.to_orders(available_queues))
                .limit(1)
                .first()
        )

        if result is None:
            raise Exception("No card found")

        flashcard = result[0]
        fsrs_data = result[1]

        if flashcard is None:
            raise Exception("No card found")

        only_pending_queues = all([queue for queue in available_queues if queue.is_pending])

        fsrs = FsrsParams(
            difficulty=fsrs_data['difficulty'],
            stability=fsrs_data['stability'],
            next_review_date=fsrs_data['next_review_date'],
            due_date=fsrs_data['due_date'],
            reviews_count=fsrs_data['reviews_count'],
            last_rating=fsrs_data['last_rating'],
            is_pending=fsrs_data['is_pending'],
        ) if fsrs_data is not None else FsrsParams.new_fsrs(only_pending_queues)

        queue_type = self.queue_mapper.get_queue_type(fsrs)

        current_queue = available_queues.find(lambda queue: queue.type == queue_type and queue.is_pending == fsrs.is_pending)

        flashcard = Flashcard(
            content=flashcard['content'],
        )

        return FsrsFlashcard(
            fsrs=fsrs,
            flashcard=flashcard,
            current_queue=current_queue,
        )