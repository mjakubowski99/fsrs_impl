from src.fsrs_model import UserFsrsModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.fsrs_queue import FsrsQueue
from src.queue_type import QueueType
from src.user_fsrs import UserFsrs
from datetime import datetime

engine = create_engine('sqlite:///db.db')

Session = sessionmaker(bind=engine)

class UserFsrsRepository:

    def save(self, user_fsrs: UserFsrs):
        session = Session()
        payload = {
            'queues': [
                {
                    'type': queue.type.value,
                    'is_pending': queue.is_pending,
                    'daily_count': queue.daily_count,
                    'daily_limit': queue.daily_limit,
                }
                for queue in user_fsrs.queues
            ],
        }
        if user_fsrs.id is None:
            model = UserFsrsModel(
                user_id=user_fsrs.user_id,
                payload=payload,
                updated_at=datetime.now(),
            )
            session.add(model)
            session.commit()
            user_fsrs.id = model.id
        else:
            session.query(UserFsrsModel).filter(UserFsrsModel.user_id == user_fsrs.user_id).update({
                'payload': payload,
                'updated_at': datetime.now(),
            })

        session.commit()

    def get_by_user_id(self, user_id: str) -> UserFsrs|None:
        session = Session()
        result = session.query(UserFsrsModel).filter(UserFsrsModel.user_id == user_id).first()
        if result is None:
            return None

        queues = []
        for queue in result.payload['queues']:
            queues.append(FsrsQueue(
                type=QueueType(queue['type']),
                is_pending=queue['is_pending'],
                daily_count=queue['daily_count'],
                daily_limit=queue['daily_limit'],
            ))

        return UserFsrs(
            id=result.id,
            user_id=result.user_id,
            queues=queues,
            updated_at=result.updated_at,
        )