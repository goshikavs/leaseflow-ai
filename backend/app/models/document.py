from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base
from app.models.enums import ProcessingStatus

if TYPE_CHECKING:
    from app.models.extraction import Extraction
    from app.models.lease import Lease


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_content_hash", "content_hash"),
        Index("ix_documents_processing_status", "processing_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default=ProcessingStatus.UPLOADED.value)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    lease: Mapped["Lease | None"] = relationship(back_populates="document", uselist=False, cascade="all, delete-orphan")
    extractions: Mapped[list["Extraction"]] = relationship(back_populates="document", cascade="all, delete-orphan")
