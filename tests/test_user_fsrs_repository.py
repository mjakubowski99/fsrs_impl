from src.fsrs_model import UserFsrsModel
from src.fsrs_queue import FsrsQueue
from src.queue_type import QueueType
from sqlalchemy.orm import sessionmaker
from conftest import engine
from datetime import datetime, timezone

from src.user_fsrs import UserFsrs
from src.user_fsrs_repository import UserFsrsRepository

Session = sessionmaker(bind=engine)

def test_get_user_fsrs():
    user_fsrs_repository = UserFsrsRepository()

    session = Session()
    user_fsrs_model = UserFsrsModel(
        user_id="test",
        payload={
            'queues': [
                {
                    'type': QueueType.NEW.value,
                    'is_pending': False,
                    'daily_count': 0,
                    'daily_limit': 10,
                },
                 {
                    'type': QueueType.LEARNING.value,
                    'is_pending': False,
                    'daily_count': 10,
                    'daily_limit': 10,
                }
            ]
        },
        updated_at=datetime.now(),
    )
    session.add(user_fsrs_model)
    session.commit()

    user_fsrs = user_fsrs_repository.get_by_user_id("test")

    assert user_fsrs is not None
    assert len(list(user_fsrs.get_available_queues())) == 1
    assert list(user_fsrs.get_available_queues())[0].type == QueueType.NEW

def test_save_user_fsrs():
    user_fsrs_repository = UserFsrsRepository()

    user_fsrs = UserFsrs(
        id=None,
        user_id="test",
        queues=[
            FsrsQueue(QueueType.NEW, False, 0, 10),
        ],
        updated_at=datetime.now(),
    )

    user_fsrs_repository.save(user_fsrs)

    assert user_fsrs.id is not None

def test_save_user_fsrs_with_id():
    user_fsrs_repository = UserFsrsRepository()
    now = datetime.now(timezone.utc)

    session = Session()
    user_fsrs = UserFsrsModel(
        user_id="test",
        payload={
            'queues': [
                {
                    'type': QueueType.NEW.value,
                    'is_pending': False,
                    'daily_count': 0,
                    'daily_limit': 10,
                }
            ]
        },
        updated_at=now,
    )
    session.add(user_fsrs)
    session.commit()
    user_fsrs =user_fsrs_repository.get_by_user_id("test")

    user_fsrs_repository.save(user_fsrs)

    assert session.query(UserFsrsModel).filter(UserFsrsModel.user_id == user_fsrs.user_id).first() is not None