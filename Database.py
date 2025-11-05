# app/database.py
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./health.db"  # change to postgres://... for cloud
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
