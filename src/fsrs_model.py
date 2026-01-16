from sqlalchemy import JSON, Column, DateTime, Integer, Boolean, ForeignKey, Numeric, String, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class FlashcardModel(Base):
    __tablename__ = 'flashcards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    content = Column(String, nullable=False)
    
    # Relacja z FsrsModel
    fsrs = relationship("FsrsModel", back_populates="flashcard", uselist=False)

    def __repr__(self):
        return f"<FlashcardModel(id={self.id}, content={self.content[:50]}...)>"


class FsrsModel(Base):
    __tablename__ = 'fsrs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    flashcard_id = Column(Integer, ForeignKey('flashcards.id'), nullable=False, unique=True)
    flashcard = relationship("FlashcardModel", back_populates="fsrs")
    is_pending = Column(Boolean, nullable=False)
    difficulty = Column(Numeric(precision=6, scale=4), nullable=False)
    stability = Column(Numeric(precision=15, scale=6), nullable=True)
    state = Column(String(1), nullable=False)
    due = Column(Integer, nullable=True, index=True)
    reviews_count = Column(Integer, nullable=False, default=0)
    step = Column(SmallInteger, nullable=True)
    last_rating = Column(SmallInteger, nullable=True)
    last_review = Column(Integer, nullable=True)
    blocked_until = Column(Integer, nullable=True)
    freshness_score = Column(Integer)
    updated_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"""<FsrsModel(
            id={self.id}, 
            flashcard_id={self.flashcard_id}, 
            difficulty={self.difficulty}, 
            stability={self.stability}, 
            state={self.state}, 
            due={self.due}, 
            reviews_count={self.reviews_count},
            last_rating={self.last_rating},
            freshness_score={self.freshness_score})>
        )
        """
    

class UserFsrsModel(Base):
    __tablename__ = 'user_fsrs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, unique=True)
    payload = Column(JSON, nullable=False)
    updated_at = Column(DateTime, nullable=False)