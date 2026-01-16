from src.fsrs_algorithm import FsrsParams
from src.fsrs_model import FlashcardModel, FsrsModel
from src.fsrs_queue_mapper import FsrsQueueMapper
from src.fsrs_repository import FsrsRepository
from src.queue_type import QueueType
from src.fsrs_queue import FsrsQueue
from sqlalchemy.orm import sessionmaker
from conftest import engine
from datetime import datetime, timezone
from src.state import State

Session = sessionmaker(bind=engine)

def test_fsrs_repository_get_next_card():
    fsrs_repository = FsrsRepository(FsrsQueueMapper())
    
    available_queues = [
        FsrsQueue(QueueType.NEW, False, 0, 10),
        FsrsQueue(QueueType.LEARNING, False, 0, 10),
        FsrsQueue(QueueType.DUE, False, 0, 10),
        FsrsQueue(QueueType.NEW, True, 0, 10),
        FsrsQueue(QueueType.LEARNING, True, 0, 10),
        FsrsQueue(QueueType.DUE, True, 0, 10),
    ]

    session = Session()
    for i in range(10):
        flashcard = FlashcardModel(
            user_id="test",
            content=f"Test card {i}",
        )
        session = Session()
        session.add(flashcard)
        session.commit()
        fsrs = FsrsModel(
            flashcard_id=flashcard.id,
            user_id="test",
            difficulty=0.0,
            stability=0.0,
            state=State.LEARNING.value,
            due=None,
            reviews_count=0,
            last_rating=None,
            is_pending=False,
        )
        session.add(fsrs)
        session.commit()

    card = fsrs_repository.get_next_card("test", available_queues)

    assert card is not None
    

def test_fsrs_get_due_card():
    fsrs_repository = FsrsRepository(FsrsQueueMapper())
    
    available_queues = [
        FsrsQueue(QueueType.DUE, False, 0, 10),
    ]

    session = Session()
    for i in range(1):
        flashcard = FlashcardModel(
            user_id="test",
            content=f"Test card {i}",
        )
        session = Session()
        session.add(flashcard)
        session.commit()
        fsrs = FsrsModel(
            flashcard_id=flashcard.id,
            user_id="test",
            difficulty=0.0,
            stability=0.0,
            state=State.REVIEW.value,
            due=int(datetime.now(timezone.utc).timestamp()),
            reviews_count=0,
            last_rating=None,
            is_pending=False,
        )
        session.add(fsrs)
        session.commit()

    card = fsrs_repository.get_next_card("test", available_queues)

    assert card is not None
    assert card.fsrs.state == State.REVIEW

def test_get_learning_card():
    fsrs_repository = FsrsRepository(FsrsQueueMapper())
    
    available_queues = [
        FsrsQueue(QueueType.LEARNING, False, 0, 10),
    ]

    session = Session()
    for i in range(1):
        flashcard = FlashcardModel(
            user_id="test",
            content=f"Test card {i}",
        )
        session = Session()
        session.add(flashcard)
        session.commit()
        fsrs = FsrsModel(
            flashcard_id=flashcard.id,
            user_id="test",
            difficulty=0.0,
            stability=0.0,
            state=State.RELEARNING.value,
            due=int(datetime.now(timezone.utc).timestamp()),
            reviews_count=0,
            last_rating=None,
            is_pending=False,
        )
        session.add(fsrs)
        session.commit()

    card = fsrs_repository.get_next_card("test", available_queues)

    assert card is not None
    assert card.fsrs.state == State.RELEARNING
    assert card.current_queue.type == QueueType.LEARNING

def test_get_pending_due_card():
    fsrs_repository = FsrsRepository(FsrsQueueMapper())
    
    available_queues = [
        FsrsQueue(QueueType.NEW, False, 0, 10),
    ]

    session = Session()
    for i in range(1):
        flashcard = FlashcardModel(
            user_id="test",
            content=f"Test card {i}",
        )
        session = Session()
        session.add(flashcard)
        session.commit()
        fsrs = FsrsModel(
            flashcard_id=flashcard.id,
            user_id="test",
            difficulty=0.0,
            stability=0.0,
            state=State.REVIEW.value,
            due=int(datetime.now(timezone.utc).timestamp()),
            reviews_count=0,
            last_rating=None,
            is_pending=True,
        )
        session.add(fsrs)
        session.commit()

    card = fsrs_repository.get_next_card("test", available_queues)

    assert card is not None
    assert card.current_queue.type == QueueType.NEW
    assert card.fsrs.is_pending is True 
    assert card.current_queue.transform_to_not_pending is True

def test_get_due_cards_before_learning():
    fsrs_repository = FsrsRepository(FsrsQueueMapper())
    
    available_queues = [
        FsrsQueue(QueueType.DUE, False, 0, 10),
        FsrsQueue(QueueType.LEARNING, False, 0, 10),
        FsrsQueue(QueueType.NEW, False, 0, 10),
    ]
    now = datetime.now(timezone.utc)

    session = Session()
    flashcard = FlashcardModel(
        user_id="test",
        content="Test card 2",
    )
    session.add(flashcard)
    session.commit()
    fsrs = FsrsModel(
        flashcard_id=flashcard.id,
        user_id="test",
        difficulty=0.0,
        stability=0.0,
        state=State.LEARNING.value,
        due=now.timestamp(),
        reviews_count=0,
        last_rating=None,
        is_pending=False,
    )
    session.add(fsrs)
    session.commit()

    session = Session()
    flashcard = FlashcardModel(
        user_id="test",
        content="Test card 1",
    )
    session.add(flashcard)
    session.commit()
    fsrs = FsrsModel(
        flashcard_id=flashcard.id,
        user_id="test",
        difficulty=0.0,
        stability=0.0,
        state=State.REVIEW.value,
        due=now.timestamp(),
        reviews_count=0,
        last_rating=None,
        is_pending=False,
    )
    session.add(fsrs)
    session.commit()


    card = fsrs_repository.get_next_card("test", available_queues)

    assert card is not None
    assert card.current_queue.type == QueueType.DUE
    assert card.fsrs.state == State.REVIEW

def test_save_fsrs():
    session = Session()
    fsrs_repository = FsrsRepository(FsrsQueueMapper())
    fsrs = FsrsParams(
        flashcard_id=1,
        user_id="test",
        difficulty=10.0,
        stability=11.0,
        state=State.REVIEW,
        due=datetime.now(timezone.utc),
        reviews_count=0,
        last_rating=None,
        is_pending=True,
    )
    fsrs_repository.save(fsrs)
    assert session.query(FsrsModel).filter(
        FsrsModel.difficulty == fsrs.difficulty,
        FsrsModel.stability == fsrs.stability,
        FsrsModel.state == fsrs.state.value,
        FsrsModel.due == fsrs.due.timestamp(),
        FsrsModel.reviews_count == fsrs.reviews_count,
        FsrsModel.last_rating == fsrs.last_rating,
        FsrsModel.is_pending == fsrs.is_pending,
    ).first() is not None

def test_save_fsrs_when_card_exists():
    session = Session()
    fsrs_repository = FsrsRepository(FsrsQueueMapper())
    fsrs = FsrsModel(
        flashcard_id=1,
        user_id="test",
        difficulty=10.0,
        stability=11.0,
        state=State.REVIEW.value,
        due=int(datetime.now(timezone.utc).timestamp()),
        reviews_count=0,
        last_rating=None,
        is_pending=True,
    )
    session.add(fsrs)
    session.commit()
    params = FsrsParams(
        flashcard_id=1,
        user_id="test",
        difficulty=10.0,
        stability=11.0,
        state=State.REVIEW,
        due=datetime.now(timezone.utc),
        reviews_count=0,
        last_rating=None,
        is_pending=True,
    )

    fsrs_repository.save(params)
    assert session.query(FsrsModel).filter(
        FsrsModel.difficulty == params.difficulty,
        FsrsModel.stability == params.stability,
        FsrsModel.state == params.state.value,
        FsrsModel.due == params.due.timestamp(),
        FsrsModel.reviews_count == params.reviews_count,
        FsrsModel.last_rating == params.last_rating,
        FsrsModel.is_pending == params.is_pending,
    ).first() is not None