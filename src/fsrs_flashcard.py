from src.fsrs_algorithm import FsrsParams
from src.flashcard import Flashcard
from src.fsrs_queue import FsrsQueue

class FsrsFlashcard:
    fsrs: FsrsParams
    flashcard: Flashcard
    current_queue: FsrsQueue

    def __init__(self, fsrs: FsrsParams, flashcard: Flashcard, current_queue: FsrsQueue):
        self.fsrs = fsrs
        self.flashcard = flashcard
        self.current_queue = current_queue