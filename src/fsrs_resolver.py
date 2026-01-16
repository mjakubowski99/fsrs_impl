from src.user_fsrs import UserFsrs
from src.user_fsrs_repository import UserFsrsRepository
from datetime import datetime, timedelta

class FsrsResolver:

    def __init__(self, user_fsrs_repository: UserFsrsRepository):
        self.user_fsrs_repository = user_fsrs_repository

    def resolve(self, user_id: str) -> UserFsrs:
        data = self.user_fsrs_repository.get_by_user_id(user_id)
        if data is None:
            user_fsrs = UserFsrs.new_fsrs(user_id)
            self.user_fsrs_repository.save(user_fsrs)
            return user_fsrs
        
        if data.updated_at.day != datetime.now().day:
            user_fsrs = UserFsrs.new_fsrs(user_id)
            user_fsrs.id = data.id
            user_fsrs.updated_at = datetime.now()
            self.user_fsrs_repository.save(user_fsrs)
            return user_fsrs
        
        return data