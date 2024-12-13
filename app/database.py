from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

connection_string = f"postgresql://postgres:rootroot@postgres:5432/primeinsights"

engine = create_engine(connection_string)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


