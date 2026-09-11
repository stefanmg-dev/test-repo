from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import uuid

# ============================
# SQLITE DATABASE
# ============================
DATABASE_URL = "sqlite:///database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # важно за FastAPI
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# ============================
# DOCUMENT TABLE
# ============================
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(Text)
    document_type = Column(Text)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ============================
# EXTRACTED FIELDS TABLE
# ============================
class DocumentExtracted(Base):
    __tablename__ = "document_extracted"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"))
    field_name = Column(Text)
    field_value = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ============================
# CREATE TABLES
# ============================
Base.metadata.create_all(engine)
