import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

dbhost = os.getenv('NOTES_DB_HOST')
dbport = os.getenv('NOTES_DB_PORT')
dbname = os.getenv('NOTES_DB_NAME')
dbuser = os.getenv('NOTES_DB_USERNAME')
dbpassword = os.getenv('NOTES_DB_PASSWORD')

SQLALCHEMY_DATABASE_URL = f"postgresql://{dbuser}:{dbpassword}@{dbhost}:{dbport}/{dbname}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)   
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()