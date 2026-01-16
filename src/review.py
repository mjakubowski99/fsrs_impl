from src.flashcard import Flashcard
from src.fsrs_algorithm import FsrsParams
from src.fsrs_flashcard import FsrsFlashcard
from src.fsrs_resolver import FsrsResolver
from src.fsrs_repository import FsrsRepository
from src.rating import Rating

class Review:

    def __init__(self, fsrs_resolver: FsrsResolver, fsrs_repository: FsrsRepository):
        self.fsrs_resolver = fsrs_resolver
        self.fsrs_repository = fsrs_repository

    def find_next_card(self, user_id: str) -> FsrsFlashcard:
        user_fsrs = self.fsrs_resolver.resolve(user_id)

        available_queues = list(user_fsrs.get_available_queues())

        card = self.fsrs_repository.get_next_card(user_id, available_queues, skip_blocked=True, delay_seconds=30)
        
        if card is None:
            return self.fsrs_repository.get_next_card(user_id, available_queues, skip_blocked=False, delay_seconds=None)

        return card

    def review(self, rating: Rating, card: FsrsFlashcard):
        fsrs = card.fsrs

        if card.current_queue.transform_to_not_pending:
            fsrs.activate_from_pending()

        fsrs.review(rating)

        user_fsrs = self.fsrs_resolver.resolve(card.fsrs.user_id)

        card.current_queue.daily_count += 1

        user_fsrs.update_queue(card.current_queue)

        self.fsrs_resolver.user_fsrs_repository.save(user_fsrs)

        self.fsrs_repository.save(fsrs)

    def update_out_of_schedule(self, rating: Rating, fsrs: FsrsParams):
        fsrs.review_out_of_schedule(rating)

        self.fsrs_repository.save(fsrs)