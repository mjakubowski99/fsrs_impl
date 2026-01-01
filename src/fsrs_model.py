from sqlalchemy import Column, Integer, Boolean, ForeignKey, Numeric, String, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class FlashcardModel(Base):
    __tablename__ = 'flashcards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String, nullable=False)
    
    # Relacja z FsrsModel
    fsrs = relationship("FsrsModel", back_populates="flashcard", uselist=False)

    def __repr__(self):
        return f"<FlashcardModel(id={self.id}, content={self.content[:50]}...)>"


class FsrsModel(Base):
    __tablename__ = 'fsrs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    flashcard_id = Column(Integer, ForeignKey('flashcards.id'), nullable=False, unique=True)
    flashcard = relationship("FlashcardModel", back_populates="fsrs")
    is_pending = Column(Boolean, nullable=False)
    difficulty = Column(Numeric(precision=6, scale=4), nullable=False)
    stability = Column(Numeric(precision=15, scale=6), nullable=True)
    state = Column(String(1), nullable=False)
    due = Column(Integer, nullable=True)
    reviews_count = Column(Integer(unsigned=True), nullable=False, default=0)
    last_rating = Column(SmallInteger(unsigned=True), nullable=True)

    def __repr__(self):
        return f"<FsrsModel(id={self.id}, flashcard_id={self.flashcard_id}, difficulty={self.difficulty}, stability={self.stability}, state={self.state}, due={self.due}, reviews_count={self.reviews_count}, last_rating={self.last_rating})>"

