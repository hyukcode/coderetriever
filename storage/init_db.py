from storage.database import (
    Base,
    engine,
)

import storage.models

def init_db():
    Base.metadata.create_all(
        bind=engine
    )

if __name__ == "__main__":
    init_db()