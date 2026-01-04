import sys
from pathlib import Path
import pytest
import os
from sqlalchemy import create_engine

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

engine = create_engine('sqlite:///db.db')

@pytest.fixture(scope="function", autouse=True)
def db_setup():
    from src.fsrs_model import Base
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield