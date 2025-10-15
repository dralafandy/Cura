from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# إعداد قاعدة البيانات (SQLite للبساطة)
engine = create_engine('sqlite:///dental_clinic.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)