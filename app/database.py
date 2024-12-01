from sqlmodel import SQLModel, create_engine, Session


# SQLite Database connection
DATABASE_URL = "sqlite:///./books.db"
engine = create_engine(DATABASE_URL, echo=True)


# Dependency for database session
def get_session():
    with Session(engine) as session:
        yield session