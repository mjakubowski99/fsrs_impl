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

        available_queues = user_fsrs.get_available_queues()

        return self.fsrs_repository.get_next_card(user_id, available_queues)

    def review(self, rating: Rating, card: FsrsFlashcard):
        if card.current_queue.transform_to_not_pending:
            card.fsrs.activate_from_pending()

        card.fsrs.review(rating)