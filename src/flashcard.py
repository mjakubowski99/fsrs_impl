
class Flashcard:
    id: int
    content: str

    def __init__(self, content: str, id: int = None):
        self.content = content
        self.id = id