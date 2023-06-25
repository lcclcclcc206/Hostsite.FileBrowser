from pathlib import Path
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

db_path = str(Path(sys.path[0]).joinpath('data.db')).replace('\\','/')
SQLALCHEMY_DATABASE_URL = f'sqlite:///{db_path}'
print(SQLALCHEMY_DATABASE_URL)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()