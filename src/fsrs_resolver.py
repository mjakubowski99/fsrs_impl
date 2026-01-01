from src.user_fsrs import UserFsrs

class FsrsResolver:

    def resolve(self, user_id: str) -> UserFsrs:
        return UserFsrs.new_fsrs(user_id)