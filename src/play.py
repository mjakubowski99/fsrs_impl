import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fsrs_model import Base, FlashcardModel
from src.fsrs_queue_mapper import FsrsQueueMapper
from src.review import Review
from src.fsrs_resolver import FsrsResolver
from src.fsrs_repository import FsrsRepository
from src.user_fsrs_repository import UserFsrsRepository
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///db.db')

Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

review = Review(
    fsrs_resolver=FsrsResolver(UserFsrsRepository()),
    fsrs_repository=FsrsRepository(FsrsQueueMapper()),
)

from src.rating import Rating

while True:
    card = review.find_next_card("test")

    if card is None:
        card = review.fsrs_repository.get_card_out_of_schedule("test", skip_blocked=True, delay_seconds=20)
        if card is None:
            card = review.fsrs_repository.get_card_out_of_schedule("test", skip_blocked=False, delay_seconds=None)

        if card is None:
            raise Exception("No card found")

        print(card.flashcard_id)

        rating = input("Rating (1=Again, 2=Hard, 3=Good, 4=Easy): ")
        print('Card out of schedule')
        review.update_out_of_schedule(Rating(int(rating)), card)
        continue

    print(card.flashcard.content)
    rating = input("Rating (1=Again, 2=Hard, 3=Good, 4=Easy): ")
    review.review(Rating(int(rating)), card)

# flashcards = [
#     FlashcardModel(
#         user_id="test",
#         content="shaving foam",
#     ),
#     FlashcardModel(
#         user_id="test",
#         content="hair spray",
#     ),
#     FlashcardModel(
#         user_id="test",
#         content="heating pipe",
#     ),
#     FlashcardModel(
#         user_id="test",
#         content="exhaust pipe",
#     ),
#     FlashcardModel(
#         user_id="test",
#         content="shaving cream",
#     ),
#     FlashcardModel(
#         user_id="test",
#         content="drain",
#     ),
#     FlashcardModel(
#         user_id="test",
#         content="shampoo",
#     ),
#     FlashcardModel(
#         user_id="test",
#         content="conditioner",
#     ),
# ]

# session = Session()

# for flashcard in flashcards:
#     session.add(flashcard)
#     session.commit()
