from src.user_fsrs import UserFsrs
from src.user_fsrs_repository import UserFsrsRepository
from datetime import datetime, timedelta

class FsrsResolver:

    def __init__(self, user_fsrs_repository: UserFsrsRepository):
        self.user_fsrs_repository = user_fsrs_repository

    def resolve(self, user_id: str) -> UserFsrs:
        data = self.user_fsrs_repository.get_by_user_id(user_id)
        if data is None:
            return UserFsrs.new_fsrs(user_id)
        
        if data.updated_at < datetime.now() - timedelta(days=1):
            return UserFsrs.new_fsrs(user_id)
        
        return data